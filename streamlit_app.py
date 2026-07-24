"""
An advanced, private, friendly web chatbot using Streamlit

Feels like Claude / ChatGPT, built on Claude:
  - MULTIPLE conversations — start new chats, switch between them, delete them
    (each keeps its own memory; they're auto-named from your first message)
  - A MODEL picker — fast & cheap (Haiku) or smartest (Opus)
  - REGENERATE the last reply, or one-tap "Try again" if something errors
  - Word-by-word STREAMING replies with chat avatars
  - A personality picker (including a custom one you write yourself)
  - Reply-length control and download-your-chat
  - "Chat with your document" — upload a .txt/.pdf and ask about it
  - Privacy-conscious: key from a secure store, session-only data, clear notice
  - Friendly error handling so it never shows a scary crash

Privacy in plain words:
  - Your messages go to Anthropic's API to generate replies. This app itself
    saves nothing to disk or any server — everything lives in memory for the
    current session and is gone on refresh.
  - Your API key is read from Streamlit secrets or an environment variable.

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY="your-key-here"     # Windows: setx ANTHROPIC_API_KEY "..."

Run it (note: 'streamlit run', NOT 'python'):
    streamlit run streamlit_app.py
"""

import os
import uuid

import anthropic
import streamlit as st
from pypdf import PdfReader

# Avatars shown next to each chat bubble.
USER_AVATAR = "🧑"
BOT_AVATAR = "🤖"

# Model choices: friendly label -> model id.
MODELS = {
    "⚡ Fast & cheap (Haiku)": "claude-haiku-4-5",
    "🧠 Smartest (Opus)": "claude-opus-4-8",
}

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


def get_secret(name):
    """Read a secret from Streamlit secrets, or return None if unavailable."""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return None


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


def require_password():
    """Optional gate: if APP_PASSWORD is set, ask for it before using the app.

    This protects a PUBLIC deployment so strangers can't spend your API credits.
    If no APP_PASSWORD is configured, the app stays open (handy for local use).
    """
    expected = get_secret("APP_PASSWORD")
    if not expected:
        return
    if st.session_state.get("auth_ok"):
        return
    entered = st.text_input("🔒 Enter password to use this app", type="password")
    if entered:
        if entered == expected:
            st.session_state.auth_ok = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()


# --- Conversation helpers (multiple chats, like Claude/ChatGPT) ----------
def new_chat():
    """Create a fresh conversation and make it the current one."""
    chat_id = str(uuid.uuid4())
    st.session_state.chats[chat_id] = {"title": "New chat", "history": []}
    st.session_state.current_chat = chat_id
    return chat_id


def current_history():
    """The message list for the active conversation."""
    return st.session_state.chats[st.session_state.current_chat]["history"]


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
    st.stop()
client = anthropic.Anthropic(api_key=api_key)

# --- Make sure there's always at least one conversation -----------------
if "chats" not in st.session_state:
    st.session_state.chats = {}
if (
    "current_chat" not in st.session_state
    or st.session_state.current_chat not in st.session_state.chats
):
    new_chat()

