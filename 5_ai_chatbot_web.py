"""
Step 5: An AI chatbot with MEMORY that can SEARCH THE WEB

A model only knows what it learned during training, so it can't answer
"what's the news today?" on its own. The fix is the built-in web search
tool: Claude searches the web and answers using what it finds.

Web search is a "server-side" tool — unlike the calculator in step 4, we
don't run anything ourselves. We just switch it on and Claude does the
searching for us.

This bot keeps the conversation memory from earlier steps too.

Setup is the same as before (pip install anthropic + set ANTHROPIC_API_KEY).

Run it with:
    python 5_ai_chatbot_web.py
"""

import anthropic

client = anthropic.Anthropic()

MODEL = "claude-haiku-4-5"

# Turn on the built-in web search tool. "max_uses" caps how many searches
# Claude may run per reply, so it doesn't search endlessly.
TOOLS = [
    {"type": "web_search_20250305", "name": "web_search", "max_uses": 5}
]


def main():
    print("AI Bot with memory + web search (type 'bye' to quit)")
    history = []  # the bot's memory

    while True:
        message = input("You: ")
        if message.lower().strip() in ("bye", "quit", "exit"):
            print("Bot: Goodbye!")
            break

        history.append({"role": "user", "content": message})

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system="You are a helpful assistant. Search the web when the "
            "question needs current or factual information, and cite what you find.",
            tools=TOOLS,
            messages=history,
        )

        # Save Claude's full turn (including its search steps) to memory.
        history.append({"role": "assistant", "content": response.content})

        # Print the text parts of the reply. (The response also contains the
        # search results Claude used, which we don't need to print here.)
        for block in response.content:
            if block.type == "text":
                print("Bot:", block.text)


if __name__ == "__main__":
    main()
