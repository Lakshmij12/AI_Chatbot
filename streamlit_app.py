"""
A friendly web-based chatbot using Streamlit

Streamlit turns our chatbot into a warm, welcoming chat webpage — chat
bubbles, avatars, streaming replies, example questions to click, and a
personality picker.

It keeps MEMORY (using Streamlit's session_state), STREAMS the reply so it
appears word-by-word, and lets you pick a PERSONALITY from the sidebar.

The personality is just a different "system prompt" — the instruction that
tells Claude how to behave. Swapping it changes the bot's whole character.

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

# We add this to EVERY personality so the bot always feels warm and welcoming.
FRIENDLY_TOUCH = (
    " Always be warm, kind, and encouraging. Greet the user, use their name if "
    "they share it, and keep answers clear and easy to follow. If a question is "
    "unclear, ask a gentle follow-up rather than guessing."
)

# --- Page setup ---------------------------------------------------------
st.set_page_config(page_title="My AI Chatbot", page_icon="💬", layout="centered")

st.title("💬 My AI Chatbot")
st.caption("Your friendly AI assistant — ask me anything! 🌟")

# --- Sidebar controls ---------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    persona_name = st.selectbox("Choose a personality", list(PERSONALITIES.keys()))
    if st.button("🗑️ Start a new chat"):
        st.session_state.history = []
        st.rerun()
    st.caption("💡 Tip: switch the personality any time — the bot's whole "
               "style changes!")

system_prompt = PERSONALITIES[persona_name] + FRIENDLY_TOUCH

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
            # Remember the clicked question so we handle it just like typed input.
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
                max_tokens=1024,
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