# --- Sidebar controls ---------------------------------------------------
with st.sidebar:
    st.markdown(f"<div style='text-align:center'>{LOGO_SVG}</div>", unsafe_allow_html=True)

    # --- Conversations list (new / switch / delete) --------------------
    st.header("💬 Conversations")
    if st.button("➕ New chat", use_container_width=True):
        new_chat()
        st.rerun()

    for chat_id, chat in list(st.session_state.chats.items()):
        is_active = chat_id == st.session_state.current_chat
        label = ("🟢 " if is_active else "💬 ") + (chat["title"] or "New chat")
        if st.button(label, key=f"chat_{chat_id}", use_container_width=True):
            st.session_state.current_chat = chat_id
            st.rerun()

    # Delete the active conversation.
    if st.button("🗑️ Delete this chat", use_container_width=True):
        del st.session_state.chats[st.session_state.current_chat]
        if st.session_state.chats:
            st.session_state.current_chat = next(iter(st.session_state.chats))
        else:
            new_chat()
        st.rerun()

    st.divider()
    st.header("⚙️ Settings")

    # Model picker.
    model_label = st.selectbox(
        "Model", list(MODELS.keys()),
        help="Haiku is fast and very cheap. Opus is the smartest but costs more.",
    )
    model = MODELS[model_label]

    # Personality picker (with a custom option).
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

    # --- Chat with your document ---------------------------------------
    st.subheader("📄 Chat with a document")
    uploaded = st.file_uploader(
        "Upload a .txt or .pdf, then ask about it", type=["txt", "pdf"]
    )
    if uploaded is not None:
        try:
            st.session_state.doc_text = read_document(uploaded)
            st.session_state.doc_name = uploaded.name
            st.success(f"Loaded: {uploaded.name}")
        except Exception:
            st.session_state.pop("doc_text", None)
            st.session_state.pop("doc_name", None)
            st.error("Couldn't read that file. Try a different .txt or .pdf.")
    else:
        st.session_state.pop("doc_text", None)
        st.session_state.pop("doc_name", None)

    # Download the current conversation as a text file.
    if current_history():
        transcript = "\n\n".join(
            f"{'You' if m['role'] == 'user' else 'Bot'}: {m['content']}"
            for m in current_history()
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
            "erased when you refresh.\n"
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


def generate_reply():
    """Stream a reply for the active conversation. Returns True on success.

    On any API problem we show a friendly message instead of a scary error,
    and leave the user's message in place so they can tap "Try again".
    """
    history = current_history()
    try:
        with st.chat_message("assistant", avatar=BOT_AVATAR):

            def stream_reply():
                with client.messages.stream(
                    model=model,
                    max_tokens=LENGTHS[length],
                    system=system_prompt,
                    messages=history,
                ) as stream:
                    for text in stream.text_stream:
                        yield text

            reply = st.write_stream(stream_reply)

        reply = reply or "🤔 I didn't quite catch that — could you rephrase?"
        history.append({"role": "assistant", "content": reply})
        return True
    except anthropic.RateLimitError:
        st.warning("😅 Lots of requests right now. Wait a few seconds, then tap "
                   "**🔄 Try again**.")
    except anthropic.AuthenticationError:
        st.error("🔑 There's a problem with the API key. Check it in the app "
                 "settings.")
    except anthropic.APIConnectionError:
        st.warning("🌐 Network hiccup. Check your connection, then tap "
                   "**🔄 Try again**.")
    except anthropic.APIStatusError:
        st.warning("⏳ The AI service is busy. Please tap **🔄 Try again** in a "
                   "moment.")
    except Exception:
        st.error("😕 Something went wrong. Please tap **🔄 Try again**.")
    return False


# Show which document is active, if any.
if st.session_state.get("doc_name"):
    st.caption(f"📄 Answering from your document: **{st.session_state['doc_name']}**")

# --- Friendly welcome + example questions (only before the chat starts) --
if not current_history():
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
for message in current_history():
    avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# The message can come from the text box OR from an example button click.
typed = st.chat_input("Ask me anything…")
user_input = typed or st.session_state.pop("pending", None)

if user_input:
    history = current_history()
    history.append({"role": "user", "content": user_input})

    # Auto-name a brand-new conversation from the first message.
    chat = st.session_state.chats[st.session_state.current_chat]
    if chat["title"] == "New chat":
        chat["title"] = user_input[:38] + ("…" if len(user_input) > 38 else "")

    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(user_input)
    generate_reply()

# --- Action buttons under the conversation ------------------------------
history = current_history()
if history and history[-1]["role"] == "assistant" and len(history) >= 2:
    # Normal completed turn → offer to regenerate the last answer.
    if st.button("🔄 Regenerate"):
        history.pop()  # drop the last assistant reply and make a new one
        if generate_reply():
            st.rerun()
elif history and history[-1]["role"] == "user":
    # Last turn didn't get an answer (e.g. an error) → offer a retry.
    if st.button("🔄 Try again"):
        if generate_reply():
            st.rerun()
