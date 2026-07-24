"""
Step 6: An AI chatbot that answers INSTANTLY (streaming) — with memory

So far the bot waited until the whole reply was ready, then printed it all
at once. On longer answers that pause feels slow.

"Streaming" fixes this: the reply appears word-by-word as Claude writes it,
just like a person typing. It's the same request as before — we just read
the answer in small pieces as they arrive.

This bot keeps the conversation memory from earlier steps too.

Setup is the same as before (pip install anthropic + set ANTHROPIC_API_KEY).

Run it with:
    python 6_ai_chatbot_streaming.py
"""

import anthropic

client = anthropic.Anthropic()

MODEL = "claude-haiku-4-5"


def main():
    print("AI Bot with instant (streaming) answers (type 'bye' to quit)")
    history = []  # the bot's memory

    while True:
        message = input("You: ")
        if message.lower().strip() in ("bye", "quit", "exit"):
            print("Bot: Goodbye!")
            break

        history.append({"role": "user", "content": message})

        print("Bot: ", end="", flush=True)

        # client.messages.stream(...) gives us the reply in pieces.
        with client.messages.stream(
            model=MODEL,
            max_tokens=1024,
            system="You are a friendly, helpful assistant.",
            messages=history,
        ) as stream:
            # Print each piece of text the moment it arrives. flush=True
            # forces it onto the screen immediately instead of buffering.
            for text in stream.text_stream:
                print(text, end="", flush=True)

            # Once streaming finishes, grab the complete reply to remember it.
            final = stream.get_final_message()

        print()  # move to a new line after the reply

        history.append({"role": "assistant", "content": final.content})


if __name__ == "__main__":
    main()
