import streamlit as st
import json
import base64
from app.mcp.client import run_agent, run_upload

st.set_page_config(
    page_title="ToolPilot",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }

/* ── Background: bright gradient ── */
.stApp {
    background: linear-gradient(135deg, #e8f4fd 0%, #f0e6ff 40%, #fce4ec 100%);
    min-height: 100vh;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #ffffff 0%, #f3e8ff 100%);
    border-right: 2px solid rgba(124,58,237,0.15);
    box-shadow: 4px 0 20px rgba(124,58,237,0.08);
}

/* ── Input ── */
.stTextInput > div > div > input {
    background: #ffffff !important;
    border: 2px solid rgba(124,58,237,0.3) !important;
    border-radius: 16px !important;
    color: #1e1b4b !important;
    padding: 14px 20px !important;
    font-size: 0.95rem !important;
    caret-color: #7c3aed !important;
    box-shadow: 0 2px 12px rgba(124,58,237,0.08) !important;
}
.stTextInput > div > div > input::placeholder { color: #a78bfa !important; }
.stTextInput > div > div > input:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 4px rgba(124,58,237,0.15) !important;
    outline: none !important;
}

/* ── Upload section ── */
.upload-section {
    background: linear-gradient(135deg, #7c3aed, #db2777);
    border-radius: 16px;
    padding: 16px;
    margin: 6px 0 10px 0;
    box-shadow: 0 4px 20px rgba(124,58,237,0.3);
}
.upload-title {
    font-size: 0.92rem;
    font-weight: 800;
    color: #ffffff !important;
    letter-spacing: 0.04em;
    margin-bottom: 2px;
}
.upload-sub {
    font-size: 0.73rem;
    color: rgba(255,255,255,0.8) !important;
    margin-bottom: 10px;
}
.upload-status-ok {
    background: rgba(255,255,255,0.95);
    border: 1.5px solid #7c3aed;
    border-radius: 10px;
    padding: 8px 12px;
    font-size: 0.8rem;
    color: #4c1d95 !important;
    margin-top: 8px;
    font-weight: 600;
}
.upload-status-info {
    background: rgba(255,255,255,0.95);
    border: 1.5px solid #db2777;
    border-radius: 10px;
    padding: 8px 12px;
    font-size: 0.8rem;
    color: #831843 !important;
    margin-top: 8px;
    font-weight: 600;
}
.active-doc {
    font-size: 0.75rem;
    color: #4c1d95 !important;
    margin-top: 6px;
    font-weight: 700;
    background: rgba(124,58,237,0.08);
    border-radius: 8px;
    padding: 5px 10px;
    border: 1px solid rgba(124,58,237,0.2);
}

/* ── File uploader override ── */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.9) !important;
    border: 2px dashed rgba(124,58,237,0.5) !important;
    border-radius: 12px !important;
}
[data-testid="stFileUploader"] * { color: #4c1d95 !important; }
[data-testid="stFileUploaderDropzoneInstructions"] * { color: #7c3aed !important; }

/* ── User bubble ── */
.user-bubble {
    background: linear-gradient(135deg, #7c3aed 0%, #db2777 100%);
    color: #fff;
    padding: 14px 20px;
    border-radius: 22px 22px 4px 22px;
    margin: 10px 0 10px 80px;
    font-size: 0.95rem;
    line-height: 1.7;
    box-shadow: 0 6px 24px rgba(124,58,237,0.35);
    animation: fadeSlideLeft 0.3s ease;
}

/* ── Agent bubble ── */
.agent-bubble {
    background: #ffffff;
    border: 1.5px solid rgba(124,58,237,0.15);
    color: #1e1b4b;
    padding: 16px 20px;
    border-radius: 22px 22px 22px 4px;
    margin: 10px 80px 10px 0;
    font-size: 0.95rem;
    line-height: 1.7;
    box-shadow: 0 4px 20px rgba(124,58,237,0.1);
    animation: fadeSlideRight 0.3s ease;
}

/* ── Plan box ── */
.plan-box {
    background: linear-gradient(135deg, rgba(124,58,237,0.06), rgba(219,39,119,0.04));
    border: 1px solid rgba(124,58,237,0.2);
    border-radius: 12px;
    padding: 10px 14px;
    margin-top: 10px;
    font-size: 0.8rem;
    color: #6d28d9;
}
.tool-badge {
    display: inline-block;
    background: linear-gradient(135deg, #7c3aed, #db2777);
    color: #ffffff;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    margin: 2px 3px;
    box-shadow: 0 2px 8px rgba(124,58,237,0.3);
}

/* ── Status row ── */
.status-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 5px 0;
    font-size: 0.82rem;
    color: #4c1d95;
    border-top: 1px solid rgba(124,58,237,0.1);
    margin-top: 6px;
}
.status-tool {
    background: linear-gradient(135deg, #ede9fe, #fce7f3);
    color: #7c3aed;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 700;
    border: 1px solid rgba(124,58,237,0.2);
}

/* ── Animated loader ── */
@keyframes pulse-dot {
    0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
    40% { transform: scale(1.1); opacity: 1; }
}
.loader-dots {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 14px 20px;
    background: #ffffff;
    border: 1.5px solid rgba(124,58,237,0.2);
    border-radius: 22px 22px 22px 4px;
    margin: 10px 80px 10px 0;
    width: fit-content;
    box-shadow: 0 4px 16px rgba(124,58,237,0.1);
}
.loader-dots span {
    width: 9px; height: 9px;
    border-radius: 50%;
    display: inline-block;
    animation: pulse-dot 1.2s infinite ease-in-out;
}
.loader-dots span:nth-child(1) { background: #7c3aed; }
.loader-dots span:nth-child(2) { background: #db2777; animation-delay: 0.2s; }
.loader-dots span:nth-child(3) { background: #f59e0b; animation-delay: 0.4s; }
.loader-label { font-size: 0.8rem; color: #7c3aed; margin-left: 6px; font-weight: 600; }

/* ── Animations ── */
@keyframes fadeSlideLeft {
    from { opacity: 0; transform: translateX(24px); }
    to   { opacity: 1; transform: translateX(0); }
}
@keyframes fadeSlideRight {
    from { opacity: 0; transform: translateX(-24px); }
    to   { opacity: 1; transform: translateX(0); }
}

/* ── Metric cards ── */
.metric-card {
    background: linear-gradient(135deg, #ffffff, #f5f3ff);
    border: 1.5px solid rgba(124,58,237,0.2);
    border-radius: 14px;
    padding: 14px;
    text-align: center;
    box-shadow: 0 2px 12px rgba(124,58,237,0.08);
}
.metric-value {
    font-size: 1.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #7c3aed, #db2777);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.metric-label {
    font-size: 0.72rem;
    color: #6d28d9;
    margin-top: 3px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 600;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #7c3aed 0%, #db2777 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 9px 18px !important;
    font-weight: 700 !important;
    font-size: 0.87rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 14px rgba(124,58,237,0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(124,58,237,0.4) !important;
}

/* ── Divider ── */
.custom-divider {
    border: none;
    border-top: 1.5px solid rgba(124,58,237,0.12);
    margin: 14px 0;
}

/* ── Logo ── */
.logo-text {
    font-size: 1.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #7c3aed, #db2777);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.logo-sub {
    font-size: 0.72rem;
    color: #7c3aed;
    margin-top: -2px;
    font-weight: 500;
}

/* ── Tool list items ── */
.tool-item {
    padding: 7px 0;
    border-bottom: 1px solid rgba(124,58,237,0.08);
}
.tool-name { font-size: 0.84rem; color: #1e1b4b; font-weight: 600; }
.tool-desc { font-size: 0.73rem; color: #7c3aed; }

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 80px 20px;
}
.empty-icon { font-size: 4rem; }
.empty-text {
    font-size: 1rem;
    margin-top: 16px;
    color: #6d28d9;
    font-weight: 500;
}
.empty-sub {
    font-size: 0.82rem;
    color: #a78bfa;
    margin-top: 6px;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in [
    ("messages", []),
    ("total_queries", 0),
    ("tools_used", []),
    ("is_thinking", False),
    ("upload_status", {}),
    ("last_uploaded", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="logo-text">🧭 ToolPilot</div>', unsafe_allow_html=True)
    st.markdown('<div class="logo-sub">Intelligent Workflow Automation</div>', unsafe_allow_html=True)
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    # Stats
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{st.session_state.total_queries}</div><div class="metric-label">Queries</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{len(set(st.session_state.tools_used))}</div><div class="metric-label">Tools</div></div>', unsafe_allow_html=True)

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    # ── Upload Document ───────────────────────────────────────────────────────
    st.markdown("""
    <div class="upload-section">
        <div class="upload-title">📎 Upload Document</div>
        <div class="upload-sub">PDF · DOCX · TXT &nbsp;|&nbsp; Ask questions after upload</div>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        label="upload",
        type=["pdf", "docx", "txt"],
        label_visibility="collapsed",
        key="doc_uploader"
    )

    if uploaded_file is not None:
        fname = uploaded_file.name
        if fname not in st.session_state.upload_status:
            st.session_state.upload_status[fname] = "processing"
            with st.spinner(f"Indexing {fname}..."):
                try:
                    content_b64 = base64.b64encode(uploaded_file.read()).decode("utf-8")
                    result = run_upload(fname, content_b64)
                    st.session_state.upload_status[fname] = result
                    st.session_state.last_uploaded = fname
                except Exception as e:
                    st.session_state.upload_status[fname] = f"❌ Upload failed: {str(e)}"

        status = st.session_state.upload_status.get(fname, "")
        if status and status != "processing":
            css_class = "upload-status-ok" if ("✅" in status or "successfully" in status.lower()) else "upload-status-info"
            st.markdown(f'<div class="{css_class}">{status}</div>', unsafe_allow_html=True)

    if st.session_state.last_uploaded:
        st.markdown(
            f'<div class="active-doc">📄 Active: {st.session_state.last_uploaded}</div>',
            unsafe_allow_html=True
        )

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    # ── Available Tools ───────────────────────────────────────────────────────
    st.markdown('<span style="font-size:0.82rem;font-weight:700;color:#4c1d95;text-transform:uppercase;letter-spacing:0.06em;">Available Tools</span>', unsafe_allow_html=True)
    tools_info = {
        "🔍 rag_tool":      "Search documents",
        "🌐 web_tool":      "Live web search",
        "📄 file_tool":     "Read local files",
        "✂️ summary_tool":  "Summarize text",
        "🗄️ db_tool":       "Query database",
        "🧠 memory_tool":   "Save to memory",
        "💭 recall_memory": "Retrieve memories",
    }
    for tool, desc in tools_info.items():
        st.markdown(f'<div class="tool-item"><span class="tool-name">{tool}</span><br><span class="tool-desc">{desc}</span></div>', unsafe_allow_html=True)

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    st.markdown('<span style="font-size:0.82rem;font-weight:700;color:#4c1d95;text-transform:uppercase;letter-spacing:0.06em;">Try These</span>', unsafe_allow_html=True)

    examples = [
        "What is machine learning?",
        "Latest AI news",
        "Summarize the file",
        "Store: Python is great",
        "List all tables",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex}", use_container_width=True):
            st.session_state["prefill"] = ex
            st.rerun()

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.total_queries = 0
        st.session_state.tools_used = []
        st.rerun()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:24px 0 10px 0;">
    <h1 style="font-size:2.4rem;font-weight:800;background:linear-gradient(135deg,#7c3aed,#db2777,#f59e0b);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin:0;letter-spacing:-0.02em;">
        ToolPilot Agent
    </h1>
    <p style="color:#7c3aed;font-size:0.88rem;margin-top:6px;font-weight:500;">
        Powered by LLM &nbsp;·&nbsp; RAG &nbsp;·&nbsp; SQLite &nbsp;·&nbsp; MCP
    </p>
</div>
""", unsafe_allow_html=True)

# ── Chat history ──────────────────────────────────────────────────────────────
with st.container():
    if not st.session_state.messages and not st.session_state.is_thinking:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">🧭</div>
            <div class="empty-text">Ask me anything</div>
            <div class="empty-sub">I'll automatically pick the right tool and get you an answer.</div>
        </div>""", unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="user-bubble">👤 &nbsp;{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                status_html = ""
                for s in msg.get("statuses", []):
                    status_html += f'<div class="status-row"><span class="status-tool">{s["tool"]}</span><span>{s["status"]}</span></div>'

                plan_html = ""
                if msg.get("plan"):
                    steps = msg["plan"].get("steps", [])
                    badges = "".join([f'<span class="tool-badge">{s["tool"]}</span>' for s in steps])
                    plan_html = f'<div class="plan-box">🗺️ &nbsp;Plan: {badges}</div>'

                content = str(msg["content"]).replace("\n", "<br>")
                st.markdown(
                    f'<div class="agent-bubble">🧭 &nbsp;{content}{status_html}{plan_html}</div>',
                    unsafe_allow_html=True
                )

        if st.session_state.is_thinking:
            st.markdown("""
            <div class="loader-dots">
                <span></span><span></span><span></span>
                <span class="loader-label">Thinking...</span>
            </div>""", unsafe_allow_html=True)

# ── Input form ────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
prefill = st.session_state.pop("prefill", "")

with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input(
            label="query",
            value=prefill,
            placeholder="Ask anything — I'll route it to the right tool...",
            label_visibility="collapsed"
        )
    with col2:
        submitted = st.form_submit_button("Send →")

# ── Process ───────────────────────────────────────────────────────────────────
if submitted and user_input.strip():
    query = user_input.strip()
    st.session_state.messages.append({"role": "user", "content": query})
    st.session_state.total_queries += 1
    st.session_state.is_thinking = True
    st.rerun()

if st.session_state.is_thinking:
    last_user = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"), None)
    if last_user:
        history = st.session_state.messages[:-1][-6:]
        try:
            plan, result, tool_statuses = run_agent(last_user, history=history)
            for step in plan.get("steps", []):
                st.session_state.tools_used.append(step.get("tool", ""))
            st.session_state.messages.append({
                "role": "agent",
                "content": result,
                "plan": plan,
                "statuses": tool_statuses
            })
        except Exception as e:
            st.session_state.messages.append({
                "role": "agent",
                "content": f"Something went wrong: {str(e)}",
                "plan": None,
                "statuses": []
            })
        finally:
            st.session_state.is_thinking = False
            st.rerun()
