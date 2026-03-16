

import os
import json
import pickle
import numpy as np
from pathlib import Path
from typing import List, Tuple

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    from groq import Groq          
except ImportError as e:
    raise ImportError(f"Missing dependency: {e}. Run: pip install -r requirements.txt")



EMBED_MODEL   = "all-MiniLM-L6-v2"   
CHUNK_SIZE    = 300                    
CHUNK_OVERLAP = 50
TOP_K         = 10                     
INDEX_DIR     = Path("data/index")
KB_PATH   = Path("data/raw/combined_corpus.txt")

INDEX_DIR.mkdir(parents=True, exist_ok=True)



def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks by character count."""
    words = text.split()
    chunks = []
    step   = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk.strip())
    return chunks


def prepare_knowledge_base(kb_path: Path = KB_PATH) -> List[dict]:
    """Load corpus, split by source section, chunk each section."""
    text = kb_path.read_text(encoding="utf-8")

    import re
    sections = re.split(r"={60}\nSOURCE: (.+?) \((.+?)\)\n={60}", text)

    docs = []

    i = 1
    while i + 2 < len(sections):
        source_name = sections[i].strip()
        source_url  = sections[i+1].strip()
        content     = sections[i+2].strip()
        chunks = chunk_text(content)
        for idx, chunk in enumerate(chunks):
            docs.append({
                "id":     f"{source_name}_{idx}",
                "source": source_name,
                "url":    source_url,
                "text":   chunk,
            })
        i += 3

    print(f"  Total chunks created: {len(docs)}")
    return docs


# Embedding & Indexing 
def build_index(docs: List[dict], embed_model: str = EMBED_MODEL):
    """Embed all chunks and build FAISS index. Saves to disk."""
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    print(f"  Loading embedding model: {embed_model} ...")
    model = SentenceTransformer(embed_model)

    texts = [d["text"] for d in docs]
    print(f"  Embedding {len(texts)} chunks ...")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)
    embeddings = np.array(embeddings, dtype="float32")

    # L2 normalise for cosine similarity
    faiss.normalize_L2(embeddings)

    dim   = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)   # Inner product = cosine after L2 norm
    index.add(embeddings)

    # Save index + metadata
    faiss.write_index(index, str(INDEX_DIR / "faiss.index"))
    with open(INDEX_DIR / "docs.pkl", "wb") as f:
        pickle.dump(docs, f)
    with open(INDEX_DIR / "embed_model.txt", "w") as f:
        f.write(embed_model)

    print(f"  Index saved to {INDEX_DIR}/")
    return index, docs, model


def load_index() -> Tuple:
    """Load existing FAISS index from disk."""
    index = faiss.read_index(str(INDEX_DIR / "faiss.index"))
    with open(INDEX_DIR / "docs.pkl", "rb") as f:
        docs = pickle.load(f)
    embed_model = (INDEX_DIR / "embed_model.txt").read_text().strip()
    model = SentenceTransformer(embed_model)
    print(f"   Loaded index ({index.ntotal} vectors) from {INDEX_DIR}/")
    return index, docs, model


def index_exists() -> bool:
    return (INDEX_DIR / "faiss.index").exists() and (INDEX_DIR / "docs.pkl").exists()


#  Retrieval 
def retrieve(query: str, index, docs: List[dict], model, top_k: int = TOP_K) -> List[dict]:
    """Embed query, retrieve top-k chunks."""
    q_emb = model.encode([query], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(q_emb)
    scores, indices = index.search(q_emb, top_k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        results.append({**docs[idx], "score": float(score)})
    return results


# LLM Generation (Groq — free tier)
SYSTEM_PROMPT = """You are EduAI, an expert admissions and academic advisor for a specific educational program. Your job is to help prospective students make informed decisions by answering their questions accurately and helpfully.

You will be given CONTEXT extracted from official program materials. Use ONLY this context to answer.

## Response Rules

**Accuracy (never guess):**
- Answer ONLY from the provided context. Do not use outside knowledge.
- If a specific fact (fee, date, location, eligibility) is not in the context, say exactly: "This detail isn't in the materials I have — please verify at the official website."
- Never round, estimate, or approximate numbers unless the context itself does so.

**Relevance (stay focused):**
- Directly answer what was asked. Do not pad with unrelated program info.
- If the question has multiple parts, answer each part clearly.
- If the context only partially answers the question, answer what you can and flag what's missing.

**Robustness (handle edge cases):**
- If the question is vague (e.g. "tell me about fees"), ask one clarifying question OR cover all fee-related info from context.
- If the student seems confused or asks something off-topic, gently redirect: "I can best help with questions about this program's curriculum, admissions, fees, and career outcomes."
- Never refuse to engage — always provide something useful.

**User Experience (be human):**
- Be warm, clear, and concise. Write like a knowledgeable advisor, not a search engine.
- Use bullet points or numbered lists when listing multiple items (e.g. eligibility criteria, course modules).
- Bold key terms like **fee**, **eligibility**, **duration** for scannability.
- Keep answers under 200 words unless the question genuinely requires more detail.
- End with a helpful follow-up nudge when relevant, e.g. "Would you like details on the application process?"

## Output Format
- For factual questions (fees, dates, eligibility): answer directly, then cite the source section in parentheses e.g. *(Admissions & Fees)*
- For open-ended questions (career outcomes, program value): give a structured 2-3 point answer
- For comparisons or "should I" questions: present the relevant facts neutrally and let the student decide

Remember: You represent this program. Be helpful, honest, and never mislead a prospective student.
"""

def generate_answer(query: str, context_chunks: List[dict], groq_api_key: str) -> str:
    """Call Groq LLM with retrieved context."""
    client = Groq(api_key=groq_api_key)

    # Build context string
    context = "\n\n---\n\n".join(
        f"[Source: {c['source']}]\n{c['text']}" for c in context_chunks
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"CONTEXT:\n{context}\n\nQUESTION: {query}"},
    ]

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.2,
        max_tokens=600,
    )
    return response.choices[0].message.content.strip()


# Full RAG Query 
class CourseAssistant:
    def __init__(self, groq_api_key: str):
        self.groq_api_key = groq_api_key
        self._load_or_build()

    def _load_or_build(self):
        if index_exists():
            print("Loading existing index...")
            self.index, self.docs, self.embed_model = load_index()
        else:
            print("Building index from corpus...")
            if not KB_PATH.exists():
                raise FileNotFoundError(
                    f"Corpus not found at {KB_PATH}. Run scraper.py first."
                )
            docs = prepare_knowledge_base()
            self.index, self.docs, self.embed_model = build_index(docs)

    def ask(self, question: str) -> dict:
        """Ask a question, returns answer + source chunks."""
        chunks = retrieve(question, self.index, self.docs, self.embed_model)
        answer = generate_answer(question, chunks, self.groq_api_key)
        return {
            "question": question,
            "answer":   answer,
            "sources":  [{"source": c["source"], "score": round(c["score"], 3)} for c in chunks],
        }

if __name__ == "__main__":
    import sys
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        print("Set GROQ_API_KEY environment variable first.")
        sys.exit(1)

    assistant = CourseAssistant(groq_api_key=key)
    print("\nCourse Assistant ready! Type 'quit' to exit.\n")
    while True:
        q = input("You: ").strip()
        if q.lower() in ("quit", "exit", "q"):
            break
        if not q:
            continue
        result = assistant.ask(q)
        print(f"\nAssistant: {result['answer']}")
        print(f"  (Sources: {', '.join(s['source'] for s in result['sources'][:3])})\n")