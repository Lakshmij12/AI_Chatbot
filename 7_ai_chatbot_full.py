"""
Step 7: The full chatbot — everything combined

This bot brings together every idea from the earlier steps:
  - MEMORY:    keeps the whole conversation in a `history` list.
  - CALCULATOR: a tool WE run for exact math (from step 4).
  - WEB SEARCH: a tool ANTHROPIC runs for current, real answers (step 5).
  - STREAMING:  the reply appears word-by-word, so it feels instant (step 6).

The tricky part is the loop. When streaming and tools are combined, one user
question can take a few rounds:
    stream a reply -> maybe Claude asks for the calculator -> we run it ->
    stream the continued reply -> ... -> final answer.
We keep looping until Claude has a final answer with no more tool requests.

Setup is the same as before (pip install anthropic + set ANTHROPIC_API_KEY).

Run it with:
    python 7_ai_chatbot_full.py
"""

import ast
import operator

import anthropic

client = anthropic.Anthropic()

MODEL = "claude-haiku-4-5"


# --- The calculator tool (same safe evaluator as step 4) ----------------

_ALLOWED = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def calculate(expression):
    """Safely evaluate a basic math expression like '3 * (4 + 5)'."""

    def _eval(node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.BinOp):
            return _ALLOWED[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp):
            return _ALLOWED[type(node.op)](_eval(node.operand))
        raise ValueError("Only basic arithmetic is allowed.")

    return _eval(ast.parse(expression, mode="eval").body)


# We offer Claude TWO tools at once: our calculator and the built-in web search.
TOOLS = [
    {
        "name": "calculate",
        "description": "Evaluate a math expression (e.g. '12 * (3 + 4)'). "
        "Use this for any calculation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The math expression to evaluate.",
                }
            },
            "required": ["expression"],
        },
    },
    {"type": "web_search_20250305", "name": "web_search", "max_uses": 5},
]

SYSTEM = (
    "You are a friendly, helpful assistant. Use the calculator tool for any "
    "math, and search the web when a question needs current or factual "
    "information. Cite what you find."
)


def run_calculator_tools(response):
    """Run any calculator requests in Claude's reply and return the results."""
    tool_results = []
    for block in response.content:
        # Only the client-side 'calculate' tool needs us to run it.
        # Web search runs on Anthropic's side, so it never appears here.
        if block.type == "tool_use" and block.name == "calculate":
            try:
                result_text = str(calculate(block.input["expression"]))
            except Exception as error:
                result_text = f"Error: {error}"
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result_text,
            })
    return tool_results


def main():
    print("Full AI Bot — memory + calculator + web + streaming (type 'bye' to quit)")
    history = []  # the bot's memory

    while True:
        message = input("You: ")
        if message.lower().strip() in ("bye", "quit", "exit"):
            print("Bot: Goodbye!")
            break

        history.append({"role": "user", "content": message})
        print("Bot: ", end="", flush=True)

        # Keep going until Claude produces a final answer (no more tool work).
        while True:
            with client.messages.stream(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM,
                tools=TOOLS,
                messages=history,
            ) as stream:
                for text in stream.text_stream:
                    print(text, end="", flush=True)
                response = stream.get_final_message()

            # Remember Claude's turn (it may include tool requests).
            history.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "tool_use":
                # Claude wants our calculator — run it and send results back.
                results = run_calculator_tools(response)
                history.append({"role": "user", "content": results})
                continue

            if response.stop_reason == "pause_turn":
                # A long web search paused; loop again to let Claude resume.
                continue

            break  # final answer reached

        print()  # newline after the reply


if __name__ == "__main__":
    main()
