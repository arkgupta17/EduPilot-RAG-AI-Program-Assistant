import os
import shutil
import subprocess
import winreg
from pathlib import Path
import streamlit as st
from rag_pipeline import CourseAssistant

TEAM_NAME = "BASIC"
VERSION = "1.0.0"

def get_api_key():
    key = os.environ.get("GROQ_API_KEY", "")
    if key:
        return key
    try:
        reg = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
        key, _ = winreg.QueryValueEx(reg, "GROQ_API_KEY")
        return key
    except Exception:
        return ""

groq_key = get_api_key()

st.set_page_config(page_title="EduPilot", page_icon="◈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=Inter:wght@300;400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
    background: #060810 !important;
    color: #C9D1DC !important;
}

#MainMenu, footer, header, .stDeployButton { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

[data-testid="stSidebar"] {
    background: #0A0D14 !important;
    border-right: 1px solid #151B27 !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 2rem 1.5rem !important; }

.brand { font-family: 'Syne', sans-serif; 
font-size: 1.6rem; font-weight: 800; 
letter-spacing: -0.03em; color: #fff; 
margin-bottom: 3px; }
.brand span { color: #2EE89A; }
.brand-sub { font-size: 0.62rem; 
letter-spacing: 0.18em; 
text-transform: uppercase; 
color: #2A3649; margin-bottom: 2.2rem; 
font-weight: 500; }
.sec { font-size: 0.62rem; 
letter-spacing: 0.18em; 
text-transform: uppercase; 
color: #2A3649; 
font-weight: 600; 
margin: 1.6rem 0 0.7rem; }

[data-testid="stSidebar"] .stTextInput > div { border: none !important; box-shadow: none !important; }
[data-testid="stSidebar"] .stTextInput > div > div { border: none !important; box-shadow: none !important; background: transparent !important; }
[data-testid="stSidebar"] .stTextInput input {
    background: #10151F !important;
    border: 1px solid #1C2535 !important;
    border-radius: 8px !important;
    color: #C9D1DC !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
    padding: 0.6rem 0.9rem !important;
    height: 40px !important;
    outline: none !important;
    box-shadow: none !important;
    transition: border-color 0.15s !important;
}
[data-testid="stSidebar"] .stTextInput input:focus {
    border-color: #2EE89A !important;
    box-shadow: none !important;
    outline: none !important;
}
[data-testid="stSidebar"] .stTextInput input:focus-visible { outline: none !important; }
[data-baseweb="base-input"] { background: transparent !important; border: none !important; box-shadow: none !important; outline: none !important; }
[data-baseweb="input"] { border: none !important; box-shadow: none !important; }
[data-testid="stSidebar"] label { font-size: 0.75rem !important; color: #3D5068 !important; font-family: 'Inter', sans-serif !important; }

.stack-row { display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 0.7rem; background: #10151F; border-radius: 8px; margin-bottom: 5px; border: 1px solid #151B27; }
.stack-left { display: flex; align-items: center; gap: 8px; }
.sdot { width: 6px; height: 6px; border-radius: 50%; background: #2EE89A; box-shadow: 0 0 6px rgba(46,232,154,0.5); flex-shrink: 0; }
.slabel { font-size: 0.78rem; color: #5A6E84; font-weight: 500; }
.sval { font-size: 0.75rem; color: #3D5068; }

[data-testid="stSidebar"] .stButton > button {
    background: #10151F !important;
    border: 1px solid #1C2535 !important;
    color: #5A6E84 !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 0.35rem 0.9rem !important;
    height: 38px !important;
    width: 100% !important;
    transition: all 0.15s !important;
    letter-spacing: 0.01em !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    border-color: #2EE89A !important;
    color: #2EE89A !important;
    background: #0D1A14 !important;
}

.topbar {
    padding: 0.9rem 2.5rem;
    border-bottom: 1px solid #151B27;
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #060810;
    position: sticky;
    top: 0;
    z-index: 100;
}
.topbar-title { font-family: 'Syne', sans-serif; font-size: 0.95rem; font-weight: 700; color: #E2E8F0; display: flex; align-items: center; gap: 8px; }
.tgem { color: #2EE89A; }
.status-pill { display: flex; align-items: center; gap: 6px; background: #10151F; border: 1px solid #151B27; border-radius: 20px; padding: 4px 12px; font-size: 0.7rem; color: #2A3649; font-weight: 500; letter-spacing: 0.05em; }
.ldot { width: 6px; height: 6px; border-radius: 50%; background: #2EE89A; box-shadow: 0 0 5px #2EE89A; animation: blink 2.5s infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.25} }

.hero { text-align: center; padding: 3.5rem 1rem 2.5rem; }
.hero-title { font-family: 'Syne', sans-serif; font-size: 3.2rem; font-weight: 800; letter-spacing: -0.04em; color: #E2E8F0; line-height: 1.1; margin-bottom: 0.75rem; }
.hero-title .ac { color: #2EE89A; }
.hero-sub { font-size: 1rem; color: #2A3649; font-weight: 400; margin: 0 auto 2.5rem; max-width: 380px; line-height: 1.6; }
.chips-label { font-size: 0.62rem; letter-spacing: 0.18em; text-transform: uppercase; color: #2A3649; font-weight: 600; margin-bottom: 0.9rem; text-align: center; }

.stButton > button {
    background: #0D1018 !important;
    border: 1px solid #1C2535 !important;
    color: #8A9BB0 !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 400 !important;
    padding: 1.2rem 1.4rem !important;
    text-align: left !important;
    height: auto !important;
    min-height: 72px !important;
    line-height: 1.5 !important;
    transition: all 0.15s ease !important;
    white-space: normal !important;
    word-wrap: break-word !important;
}
.stButton > button p {
    font-size: 1rem !important;
    color: #8A9BB0 !important;
    margin: 0 !important;
}
.stButton > button:hover {
    background: #0D1A14 !important;
    border-color: #2EE89A !important;
    color: #C9D1DC !important;
}
.stButton > button:hover p {
    color: #C9D1DC !important;
}

[data-testid="stChatMessage"] { background: transparent !important; border: none !important; padding: 0 !important; }

.umsg { display: flex; justify-content: flex-end; margin: 1rem 0; animation: fadeup 0.2s ease; }
.ububble { max-width: 68%; background: #0C1F16; border: 1px solid #1A3928; border-radius: 16px; border-bottom-right-radius: 4px; padding: 0.85rem 1.2rem; font-size: 1.2rem; color: #D4E8DC; line-height: 1.65; font-weight: 450; }

.bmsg { display: flex; gap: 12px; margin: 1rem 0; animation: fadeup 0.2s ease; }
.bavatar { width: 32px; height: 32px; border-radius: 8px; background: #0C1F16; border: 1px solid #1A3928; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; color: #2EE89A; font-weight: 800; font-family: 'Syne', sans-serif; flex-shrink: 0; margin-top: 2px; }
.bcontent { flex: 1; min-width: 0; }
.bbubble { background: #0A0D14; border: 1px solid #151B27; border-radius: 16px; border-top-left-radius: 4px; padding: 0.9rem 1.2rem; font-size: 1.2rem; color: #B8C4D0; line-height: 1.75; font-weight: 400; }
.bbubble strong { color: #D4DDE8; font-weight: 600; }
.bbubble ul, .bbubble ol { margin: 0.4rem 0 0.4rem 1.1rem; }
.bbubble li { margin-bottom: 0.25rem; }

.srcrow { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 7px; }
.srcpill { font-size: 0.8rem; padding: 2px 9px; border-radius: 20px; background: #0A0D14; border: 1px solid #151B27; color: #2A3649; letter-spacing: 0.05em; }
.srcpill .sc { color: #2EE89A; margin-left: 3px; font-weight: 800; }

@keyframes fadeup { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }

[data-testid="stChatInput"] {
    background: #0A0D14 !important;
    border: 1px solid #1C2535 !important;
    border-radius: 12px !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #2EE89A !important;
    box-shadow: none !important;
    outline: none !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: #C9D1DC !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    outline: none !important;
    box-shadow: none !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: #5A7A8A !important; font-size: 1rem !important; }
[data-testid="stChatInput"] > div { border: none !important; box-shadow: none !important; outline: none !important; }

::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #151B27; border-radius: 4px; }

.stAlert { background: #0A0D14 !important; border: 1px solid #151B27 !important; border-radius: 10px !important; font-family: 'Inter', sans-serif !important; font-size: 0.88rem !important; }
.stSpinner > div { border-top-color: #2EE89A !important; }

div[data-testid="stVerticalBlock"] > div { gap: 0 !important; }

.topbar-title { font-size: 1.3rem !important; font-weight: 700 !important; color: #E2E8F0 !important; }
.sec { font-size: 1rem !important; color: #6A8099 !important; font-weight: 600 !important; letter-spacing: 0.12em !important; }
.brand { font-size: 2rem !important; color: #FFFFFF !important; }
.brand-sub { font-size: 1rem !important; color: #4A6070 !important; }
.slabel { font-size: 1rem !important; color: #7A90A8 !important; font-weight: 500 !important; }
.sval { font-size: 1rem !important; color: #506070 !important; }
.status-pill { font-size: 1rem !important; color: #4A6070 !important; }
.hero-sub { font-size: 1.15rem !important; color: #5A7A8A !important; font-weight: 450 !important; }
.chips-label { font-size: 0.95rem !important; color: #5A7A8A !important; font-weight: 650 !important; letter-spacing: 0.18em !important; }

[data-testid="collapsedControl"] {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    color: #2EE89A !important;
}

# tried flex but kept breaking, this works
# TODO: fix spacing on mobile later  
# not sure why this needs !important but it does

</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="brand">edu<span>PILOT</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">AI Course Assistant</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="brand-sub">v{VERSION} · {TEAM_NAME}</div>', unsafe_allow_html=True)

    st.markdown('<div class="sec">Data Source</div>', unsafe_allow_html=True)
    new_url = st.text_input("url", placeholder="https://college.edu/program", label_visibility="collapsed")
    if st.button("⟳  Scrape & Rebuild"):
        if new_url.strip():
            with st.spinner("Scraping..."):
                if Path("data").exists():
                    shutil.rmtree("data")
                result = subprocess.run(["python", "scraper.py", new_url.strip()], capture_output=True, text=True)
            if result.returncode == 0:
                st.success("Done!")
                st.cache_resource.clear()
                st.session_state.messages = []
                st.rerun()
            else:
                st.error(result.stderr[-300:])
        else:
            st.warning("Enter a URL first.")

    st.markdown('<div class="sec">Stack</div>', unsafe_allow_html=True)
    for l, v in [("Scraper","Playwright"),("Embed","MiniLM-L6"),("Store","FAISS"),("LLM","Llama3 · Groq")]:
        st.markdown(f'<div class="stack-row"><div class="stack-left"><div class="sdot"></div><span class="slabel">{l}</span></div><span class="sval">{v}</span></div>', unsafe_allow_html=True)

    st.markdown('<div class="sec">Actions</div>', unsafe_allow_html=True)
    if st.button("✕  Clear Chat"):
        st.session_state.messages = []
        st.rerun()

st.markdown("""
<div class="topbar">
    <div class="topbar-title"><span class="tgem">◈</span> AI-Powered Course Assistant</div>
    <div class="status-pill"><div class="ldot"></div>RAG · FAISS · Groq</div>
</div>
""", unsafe_allow_html=True)

if not groq_key:
    st.markdown("<br>", unsafe_allow_html=True)
    st.error("GROQ_API_KEY not found. Set it with: [System.Environment]::SetEnvironmentVariable('GROQ_API_KEY','your_key','User') then restart terminal.")
    st.stop()

@st.cache_resource(show_spinner="Loading knowledge base...")
def load_assistant(k):
    return CourseAssistant(groq_api_key=k)

try:
    assistant = load_assistant(groq_key)
except FileNotFoundError:
    st.markdown("<br>", unsafe_allow_html=True)
    st.error("No data found. Paste a program URL in the sidebar and click Scrape & Rebuild.")
    st.stop()
except Exception as e:
    st.error(f"Error: {e}")
    st.stop()

SUGGESTIONS = [
    "What is the duration & structure?",
    "What are the admission requirements?",
    "What is the total fee?",
    "What career roles can I expect?",
    "What topics are in the curriculum?",
    "Is work experience required?",
]

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.markdown("""
    <div class="hero">
        <div class="hero-title">Ask anything about<br><span class="ac">the program</span></div>
        <div class="hero-sub">Curriculum · Admissions · Fees · Career Outcomes</div>
    </div>
    <div class="chips-label">Suggested questions</div>
    """, unsafe_allow_html=True)
    cols = st.columns(2, gap="small")
    for i, s in enumerate(SUGGESTIONS):
        with cols[i % 2]:
            if st.button(s, key=f"s{i}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": s})
                with st.spinner(""):
                    result = assistant.ask(s)
                st.session_state.messages.append({"role": "assistant", "content": result["answer"], "sources": result["sources"]})
                st.rerun()

for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(f'<div class="umsg"><div class="ububble">{msg["content"]}</div></div>', unsafe_allow_html=True)
    else:
        with st.chat_message("assistant"):
            pills = "".join(f'<span class="srcpill">{s["source"].replace("-"," ").lower()}<span class="sc">{s["score"]:.2f}</span></span>' for s in msg.get("sources", [])[:4])
            st.markdown(f'''<div class="bmsg"><div class="bavatar">◈</div><div class="bcontent"><div class="bbubble">{msg["content"]}</div><div class="srcrow">{pills}</div></div></div>''', unsafe_allow_html=True)

if prompt := st.chat_input("Ask about fees, curriculum, admissions..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(f'<div class="umsg"><div class="ububble">{prompt}</div></div>', unsafe_allow_html=True)
    with st.chat_message("assistant"):
        with st.spinner(""):
            result = assistant.ask(prompt)
        pills = "".join(f'<span class="srcpill">{s["source"].replace("-"," ").lower()}<span class="sc">{s["score"]:.2f}</span></span>' for s in result["sources"][:4])
        st.markdown(f'''<div class="bmsg"><div class="bavatar">◈</div><div class="bcontent"><div class="bbubble">{result["answer"]}</div><div class="srcrow">{pills}</div></div></div>''', unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": result["answer"], "sources": result["sources"]})