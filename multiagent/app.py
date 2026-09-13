import threading
import time

from flask import Flask, render_template, jsonify, request, redirect, url_for

import engine
import store
import sensor
import sync_adapters
import oscal

app = Flask(__name__)
store.init_db()

SENSE_INTERVAL_SECONDS = 4
_stop_flag = False


def sense_loop():
    """Runs continuously, whether or not the box has connectivity.
    This is the point: sensing/deciding/logging never stops."""
    while not _stop_flag:
        state = sensor.load_state()
        result = engine.evaluate(state)
        action = "auto-remediated" if result["auto_fix"] else "logged only"
        store.log_event(state, result, action)
        time.sleep(SENSE_INTERVAL_SECONDS)


@app.route("/")
def captive_portal():
    """What a customer's phone sees when it joins the appliance's local AP.
    No internet required to render this -- it's served from the box itself."""
    state = sensor.load_state()
    result = engine.evaluate(state)
    return render_template("portal.html", state=state, result=result)


@app.route("/admin")
def admin():
    state = sensor.load_state()
    result = engine.evaluate(state)
    events = store.get_recent(15)
    depth = store.queue_depth()
    return render_template("admin.html", state=state, result=result, events=events, depth=depth)


@app.route("/admin/scenario/<name>", methods=["POST"])
def set_scenario(name):
    sensor.set_scenario(name)
    # log immediately so the demo doesn't wait for the next tick
    state = sensor.load_state()
    result = engine.evaluate(state)
    action = "auto-remediated" if result["auto_fix"] else "logged only"
    store.log_event(state, result, action)
    return redirect(url_for("admin"))


@app.route("/admin/sync", methods=["POST"])
def sync_now():
    """Simulates connectivity returning: flush the local queue out to the
    three external apps. If neighbor_wan_up is set, this represents a
    mesh-relayed sync instead of the box's own WAN recovering."""
    state = sensor.load_state()
    via = "mesh_relay" if state.get("neighbor_wan_up") else "direct_wan"
    unsynced = store.get_unsynced()
    synced_ids = []
    for ev in unsynced:
        succeeded = sync_adapters.flush_event(ev)
        if succeeded:
            synced_ids.append(ev["id"])
    store.mark_synced(synced_ids, via)
    return redirect(url_for("admin"))


@app.route("/admin/reset", methods=["POST"])
def reset_demo():
    import os
    if os.path.exists(store.DB_PATH):
        os.remove(store.DB_PATH)
    store.init_db()
    sensor.set_scenario("nominal")
    return redirect(url_for("admin"))


@app.route("/admin/evidence")
def evidence_export():
    """OSCAL-style evidence export -- what a compliance buyer/insurer would
    actually consume. Includes every event, synced or not, so it doubles
    as the audit trail even while offline."""
    events = store.get_recent(100)
    bundle = oscal.build_evidence_bundle(events)
    return jsonify(bundle)


@app.route("/api/state")
def api_state():
    state = sensor.load_state()
    result = engine.evaluate(state)
    return jsonify({"state": state, "result": result, "queue_depth": store.queue_depth()})


if __name__ == "__main__":
    t = threading.Thread(target=sense_loop, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000, debug=False)
