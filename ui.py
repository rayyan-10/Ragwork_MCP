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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }

.stApp {
    background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    min-height: 100vh;
}

[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.03);
    border-right: 1px solid rgba(255,255,255,0.08);
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }

/* ── Input text ── */
.stTextInput > div > div > input {
    background: #1e2235 !important;
    border: 1.5px solid rgba(102,126,234,0.4) !important;
    border-radius: 14px !important;
    color: #f0f4ff !important;
    padding: 13px 18px !important;
    font-size: 0.95rem !important;
    caret-color: #a78bfa !important;
}
.stTextInput > div > div > input::placeholder { color: #4a5568 !important; }
.stTextInput > div > div > input:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 3px rgba(102,126,234,0.2) !important;
    outline: none !important;
}

/* ── Upload section ── */
.upload-section {
    background: linear-gradient(135deg, rgba(102,126,234,0.12), rgba(167,139,250,0.08));
    border: 1.5px solid rgba(102,126,234,0.35);
    border-radius: 14px;
    padding: 14px 14px 10px 14px;
    margin: 4px 0 10px 0;
}
.upload-title {
    font-size: 0.88rem;
    font-weight: 700;
    color: #a78bfa !important;
    letter-spacing: 0.03em;
    margin-bottom: 2px;
}
.upload-sub {
    font-size: 0.72rem;
    color: #667eea !important;
    margin-bottom: 8px;
}
.upload-status-ok {
    background: rgba(72,187,120,0.12);
    border: 1px solid rgba(72,187,120,0.3);
    border-radius: 8px;
    padding: 7px 10px;
    font-size: 0.78rem;
    color: #68d391 !important;
    margin-top: 6px;
}
.upload-status-info {
    background: rgba(102,126,234,0.1);
    border: 1px solid rgba(102,126,234,0.25);
    border-radius: 8px;
    padding: 7px 10px;
    font-size: 0.78rem;
    color: #a78bfa !important;
    margin-top: 6px;
}

/* ── Bubbles ── */
.user-bubble {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    padding: 14px 20px;
    border-radius: 20px 20px 4px 20px;
    margin: 10px 0 10px 80px;
    font-size: 0.95rem;
    line-height: 1.7;
    box-shadow: 0 4px 20px rgba(102,126,234,0.35);
    animation: fadeSlideLeft 0.3s ease;
}
.agent-bubble {
    background: rgba(255,255,255,0.055);
    border: 1px solid rgba(255,255,255,0.1);
    color: #e2e8f0;
    padding: 14px 20px;
    border-radius: 20px 20px 20px 4px;
    margin: 10px 80px 10px 0;
    font-size: 0.95rem;
    line-height: 1.7;
    backdrop-filter: blur(12px);
    animation: fadeSlideRight 0.3s ease;
}

/* ── Plan box ── */
.plan-box {
    background: rgba(102,126,234,0.07);
    border: 1px solid rgba(102,126,234,0.18);
    border-radius: 10px;
    padding: 10px 14px;
    margin-top: 10px;
    font-size: 0.8rem;
    color: #a0aec0;
}
.tool-badge {
    display: inline-block;
    background: rgba(102,126,234,0.18);
    border: 1px solid rgba(102,126,234,0.35);
    color: #a78bfa;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.73rem;
    font-weight: 600;
    margin: 2px 3px;
}

/* ── Status row ── */
.status-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 5px 0;
    font-size: 0.82rem;
    color: #cbd5e0;
    border-top: 1px solid rgba(255,255,255,0.05);
    margin-top: 6px;
}
.status-tool {
    background: rgba(167,139,250,0.15);
    color: #a78bfa;
    padding: 1px 8px;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 600;
}

