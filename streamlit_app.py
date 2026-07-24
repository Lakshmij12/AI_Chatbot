"""
A polished, private, friendly web chatbot using Streamlit

An advanced version of our web app that also solves a real problem:
"chat with your document". Upload a .txt or .pdf and ask questions about it.

Features:
  - Chat with MEMORY and word-by-word STREAMING replies
  - A logo, warm theme, avatars, and clickable example questions
  - A personality picker (including a custom one you write yourself)
  - Reply-length control, clear-chat confirmation, download-your-chat
  - "Chat with your document" — ask questions about a file you upload
  - Privacy-conscious: reads your API key from a secure store, keeps data only
    for the current session, and shows a clear privacy notice

Privacy in plain words:
  - Your messages are sent to Anthropic's API to generate replies. That's how
    the AI works — but this app itself does NOT save your chats to any file or
    server. Everything lives in memory for the current browser session and is
    gone when you refresh or click "Clear chat".
  - Your API key is read from Streamlit secrets or an environment variable,
    never written into the code.

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY="your-key-here"     # Windows: setx ANTHROPIC_API_KEY "..."
    # (or put it in .streamlit/secrets.toml as ANTHROPIC_API_KEY = "...")

Run it (note: 'streamlit run', NOT 'python'):
    streamlit run streamlit_app.py
"""

import os

import anthropic
import streamlit as st
from pypdf import PdfReader

MODEL = "claude-haiku-4-5"

# Avatars shown next to each chat bubble.
USER_AVATAR = "🧑"
BOT_AVATAR = "🤖"

# Our logo, drawn as an SVG so it always looks crisp. (Also in assets/logo.svg.)
LOGO_SVG = """
<svg width="72" height="72" viewBox="0 0 96 96" xmlns="http://www.w3.org/2000/svg">
  <line x1="48" y1="18" x2="48" y2="9" stroke="#FF7A59" stroke-width="4" stroke-linecap="round"/>
  <circle cx="48" cy="6" r="4" fill="#FFC15E"/>
  <rect x="14" y="18" width="68" height="52" rx="16" fill="#FF7A59"/>
  <path d="M34 66 L34 84 L52 66 Z" fill="#FF7A59"/>
  <circle cx="36" cy="41" r="7" fill="#FFF8F2"/>
  <circle cx="60" cy="41" r="7" fill="#FFF8F2"/>
  <circle cx="36" cy="42" r="3" fill="#2B2B2B"/>
  <circle cx="60" cy="42" r="3" fill="#2B2B2B"/>
  <path d="M36 53 Q48 61 60 53" stroke="#FFF8F2" stroke-width="4" fill="none" stroke-linecap="round"/>
</svg>
"""

PERSONALITIES = {
    "😊 Friendly helper": "You are a warm, friendly assistant.",
    "🐍 Python tutor": "You are a patient, encouraging Python tutor. Explain "
    "simply and always show a tiny code example.",
    "🏴‍☠️ Pirate": "You are a cheerful pirate. Answer helpfully but talk like "
    "a pirate, with 'arr' and nautical slang.",
    "⚡ Quick answers": "You are a concise assistant. Answer briefly and "
    "clearly, no filler.",
}
CUSTOM_OPTION = "✏️ Custom (write your own)"

FRIENDLY_TOUCH = (
    " Always be warm, kind, and encouraging. Greet the user, use their name if "
    "they share it, and keep answers clear and easy to follow. If a question is "
    "unclear, ask a gentle follow-up rather than guessing."
)

LENGTHS = {"Short": 300, "Medium": 1024, "Long": 2048}

# How much of an uploaded document we include (keeps requests fast and cheap).
MAX_DOC_CHARS = 24000


def get_api_key():
    """Read the API key from Streamlit secrets first, then an env var.

    Keeping the key out of the code is the core privacy/security practice.
    """
    return get_secret("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")


def read_document(uploaded_file):
    """Extract text from an uploaded .txt or .pdf file (kept in memory only)."""
    if uploaded_file.name.lower().endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    else:
        text = uploaded_file.read().decode("utf-8", errors="ignore")
    return text[:MAX_DOC_CHARS]


def get_secret(name):
    """Read a secret from Streamlit secrets, or return None if unavailable."""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return None


def require_password():
    """Optional gate: if APP_PASSWORD is set, ask for it before using the app.

    This protects a PUBLIC deployment so strangers can't spend your API credits.
    If no APP_PASSWORD is configured, the app stays open (handy for local use).
    """
    expected = get_secret("APP_PASSWORD")
    if not expected:
        return  # no password configured → app is open
    if st.session_state.get("auth_ok"):
        return
    entered = st.text_input("🔒 Enter password to use this app", type="password")
    if entered:
        if entered == expected:
            st.session_state.auth_ok = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()  # don't render the rest of the app until the password is correct


# --- Page setup ---------------------------------------------------------
st.set_page_config(page_title="My AI Chatbot", page_icon="💬", layout="centered")

