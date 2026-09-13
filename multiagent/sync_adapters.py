"""
Sync adapters -- fire only when connectivity exists (or is simulated).
Each function returns True on success. If no credential/env var is set,
it logs what WOULD have been sent and returns True anyway, so the demo
flow (queue -> flush) is visible even before real keys are wired in.

To go live before the hackathon: set these env vars --
  SLACK_WEBHOOK_URL
  TRELLO_API_KEY, TRELLO_TOKEN, TRELLO_LIST_ID
  GENERIC_WEBHOOK_URL   (Google Sheets via Apps Script, Notion via Zapier, etc.)
"""
import os
import requests

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
TRELLO_API_KEY = os.environ.get("TRELLO_API_KEY")
TRELLO_TOKEN = os.environ.get("TRELLO_TOKEN")
TRELLO_LIST_ID = os.environ.get("TRELLO_LIST_ID")
GENERIC_WEBHOOK_URL = os.environ.get("GENERIC_WEBHOOK_URL")


def send_slack(event: dict) -> bool:
    text = (f"[{event['rule_id']}] {event['verdict']}\n"
            f"Citation: {event['citation']}\n"
            f"Action: {event['action_taken']}")
    if not SLACK_WEBHOOK_URL:
        print(f"[SLACK - not configured, would send]\n{text}\n")
        return True
    try:
        r = requests.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=5)
        return r.status_code < 300
    except Exception as e:
        print(f"[SLACK ERROR] {e}")
        return False


def send_trello_card(event: dict) -> bool:
    # Only fires a real card for truck-roll events -- that's the point:
    # fewer tickets, not more.
    if not event.get("truck_roll"):
        return True
    name = f"Truck roll: {event['rule_id']} @ event {event['id']}"
    desc = f"{event['verdict']}\nCitation: {event['citation']}"
    if not (TRELLO_API_KEY and TRELLO_TOKEN and TRELLO_LIST_ID):
        print(f"[TRELLO - not configured, would create card]\n{name}\n{desc}\n")
        return True
    try:
        r = requests.post(
            "https://api.trello.com/1/cards",
            params={
                "key": TRELLO_API_KEY, "token": TRELLO_TOKEN,
                "idList": TRELLO_LIST_ID, "name": name, "desc": desc,
            }, timeout=5
        )
        return r.status_code < 300
    except Exception as e:
        print(f"[TRELLO ERROR] {e}")
        return False


def send_generic_webhook(event: dict) -> bool:
    # Evidence-log style export -- stands in for Sheets/Notion/Drive.
    payload = {
        "ts": event["ts"], "rule_id": event["rule_id"], "verdict": event["verdict"],
        "citation": event["citation"], "action_taken": event["action_taken"],
    }
    if not GENERIC_WEBHOOK_URL:
        print(f"[EVIDENCE LOG - not configured, would export]\n{payload}\n")
        return True
    try:
        r = requests.post(GENERIC_WEBHOOK_URL, json=payload, timeout=5)
        return r.status_code < 300
    except Exception as e:
        print(f"[WEBHOOK ERROR] {e}")
        return False


def flush_event(event: dict) -> list:
    """Fan the event out to all three apps. Returns list of app names that succeeded."""
    succeeded = []
    if send_slack(event):
        succeeded.append("slack")
    if send_trello_card(event):
        succeeded.append("trello")
    if send_generic_webhook(event):
        succeeded.append("evidence_log")
    return succeeded
