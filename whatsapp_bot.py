"""
Put your chatbot on WhatsApp (using Twilio)

WhatsApp can't run your Python directly. Instead:

    You (WhatsApp)  ->  Twilio  ->  THIS web server  ->  Claude
                                         |
    You (WhatsApp)  <-  Twilio  <--------+  (the reply)

Twilio receives your WhatsApp message and forwards it to this little web
server. We ask Claude for a reply and send it back. Each phone number gets
its own memory so conversations stay separate.

This uses Twilio's free WhatsApp **Sandbox**, which is the easiest way to
try it. See WHATSAPP.md for the full step-by-step setup.

Quick setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY="your-key-here"
    python whatsapp_bot.py        # starts the server on port 5000

Then use ngrok to expose it and point your Twilio sandbox at it
(all explained in WHATSAPP.md).
"""

import anthropic
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

client = anthropic.Anthropic()
MODEL = "claude-opus-4-8"

app = Flask(__name__)

# Memory for every user, keyed by their phone number.
# Note: this lives in memory, so it resets when you restart the server.
conversations = {}


def get_reply(sender, message):
    """Get Claude's reply for one user, remembering their conversation."""
    history = conversations.setdefault(sender, [])
    history.append({"role": "user", "content": message})

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system="You are a friendly, helpful assistant replying on WhatsApp. "
        "Keep replies fairly short and easy to read on a phone.",
        messages=history,
    )

    reply = ""
    for block in response.content:
        if block.type == "text":
            reply = block.text

    history.append({"role": "assistant", "content": reply})
    return reply


@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    """Twilio sends incoming WhatsApp messages here as a POST request."""
    sender = request.form.get("From", "")       # e.g. 'whatsapp:+15551234567'
    message = request.form.get("Body", "")       # the text the user sent

    reply = get_reply(sender, message)

    # Twilio expects a TwiML response; it delivers <Message> back to WhatsApp.
    twiml = MessagingResponse()
    twiml.message(reply)
    return str(twiml)


if __name__ == "__main__":
    # host="0.0.0.0" so ngrok/Twilio can reach it; port 5000 by default.
    app.run(host="0.0.0.0", port=5000)