st.markdown(
    """
    <style>
      .stButton > button { border-radius: 20px; font-weight: 600; }
      .stChatInput textarea { border-radius: 16px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header: logo + title, centered.
st.markdown(f"<div style='text-align:center'>{LOGO_SVG}</div>", unsafe_allow_html=True)
st.markdown(
    "<h1 style='text-align:center; margin-top:0'>My AI Chatbot</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center; color:#a05a3f'>Your friendly AI assistant — "
    "ask me anything! 🌟</p>",
    unsafe_allow_html=True,
)

# --- Optional password gate (protects a public deployment) --------------
require_password()

# --- API key check (fail kindly if it's missing) ------------------------
api_key = get_api_key()
if not api_key:
    st.error(
        "🔑 No API key found. Set `ANTHROPIC_API_KEY` as an environment variable, "
        "or add it to `.streamlit/secrets.toml`, then reload."
    )
    # Safe diagnostic: show the NAMES of any secrets the app can see (never the
    # values). This helps figure out whether the secret reached the app.
    try:
        secret_names = list(st.secrets.keys())
        st.caption(f"🔍 Secrets the app can see: {secret_names or 'none'}")
    except Exception as diagnostic_error:
        st.caption(f"🔍 Couldn't read secrets: {diagnostic_error}")
    st.stop()
client = anthropic.Anthropic(api_key=api_key)

# --- Sidebar controls ---------------------------------------------------
with st.sidebar:
    st.markdown(f"<div style='text-align:center'>{LOGO_SVG}</div>", unsafe_allow_html=True)
    st.header("⚙️ Settings")

    persona_name = st.selectbox(
        "Choose a personality", list(PERSONALITIES.keys()) + [CUSTOM_OPTION]
    )
    if persona_name == CUSTOM_OPTION:
        base_prompt = st.text_area(
            "Describe your bot's personality",
            "You are a helpful, friendly assistant.",
        )
    else:
        base_prompt = PERSONALITIES[persona_name]

    length = st.select_slider(
        "Reply length", options=list(LENGTHS.keys()), value="Medium"
    )

    st.divider()

    # --- Chat with your document (a real, useful feature) ---------------
    st.subheader("📄 Chat with a document")
    uploaded = st.file_uploader(
        "Upload a .txt or .pdf, then ask about it", type=["txt", "pdf"]
    )
    if uploaded is not None:
        st.session_state.doc_text = read_document(uploaded)
        st.session_state.doc_name = uploaded.name
        st.success(f"Loaded: {uploaded.name}")
    else:
        # File removed → forget its contents.
        st.session_state.pop("doc_text", None)
        st.session_state.pop("doc_name", None)

    st.divider()

    # Clear chat — with a confirmation so it's not accidental.
    if st.button("🗑️ Clear chat"):
        st.session_state.confirm_clear = True
    if st.session_state.get("confirm_clear"):
        st.warning("Clear the whole conversation?")
        yes, no = st.columns(2)
        if yes.button("Yes, clear"):
            st.session_state.history = []
            st.session_state.confirm_clear = False
            st.rerun()
        if no.button("Cancel"):
            st.session_state.confirm_clear = False
            st.rerun()

    # Download the conversation as a text file (only when the user clicks).
    if st.session_state.get("history"):
        transcript = "\n\n".join(
            f"{'You' if m['role'] == 'user' else 'Bot'}: {m['content']}"
            for m in st.session_state.history
        )
        st.download_button("⬇️ Download chat", transcript, file_name="my_chat.txt")

    st.divider()

    # --- Privacy notice ------------------------------------------------
    with st.expander("🔒 Privacy"):
        st.markdown(
            "- Your messages are sent to **Anthropic's API** to generate "
            "replies — that's how the AI works.\n"
            "- This app does **not** save your chats or documents to any file "
            "or server. They stay in memory for this session only and are "
            "erased when you refresh or click **Clear chat**.\n"
            "- Your API key is read from a secure store, never stored in the "
            "code.\n"
            "- Please avoid sharing passwords or other sensitive personal "
            "information in chat."
        )

# Build the system prompt: personality + friendliness (+ document if provided).
system_prompt = base_prompt + FRIENDLY_TOUCH
if st.session_state.get("doc_text"):
    system_prompt += (
        f"\n\nThe user has shared a document titled "
        f"'{st.session_state['doc_name']}'. Use it to answer their questions "
        "when relevant, and say clearly when the answer isn't in the document."
        "\n\n--- DOCUMENT START ---\n"
        + st.session_state["doc_text"]
        + "\n--- DOCUMENT END ---"
    )

# session_state is Streamlit's memory — it survives across clicks and messages.
if "history" not in st.session_state:
    st.session_state.history = []

# Show which document is active, if any.
if st.session_state.get("doc_name"):
    st.caption(f"📄 Answering from your document: **{st.session_state['doc_name']}**")

# --- Friendly welcome + example questions (only before the chat starts) --
if not st.session_state.history:
    st.info("👋 Hi there! I'm here to help. Tap an example below, upload a "
            "document in the sidebar, or just type a message.")
    examples = [
        "Tell me a fun fact 🎉",
        "Help me learn Python 🐍",
        "Give me an idea for today ✨",
    ]
    cols = st.columns(len(examples))
    for col, example in zip(cols, examples):
        if col.button(example):
            st.session_state.pending = example

# --- Show the conversation so far ---------------------------------------
for message in st.session_state.history:
    avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# The message can come from the text box OR from an example button click.
typed = st.chat_input("Ask me anything…")
user_input = typed or st.session_state.pop("pending", None)

if user_input:
    st.session_state.history.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar=BOT_AVATAR):

        def stream_reply():
            """Yield the reply piece by piece so it types out live."""
            with client.messages.stream(
                model=MODEL,
                max_tokens=LENGTHS[length],
                system=system_prompt,
                messages=st.session_state.history,
            ) as stream:
                for text in stream.text_stream:
                    yield text

        reply = st.write_stream(stream_reply)

    st.session_state.history.append({"role": "assistant", "content": reply})