/* ── Animated loader ── */
@keyframes pulse-dot {
    0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
    40% { transform: scale(1); opacity: 1; }
}
.loader-dots {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 14px 20px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px 20px 20px 4px;
    margin: 10px 80px 10px 0;
    width: fit-content;
}
.loader-dots span {
    width: 8px; height: 8px;
    background: #667eea;
    border-radius: 50%;
    display: inline-block;
    animation: pulse-dot 1.2s infinite ease-in-out;
}
.loader-dots span:nth-child(2) { animation-delay: 0.2s; background: #a78bfa; }
.loader-dots span:nth-child(3) { animation-delay: 0.4s; background: #764ba2; }
.loader-label { font-size: 0.8rem; color: #4a5568; margin-left: 4px; }

/* ── Animations ── */
@keyframes fadeSlideLeft {
    from { opacity: 0; transform: translateX(20px); }
    to   { opacity: 1; transform: translateX(0); }
}
@keyframes fadeSlideRight {
    from { opacity: 0; transform: translateX(-20px); }
    to   { opacity: 1; transform: translateX(0); }
}

/* ── Metric cards ── */
.metric-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 14px;
    text-align: center;
}
.metric-value { font-size: 1.7rem; font-weight: 700; color: #a78bfa; }
.metric-label { font-size: 0.72rem; color: #4a5568; margin-top: 3px; text-transform: uppercase; letter-spacing: 0.05em; }

/* ── Button ── */
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 9px 20px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 14px rgba(102,126,234,0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(102,126,234,0.45) !important;
}

/* ── File uploader override ── */
[data-testid="stFileUploader"] {
    background: rgba(102,126,234,0.06) !important;
    border: 1.5px dashed rgba(102,126,234,0.4) !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploader"] * { color: #a78bfa !important; }

.custom-divider { border: none; border-top: 1px solid rgba(255,255,255,0.06); margin: 14px 0; }
.logo-text {
    font-size: 1.45rem; font-weight: 700;
    background: linear-gradient(135deg, #667eea, #a78bfa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.logo-sub { font-size: 0.72rem; color: #4a5568; margin-top: -3px; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in [
    ("messages", []),
    ("total_queries", 0),
    ("tools_used", []),
    ("is_thinking", False),
    ("upload_status", {}),       # tracks upload results per filename
    ("last_uploaded", None),     # tracks last uploaded filename
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

    # ── Upload Document (above tools) ─────────────────────────────────────────
    st.markdown("""
    <div class="upload-section">
        <div class="upload-title">📎 Upload Document</div>
        <div class="upload-sub">PDF, DOCX or TXT · Ask questions after upload</div>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        label="upload",
        type=["pdf", "docx", "txt"],
        label_visibility="collapsed",
        key="doc_uploader"
    )

    # Process upload WITHOUT triggering rerun that clears chat
    if uploaded_file is not None:
        fname = uploaded_file.name
        if fname not in st.session_state.upload_status:
            # Mark as processing to avoid re-upload on next rerun
            st.session_state.upload_status[fname] = "processing"
            with st.spinner(f"Uploading {fname}..."):
                try:
                    content_b64 = base64.b64encode(uploaded_file.read()).decode("utf-8")
                    result = run_upload(fname, content_b64)
                    st.session_state.upload_status[fname] = result
                    st.session_state.last_uploaded = fname
                except Exception as e:
                    st.session_state.upload_status[fname] = f"❌ Upload failed: {str(e)}"

        # Show status without rerun
        status = st.session_state.upload_status.get(fname, "")
        if status and status != "processing":
            css_class = "upload-status-ok" if "✅" in status or "successfully" in status.lower() else "upload-status-info"
            st.markdown(f'<div class="{css_class}">{status}</div>', unsafe_allow_html=True)

    # Show last uploaded doc indicator
    if st.session_state.last_uploaded:
        st.markdown(
            f'<div style="font-size:0.72rem;color:#667eea;margin-top:4px;">📄 Active: {st.session_state.last_uploaded}</div>',
            unsafe_allow_html=True
        )

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    # ── Available Tools ───────────────────────────────────────────────────────
    st.markdown("**Available Tools**")
    tools_info = {
        "🔍 rag_tool": "Search documents",
        "🌐 web_tool": "Live web search",
        "📄 file_tool": "Read local files",
        "✂️ summary_tool": "Summarize text",
        "🗄️ db_tool": "Query database",
        "🧠 memory_tool": "Save to memory",
    }
    for tool, desc in tools_info.items():
        st.markdown(f'<div style="padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05);"><span style="font-size:0.84rem;color:#e2e8f0;">{tool}</span><br><span style="font-size:0.73rem;color:#4a5568;">{desc}</span></div>', unsafe_allow_html=True)

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    st.markdown("**Try These**")

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
<div style="text-align:center;padding:20px 0 8px 0;">
    <h1 style="font-size:2.1rem;font-weight:700;background:linear-gradient(135deg,#667eea,#a78bfa);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin:0;">
        ToolPilot Agent
    </h1>
    <p style="color:#4a5568;font-size:0.85rem;margin-top:5px;">
        Powered by Groq &nbsp;·&nbsp; RAG &nbsp;·&nbsp; SQLite &nbsp;·&nbsp; MCP
    </p>
</div>
""", unsafe_allow_html=True)

# ── Chat history ──────────────────────────────────────────────────────────────
with st.container():
    if not st.session_state.messages and not st.session_state.is_thinking:
        st.markdown("""
        <div style="text-align:center;padding:70px 20px;">
            <div style="font-size:3.5rem;">🧭</div>
            <div style="font-size:1rem;margin-top:14px;color:#4a5568;">
                Ask me anything — I'll pick the right tool automatically.
            </div>
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
                <span class="loader-label">Agent is thinking...</span>
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
