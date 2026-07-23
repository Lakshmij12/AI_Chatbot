# Put your chatbot on WhatsApp

This guide connects your Claude chatbot to WhatsApp using **Twilio's free
WhatsApp Sandbox** — the easiest way to try it without a business account.

## How it works

WhatsApp can't run your Python code directly. A middleman (Twilio) receives
your WhatsApp messages and forwards them to a small web server you run
(`whatsapp_bot.py`), which asks Claude for a reply and sends it back:

```
You (WhatsApp)  ->  Twilio  ->  whatsapp_bot.py  ->  Claude
You (WhatsApp)  <-  Twilio  <---------------------  (reply)
```

## What you'll need

- A free **Twilio** account: https://www.twilio.com/try-twilio
- **ngrok** (free) to expose your local server to the internet: https://ngrok.com/download
- Your **Anthropic API key** (same one you've been using)

## Step 1 — Install and set your key

```
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key-here"     # Windows: setx ANTHROPIC_API_KEY "..."
```

## Step 2 — Start the bot server

```
python whatsapp_bot.py
```
It starts on **http://localhost:5000** and waits for messages. Leave it
running in this terminal.

## Step 3 — Expose it to the internet with ngrok

Twilio needs a public web address to reach your server. In a **second**
terminal, run:

```
ngrok http 5000
```
ngrok prints a public URL like `https://abcd-1234.ngrok-free.app`. Copy it —
you'll add `/whatsapp` to the end in the next step.

## Step 4 — Connect the Twilio WhatsApp Sandbox

1. In the [Twilio Console](https://console.twilio.com/), go to
   **Messaging → Try it out → Send a WhatsApp message**.
2. Follow the on-screen instructions to **join the sandbox**: send the given
   code (e.g. `join <two-words>`) from your phone's WhatsApp to the Twilio
   sandbox number. You'll get a confirmation.
3. On the **Sandbox settings** tab, find **"When a message comes in"** and
   paste your ngrok URL with `/whatsapp` on the end, for example:
   ```
   https://abcd-1234.ngrok-free.app/whatsapp
   ```
   Set the method to **POST** and **Save**.

## Step 5 — Chat!

Send a WhatsApp message to the Twilio sandbox number. Your bot replies —
powered by Claude, with memory per phone number.

## Common problems

- **No reply at all** → check that (a) `python whatsapp_bot.py` is still
  running, (b) `ngrok` is still running, and (c) the Twilio webhook URL ends
  in `/whatsapp` and is set to **POST**.
- **ngrok URL changed** → the free ngrok URL changes each time you restart
  ngrok. If you restart it, update the webhook URL in Twilio again.
- **`No module named flask` / `twilio`** → run `pip install -r requirements.txt`.
- **AuthenticationError** → `ANTHROPIC_API_KEY` isn't set in the terminal
  running `whatsapp_bot.py`.
- **Memory resets** → the bot stores conversations in memory, so restarting
  the server clears them. That's fine for learning; a real app would use a
  database.

## Notes

- The **sandbox** is for testing. To message any WhatsApp number from your own
  branded number, you'd apply for the Twilio WhatsApp Business API (more setup,
  and Meta approval).
- Keep your Twilio and Anthropic keys private — never commit them to GitHub.
