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

Work through them in order — each one builds on the idea before it.

## How a chatbot works

Every chatbot, simple or advanced, follows the same loop:

1. **Read** what the user typed.
2. **Decide** on a reply.
3. **Print** the reply.
4. **Repeat** until the user quits.

The only thing that changes is *step 2*:
- The **rule-based bot** decides the reply with hand-written `if`/`else` rules.
- The **AI bot** asks Claude (a large language model) to write the reply.

## Setup for the AI bots (steps 2–6)

1. Install the library:
   ```
   pip install -r requirements.txt
   ```
2. Get an API key from https://console.anthropic.com
3. Save the key as an environment variable so the code can read it safely
   (never paste your key directly into the code):
   ```
   # Mac / Linux
   export ANTHROPIC_API_KEY="your-key-here"

   # Windows
   setx ANTHROPIC_API_KEY "your-key-here"
   ```

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

## Where to go next

- Combine everything: one bot with memory, the calculator, web search, **and**
  streaming.
- Give your bot a stronger **personality** with a detailed system prompt.
- Add more tools — the weather, a to-do list, your own data.
