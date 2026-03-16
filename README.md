# EduPilot 
AI-powered course assistant that answers any question about any educational program — instantly.

EduPilot uses a RAG (Retrieval-Augmented Generation) pipeline to scrape official program pages, index the content, and answer student queries with grounded, accurate responses. No hallucinations. No guesswork.

Built for FrostHack @ IIT Mandi — Xpecto'26.



## What it does

Prospective students waste hours digging through cluttered college websites trying to find fees, eligibility, curriculum details, and career outcomes. EduPilot fixes that — paste any program URL and ask anything in plain English.

---

## Demo

![EduPilot UI]

---

## How it works
```
Program URL
    ↓
Playwright crawls all sub-pages (curriculum, fees, admissions, careers)
    ↓
Text is chunked into 350-token windows with 40-token overlap
    ↓
all-MiniLM-L6-v2 embeds each chunk locally
    ↓
FAISS indexes all vectors for fast similarity search
    ↓
User query → embed → top-8 chunks retrieved
    ↓
Llama3 via Groq generates a grounded answer
    ↓
EduPilot displays answer + source attribution
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Web Crawling | Playwright |
| Embeddings | all-MiniLM-L6-v2 (Hugging Face) |
| Vector Store | FAISS (Meta AI) |
| LLM | Llama3 via Groq API |
| UI | Streamlit |
| Language | Python 3.13 |

---

## Setup

# 1. Clone the repo
```bash
git clone https://github.com/yourusername/edupilot.git
cd edupilot
```

# 2. Install dependencies
```bash
pip install -r requirements.txt
python -m playwright install chromium
```

# 3. Set your Groq API key
Get a free key at [console.groq.com](https://console.groq.com)

**Windows:**
```powershell
[System.Environment]::SetEnvironmentVariable("GROQ_API_KEY","your_key","User")
```

**Mac/Linux:**
```bash
export GROQ_API_KEY=your_key
```

# 4. Scrape a program
```bash
python crawler.py https://mastersunion.org/pgp-in-applied-ai-and-agentic-systems
```

# 5. Run the app
```bash
streamlit run app.py
```

---

## Project Structure
```
edupilot/
├── crawler.py          # Playwright-based web crawler
├── rag_pipeline.py     # Chunking, embedding, FAISS indexing, LLM generation
├── app.py              # Streamlit chat UI
├── requirements.txt
├── README.md
└── corpus/
    ├── scraped/        # Raw text files per page
    └── index/          # FAISS vector index
```

---

## Features

- **Works on any college website** — no hardcoded URLs
- **Auto sub-page discovery** — finds curriculum, fees, admissions pages automatically
- **Zero hallucinations** — LLM only answers from retrieved context
- **Source attribution** — every answer shows which page it came from
- **Confidence scoring** — similarity scores shown per source
- **One-click rescrape** — switch programs without touching code

---

## Limitations

- JS-heavy sites may not render fully despite Playwright wait strategies
- Free Groq API has a 100k token/day limit
- Content hidden behind authentication cannot be scraped

---

## Future Scope

- PDF brochure upload support
- Multi-program side-by-side comparison
- WhatsApp / Telegram bot integration
- Multilingual support (Hindi, regional languages)
- Analytics dashboard for admissions teams

---

## Team

Built by **Abhinav Singh, Ark Gupta, Kshitiz Kumar** — IIIT Nagpur

---

## Credits

| Tool | Credit |
|---|---|
| Playwright | Microsoft |
| sentence-transformers | Hugging Face |
| FAISS | Meta AI |
| Groq API | Groq Inc. |
| Llama3 | Meta AI |
| Streamlit | Snowflake |

---

## License

MIT
