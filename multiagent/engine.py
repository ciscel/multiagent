"""
Deterministic rule engine (ORF-style).
Given a sensed state dict, returns the FIRST matching rule as the verdict,
with its citation. No LLM in this path -- this is the auditable core.
"""
import json
import os

RULES_PATH = os.path.join(os.path.dirname(__file__), "rules.json")


def load_rules():
    with open(RULES_PATH) as f:
        return json.load(f)


def evaluate(state: dict) -> dict:
    """
    state keys expected:
      heartbeat_alive: bool   -- appliance's own local health check passed
      wan_link: "up" | "down"
      dns_ok: bool
      dhcp_ok: bool
      last_resort: bool       -- true only when no local AP/customer phone joined either
    """
    derived = dict(state)
    derived["dns_or_dhcp_broken"] = not (state.get("dns_ok", True) and state.get("dhcp_ok", True))

    rules = load_rules()
    for rule in rules:
        cond = rule["condition"]
        match = True
        for k, v in cond.items():
            if derived.get(k) != v:
                match = False
                break
        if match:
            fmt_ctx = {**derived, "attack_technique": derived.get("attack_technique") or "unknown technique"}

            def safe_format(s):
                try:
                    return s.format(**fmt_ctx)
                except (KeyError, IndexError):
                    return s

            return {
                "rule_id": rule["id"],
                "name": rule["name"],
                "category": rule.get("category", "connectivity"),
                "citation": safe_format(rule["citation"]),
                "verdict": safe_format(rule["verdict"]),
                "customer_message": safe_format(rule["customer_message"]),
                "auto_fix": rule["auto_fix"],
                "truck_roll": rule["truck_roll"],
            }

    # Should not happen if rules.json covers the space -- fail safe, not silent
    return {
        "rule_id": "R0",
        "name": "Unclassified",
        "category": "unclassified",
        "citation": "R0: no rule matched",
        "verdict": "State did not match any known pattern -- flagged for human review.",
        "customer_message": "We're looking into this and will follow up shortly.",
        "auto_fix": False,
        "truck_roll": True,
    }
