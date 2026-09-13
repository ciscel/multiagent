"""
Simulated sensing layer + connectivity state.
In real hardware this reads link lights, DHCP lease, DNS resolution, and a
cellular/mesh heartbeat. For the demo, state is just a small JSON file the
admin panel flips, so judges can see the SAME code path react to different
real-world scenarios live.
"""
import json
import os
import time

STATE_PATH = os.path.join(os.path.dirname(__file__), "sim_state.json")

DEFAULT_STATE = {
    "wan_link": "up",                  # "up" | "down" -- this box's own broadband
    "ap_functional": True,             # is the box's own local radio/hardware responding at all
    "dns_ok": True,
    "dhcp_ok": True,
    "neighbor_relay_available": False, # is a nearby appliance reachable to relay our status out?
    "unauthorized_device": False,      # security sensing: unrecognized device / anomalous traffic
    "attack_technique": None,          # e.g. "T1071.001 - Web Protocols (C2 beaconing pattern)"
}


def load_state():
    if not os.path.exists(STATE_PATH):
        save_state(DEFAULT_STATE)
    with open(STATE_PATH) as f:
        return json.load(f)


def save_state(state: dict):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def set_scenario(name: str):
    scenarios = {
        "nominal": {"wan_link": "up", "ap_functional": True, "dns_ok": True,
                    "dhcp_ok": True, "neighbor_relay_available": False},
        "carrier_outage": {"wan_link": "down", "ap_functional": True, "dns_ok": False,
                            "dhcp_ok": True, "neighbor_relay_available": False},
        "local_glitch": {"wan_link": "up", "ap_functional": True, "dns_ok": False,
                          "dhcp_ok": True, "neighbor_relay_available": False},
        "hardware_fault": {"wan_link": "down", "ap_functional": False, "dns_ok": False,
                            "dhcp_ok": False, "neighbor_relay_available": False},
        "neighbor_relay_available": {"wan_link": "down", "ap_functional": True, "dns_ok": False,
                                      "dhcp_ok": True, "neighbor_relay_available": True},
        "security_anomaly": {"wan_link": "up", "ap_functional": True, "dns_ok": True,
                              "dhcp_ok": True, "neighbor_relay_available": False,
                              "unauthorized_device": True,
                              "attack_technique": "T1071.001 - Web Protocols (C2 beaconing pattern)"},
    }
    # scenarios only specify the keys that matter for that story; fill the rest from defaults
    base = dict(DEFAULT_STATE)
    base.update(scenarios.get(name, {}))
    scenarios[name] = base
    state = scenarios.get(name, DEFAULT_STATE)
    save_state(state)
    return state
