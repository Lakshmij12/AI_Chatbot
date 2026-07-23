"""
A web-based chatbot using Streamlit

Everything so far ran in the terminal. Streamlit turns the same bot into a
real chat webpage — a text box, chat bubbles, and streaming replies — with
almost no extra code.

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

MODEL = "claude-opus-4-8"

client = anthropic.Anthropic()

# Each personality is just a name mapped to a system prompt. Add your own!
PERSONALITIES = {
    "Friendly assistant": "You are a friendly, helpful assistant.",
    "Python tutor": "You are a patient Python tutor. Explain simply and "
    "always show a tiny code example.",
    "Pirate": "You are a cheerful pirate. Answer helpfully but talk like a "
    "pirate, with 'arr' and nautical slang.",
    "Concise expert": "You are a terse expert. Answer in as few words as "
    "possible, no filler.",
}

st.title("💬 My AI Chatbot")

# --- Sidebar controls ---------------------------------------------------
with st.sidebar:
    persona_name = st.selectbox("Personality", list(PERSONALITIES.keys()))
    if st.button("New chat"):
        st.session_state.history = []
        st.rerun()

system_prompt = PERSONALITIES[persona_name]

# session_state is Streamlit's memory — it survives across button clicks and
# messages. We store the conversation history here.
if "history" not in st.session_state:
    st.session_state.history = []

# Redraw the whole conversation so far (Streamlit reruns the script each time).
for message in st.session_state.history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# The chat input box at the bottom of the page.
prompt = st.chat_input("Type a message...")

if prompt:
    # 1. Show and remember the user's message.
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Stream Claude's reply into a chat bubble.
    with st.chat_message("assistant"):

        def stream_reply():
            """Yield the reply piece by piece so it types out live."""
            with client.messages.stream(
                model=MODEL,
                max_tokens=1024,
                system=system_prompt,  # the chosen personality
                messages=st.session_state.history,
            ) as stream:
                for text in stream.text_stream:
                    yield text

        # st.write_stream prints each piece as it arrives AND returns the
        # full text once done, so we can save it to memory.
        reply = st.write_stream(stream_reply)

    # 3. Remember the bot's reply for the next turn.
    st.session_state.history.append({"role": "assistant", "content": reply})
