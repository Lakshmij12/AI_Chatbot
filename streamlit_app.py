"""
A web-based chatbot using Streamlit

Everything so far ran in the terminal. Streamlit turns the same bot into a
real chat webpage — a text box, chat bubbles, and streaming replies — with
almost no extra code.

It keeps MEMORY (using Streamlit's session_state) and STREAMS the reply so
it appears word-by-word.

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

st.title("💬 My AI Chatbot")

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
                system="You are a friendly, helpful assistant.",
                messages=st.session_state.history,
            ) as stream:
                for text in stream.text_stream:
                    yield text

        # st.write_stream prints each piece as it arrives AND returns the
        # full text once done, so we can save it to memory.
        reply = st.write_stream(stream_reply)

    # 3. Remember the bot's reply for the next turn.
    st.session_state.history.append({"role": "assistant", "content": reply})

# A button in the sidebar to start a fresh conversation.
with st.sidebar:
    if st.button("New chat"):
        st.session_state.history = []
        st.rerun()
