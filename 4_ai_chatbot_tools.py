"""
Step 4: An AI chatbot with MEMORY + a CALCULATOR tool

Language models are famously shaky at exact math. The fix is "tool use":
we give Claude a real Python calculator it can call. When the user asks a
math question, Claude doesn't guess — it asks our code to do the sum, reads
the result, and answers.

This bot combines both ideas from earlier steps:
  - MEMORY: we keep the whole conversation in a `history` list.
  - TOOLS:  we hand Claude a `calculate` tool it can call when needed.

How tool use works (the loop):
  1. We send the message + the list of tools we offer.
  2. If Claude wants a tool, it replies with stop_reason == "tool_use".
  3. WE run the tool and send the result back.
  4. Claude reads the result and gives the final answer.

Setup is the same as before (pip install anthropic + set ANTHROPIC_API_KEY).

Run it with:
    python 4_ai_chatbot_tools.py
"""

import ast
import operator

import anthropic

client = anthropic.Anthropic()

MODEL = "claude-opus-4-8"


# --- The calculator tool ------------------------------------------------

# We do NOT use Python's eval() on user text — that's unsafe. Instead we
# parse the expression and only allow basic math operations.
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
        if isinstance(node, ast.Constant):          # a number
            return node.value
        if isinstance(node, ast.BinOp):             # a + b, a * b, ...
            return _ALLOWED[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp):           # -a
            return _ALLOWED[type(node.op)](_eval(node.operand))
        raise ValueError("Only basic arithmetic is allowed.")

    tree = ast.parse(expression, mode="eval")
    return _eval(tree.body)


# This description tells Claude what the tool does and when to use it.
TOOLS = [
    {
        "name": "calculate",
        "description": "Evaluate a math expression (e.g. '12 * (3 + 4)'). "
        "Use this whenever the user asks for a calculation.",
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
    }
]


def main():
    print("AI Bot with memory + calculator (type 'bye' to quit)")
    history = []  # the bot's memory

    while True:
        message = input("You: ")
        if message.lower().strip() in ("bye", "quit", "exit"):
            print("Bot: Goodbye!")
            break

        history.append({"role": "user", "content": message})

        # Keep talking to Claude until it stops asking for tools.
        while True:
            response = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system="You are a helpful assistant. Use the calculator tool for any math.",
                tools=TOOLS,
                messages=history,
            )

            # Save Claude's turn (it may contain a tool request) to memory.
            history.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                # No tool needed — print the text answer and move on.
                for block in response.content:
                    if block.type == "text":
                        print("Bot:", block.text)
                break

            # Claude asked to use a tool. Run each request and send results back.
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    try:
                        answer = calculate(block.input["expression"])
                        result_text = str(answer)
                    except Exception as error:
                        result_text = f"Error: {error}"

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_text,
                    })

            history.append({"role": "user", "content": tool_results})
            # Loop again so Claude can read the result and reply.


if __name__ == "__main__":
    main()
