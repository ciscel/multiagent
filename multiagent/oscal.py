"""
Lightweight OSCAL-style evidence export.
Not a full OSCAL Assessment Results document -- a demo-scale fragment that
shows the shape: every event becomes a structured, cited "observation" a
downstream system (or an insurer/auditor) could consume programmatically.
"""
import datetime


def _iso(ts: float) -> str:
    return datetime.datetime.utcfromtimestamp(ts).isoformat() + "Z"


def event_to_observation(event: dict) -> dict:
    return {
        "observation-uuid": f"event-{event['id']}",
        "title": event["rule_id"],
        "description": event["verdict"],
        "collected": _iso(event["ts"]),
        "methods": ["AUTOMATED"],
        "subjects": [
            {"type": "inventory-item", "title": "appliance-01"}
        ],
        "props": [
            {"name": "rule-citation", "value": event["citation"]},
            {"name": "category", "value": event.get("category", "connectivity")},
            {"name": "action-taken", "value": event["action_taken"]},
            {"name": "truck-roll-required", "value": str(bool(event.get("truck_roll")))},
        ],
    }


def build_evidence_bundle(events: list) -> dict:
    return {
        "assessment-results": {
            "uuid": "offline-agent-demo-run",
            "metadata": {
                "title": "Offline Agent -- Local Evidence Export",
                "last-modified": datetime.datetime.utcnow().isoformat() + "Z",
            },
            "results": [
                {
                    "uuid": "local-run-1",
                    "title": "Local sense/decide/act loop -- events since last sync",
                    "observations": [event_to_observation(e) for e in events],
                }
            ],
        }
    }
