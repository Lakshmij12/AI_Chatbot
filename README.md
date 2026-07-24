# How to Build AI Chatbots

A hands-on, step-by-step guide to building chatbots in Python — starting from
a simple bot with no AI, then building up to a real AI chatbot that has memory,
does math, searches the web, and answers instantly.

## The steps

| File | What it teaches | Needs an API key? |
| --- | --- | --- |
| `1_rule_based_bot.py` | The basic chat loop: read input → reply → repeat | No |
| `2_ai_chatbot.py` | Sending a message to Claude and getting a smart reply | Yes |
| `3_ai_chatbot_memory.py` | Giving the bot **memory** of the conversation | Yes |
| `4_ai_chatbot_tools.py` | Memory **+ a calculator tool** for exact math | Yes |
| `5_ai_chatbot_web.py` | Memory **+ web search** for real, current answers | Yes |
| `6_ai_chatbot_streaming.py` | Memory **+ instant, word-by-word** answers (streaming) | Yes |
| `7_ai_chatbot_full.py` | **Everything combined**: memory + calculator + web + streaming | Yes |
| `streamlit_app.py` | A **web app** version — a real chat page in your browser | Yes |
| `whatsapp_bot.py` | A **WhatsApp** version — chat with the bot from WhatsApp (see [WHATSAPP.md](WHATSAPP.md)) | Yes |

> 🌐 **Want to put the web app online?** See [DEPLOY.md](DEPLOY.md) — deploy it free to Streamlit Community Cloud, with your API key kept private and an optional password to protect your credits.

Work through the numbered files in order — each one builds on the idea before
it. `streamlit_app.py` is a bonus: the chatbot as a web page instead of the
terminal.

## How to run

### 1. Get the code
```
git clone https://github.com/Lakshmij12/AI_Chatbot.git
cd AI_Chatbot
```

### 2. Run the no-setup bot first (no API key needed)
```
python 1_rule_based_bot.py
```
Type `hello`, chat with it, and type `bye` to quit. If `python` doesn't work,
try `python3`.

### 3. Set up the AI bots (steps 2–7)
```
pip install -r requirements.txt
```
Get an API key from https://console.anthropic.com, then give it to your
terminal (never paste it into the code):
```
# Mac / Linux
export ANTHROPIC_API_KEY="your-key-here"

# Windows (PowerShell)
setx ANTHROPIC_API_KEY "your-key-here"
```
On Windows, close and reopen the terminal after `setx` so it takes effect.

### 4. Run any AI bot
```
python 3_ai_chatbot_memory.py     # remembers what you say
python 7_ai_chatbot_full.py       # the full one: memory + math + web + streaming
```
Type your message, press Enter, and type `bye` to quit.

### 5. Or run the web app
For a real chat page in your browser instead of the terminal, use `streamlit`
(note: `streamlit run`, **not** `python`):
```
streamlit run streamlit_app.py
```
It opens automatically at http://localhost:8501.

## The web app (`streamlit_app.py`) — features

The web app is a full, ChatGPT/Claude-style chatbot:

- 💬 **Multiple conversations** — start new chats, switch between them, and
  delete them from the sidebar. Each keeps its own memory and is auto-named
  from your first message.
- 🧠 **Model picker** — ⚡ fast & cheap (Haiku) or 🧠 smartest (Opus).
- 🖼️ **Image upload (vision)** — attach a picture and ask questions about it.
- 🎙️ **Voice input** — speak instead of typing (needs `streamlit-mic-recorder`;
  works best in Chrome).
- 📄 **Chat with a document** — upload a `.txt` or `.pdf` and ask about it.
- 🎭 **Personalities** — friendly helper, Python tutor, pirate, quick answers,
  or write your **own** custom personality.
- 📏 **Reply-length control**, ⬇️ **download chat**, 🔄 **regenerate** replies,
  and 👍/👎 **feedback** buttons.
- 🌊 **Streaming** replies, a logo, a warm theme, and chat avatars.
- 🔒 **Privacy** — your API key is read from a secure store (never in the code),
  nothing is saved to disk, and there's an optional password gate.
- 🛟 **Friendly error handling** — no scary crashes, with a one-tap "Try again".

Put it online (free) with [DEPLOY.md](DEPLOY.md).

### Common hiccups
- **`python: command not found`** → use `python3` instead.
- **`No module named anthropic`** → re-run `pip install -r requirements.txt`
  (or `pip3`).
- **`AuthenticationError` / no API key** → the key isn't set in *this* terminal
  window. Re-run the `export` / `setx` step (reopen the terminal on Windows).

## How a chatbot works

Every chatbot, simple or advanced, follows the same loop:

1. **Read** what the user typed.
2. **Decide** on a reply.
3. **Print** the reply.
4. **Repeat** until the user quits.

The only thing that changes is *step 2*:
- The **rule-based bot** decides the reply with hand-written `if`/`else` rules.
- The **AI bot** asks Claude (a large language model) to write the reply.

## The big ideas

### Memory (step 3)

The Claude API is **stateless** — it does not remember previous messages on
its own. To give a bot memory, *we* keep the conversation in a list and send
the whole list on every request:

```python
history = []
history.append({"role": "user", "content": message})    # remember what you said
response = client.messages.create(..., messages=history)  # send the whole history
history.append({"role": "assistant", "content": reply})  # remember the bot's reply
```

### Tools (steps 4 & 5)

A tool lets the bot *do* things, not just talk. When a question needs a tool,
Claude asks for it, we run it (or Anthropic runs it), and Claude uses the
result in its answer.

- **Calculator (step 4)** is a tool *we* run: language models are unreliable
  at exact math, so we hand Claude a real Python calculator.
- **Web search (step 5)** is a *server-side* tool: Anthropic runs the search,
  so the bot can answer questions about current, real-world information.

### Streaming (step 6)

Instead of waiting for the whole reply, streaming prints it word-by-word as
it's generated, so answers feel instant.

### Everything together (step 7)

`7_ai_chatbot_full.py` combines all of the above into one bot. The interesting
part is the loop: with streaming *and* tools, a single question can take a few
rounds — stream a reply, run a tool if Claude asks, stream the continuation,
and repeat until there's a final answer.

## Where to go next

- Give your bot a stronger **personality** with a detailed system prompt.
- Add more tools — the weather, a to-do list, your own data.
