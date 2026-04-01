"""
YoungOnes Copy Bot — Slack Bolt app.

Trigger: tag @YoungOnesCopy in een Slack-kanaal of DM.
De bot stelt clarificerende vragen in de thread en genereert een copy-pakket.

Gebruik Socket Mode (geen publiek endpoint nodig).
"""

import os
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import copywriter

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = App(token=os.environ["SLACK_BOT_TOKEN"])

# Conversatiestatus per Slack-thread: { thread_ts: session_dict }
sessions: dict = {}


def get_or_create_session(thread_ts: str) -> dict:
    if thread_ts not in sessions:
        sessions[thread_ts] = copywriter.create_session()
    return sessions[thread_ts]


def post_thinking(client, channel: str, thread_ts: str) -> str:
    """Stuur een tijdelijk 'bezig...' bericht en geef de message_ts terug."""
    result = client.chat_postMessage(
        channel=channel,
        thread_ts=thread_ts,
        text="_Even nadenken..._",
    )
    return result["ts"]


def update_or_post(client, channel: str, thread_ts: str, thinking_ts: str | None, text: str):
    """Vervang het 'bezig...'-bericht of post een nieuw bericht."""
    if thinking_ts:
        try:
            client.chat_update(
                channel=channel,
                ts=thinking_ts,
                text=text,
            )
            return
        except Exception:
            pass  # Fallback: post nieuw bericht
    client.chat_postMessage(
        channel=channel,
        thread_ts=thread_ts,
        text=text,
    )


@app.event("app_mention")
def handle_mention(event, client, say):
    """
    Wordt aangeroepen als iemand @YoungOnesCopy taagt.
    Start of verlengt een briefing-sessie in de thread.
    """
    channel = event["channel"]
    # Gebruik de thread_ts als sessie-sleutel (of de event ts als het de eerste mention is)
    thread_ts = event.get("thread_ts") or event["ts"]
    user = event["user"]
    text = event.get("text", "")

    # Verwijder de bot-mention uit de tekst
    # Slack stuurt <@BOTID> in de tekst — strip dat eruit
    import re
    clean_text = re.sub(r"<@[A-Z0-9]+>", "", text).strip()

    if not clean_text:
        say(
            text="Hey! Wat wil je schrijven? Geef me een briefing — of gewoon een eerste idee.",
            thread_ts=thread_ts,
        )
        return

    session = get_or_create_session(thread_ts)

    # Toon 'bezig...'-indicator
    thinking_ts = post_thinking(client, channel, thread_ts)

    try:
        if not session["messages"]:
            # Eerste bericht in deze thread — start de briefing
            response = copywriter.start_briefing(session, clean_text)
        else:
            # Vervolgbericht — stuur het door als antwoord op een vraag
            response = copywriter.chat(session, clean_text)

        update_or_post(client, channel, thread_ts, thinking_ts, response)

    except Exception as e:
        logger.error(f"Fout bij genereren copy: {e}", exc_info=True)
        update_or_post(
            client,
            channel,
            thread_ts,
            thinking_ts,
            "Er ging iets mis. Probeer het opnieuw of ping Lennart.",
        )


@app.event("message")
def handle_thread_reply(event, client):
    """
    Verwerkt antwoorden in threads waar de bot al actief is.
    Wordt alleen opgeroepen als het een thread-reply is (thread_ts aanwezig)
    en de bot niet direct getagd is (die worden door handle_mention opgepakt).
    """
    # Negeer berichten van bots (inclusief onszelf)
    if event.get("bot_id") or event.get("subtype"):
        return

    thread_ts = event.get("thread_ts")
    if not thread_ts:
        return  # Geen thread-bericht, skip

    # Alleen reageren als we al een actieve sessie hebben voor deze thread
    if thread_ts not in sessions:
        return

    channel = event["channel"]
    text = event.get("text", "").strip()

    if not text:
        return

    session = sessions[thread_ts]
    thinking_ts = post_thinking(client, channel, thread_ts)

    try:
        response = copywriter.chat(session, text)
        update_or_post(client, channel, thread_ts, thinking_ts, response)
    except Exception as e:
        logger.error(f"Fout bij verwerken thread-reply: {e}", exc_info=True)
        update_or_post(
            client,
            channel,
            thread_ts,
            thinking_ts,
            "Er ging iets mis. Probeer het opnieuw.",
        )


if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    logger.info("YoungOnes Copy Bot gestart. Wachten op mentions...")
    handler.start()
