"""
A polished, friendly web chatbot using Streamlit

A more advanced version of our web app: a logo, a welcoming header, chat
avatars, streaming replies, clickable example questions, a personality picker
(including a custom one you write yourself), a reply-length control, a
clear-chat confirmation, and a download-your-chat button.

It keeps MEMORY (Streamlit's session_state) and STREAMS replies word-by-word.
The "personality" is just a system prompt — the instruction that tells Claude
how to behave.

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY="your-key-here"     # Windows: setx ANTHROPIC_API_KEY "..."

Run it (note: 'streamlit run', NOT 'python'):
    streamlit run streamlit_app.py

Your browser opens automatically at http://localhost:8501
"""

import anthropic
import streamlit as st

MODEL = "claude-haiku-4-5"

client = anthropic.Anthropic()

# Avatars shown next to each chat bubble.
USER_AVATAR = "🧑"
BOT_AVATAR = "🤖"

# Our logo, drawn as an SVG so it always looks crisp. (Also saved in assets/logo.svg.)
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

# Each personality is just a name mapped to a system prompt. Add your own!
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

# Added to EVERY personality so the bot always feels warm and welcoming.
FRIENDLY_TOUCH = (
    " Always be warm, kind, and encouraging. Greet the user, use their name if "
    "they share it, and keep answers clear and easy to follow. If a question is "
    "unclear, ask a gentle follow-up rather than guessing."
)

# Reply-length choices map to how many tokens Claude may use.
LENGTHS = {"Short": 300, "Medium": 1024, "Long": 2048}

# --- Page setup ---------------------------------------------------------
st.set_page_config(page_title="My AI Chatbot", page_icon="💬", layout="centered")

# A little CSS polish: rounded buttons and inputs.
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

    # Download the conversation as a text file.
    if st.session_state.get("history"):
        transcript = "\n\n".join(
            f"{'You' if m['role'] == 'user' else 'Bot'}: {m['content']}"
            for m in st.session_state.history
        )
        st.download_button("⬇️ Download chat", transcript, file_name="my_chat.txt")

    st.divider()
    st.caption("💡 Tip: pick a personality — or write your own — and set how "
               "long replies should be.")

system_prompt = base_prompt + FRIENDLY_TOUCH
max_tokens = LENGTHS[length]

# session_state is Streamlit's memory — it survives across clicks and messages.
if "history" not in st.session_state:
    st.session_state.history = []

# --- Friendly welcome + example questions (only before the chat starts) --
if not st.session_state.history:
    st.info("👋 Hi there! I'm here to help. Tap an example below, or type your "
            "own message at the bottom.")
    examples = [
        "Tell me a fun fact 🎉",
        "Help me learn Python 🐍",
        "Give me an idea for today ✨",
    ]
    cols = st.columns(len(examples))
    for col, example in zip(cols, examples):
        if col.button(example):
            # Remember the clicked question so we handle it like typed input.
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
    # 1. Show and remember the user's message.
    st.session_state.history.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(user_input)

    # 2. Stream Claude's reply into a chat bubble.
    with st.chat_message("assistant", avatar=BOT_AVATAR):

        def stream_reply():
            """Yield the reply piece by piece so it types out live."""
            with client.messages.stream(
                model=MODEL,
                max_tokens=max_tokens,
                system=system_prompt,  # chosen personality + the friendly touch
                messages=st.session_state.history,
            ) as stream:
                for text in stream.text_stream:
                    yield text

        # st.write_stream prints each piece as it arrives AND returns the
        # full text once done, so we can save it to memory.
        reply = st.write_stream(stream_reply)

    # 3. Remember the bot's reply for the next turn.
    st.session_state.history.append({"role": "assistant", "content": reply})
