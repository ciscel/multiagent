# Offline Agent — "No Internet" Appliance/SaaS

**This is not three devices. It's one.**
Support agent. Security system. Compliance tool.

38% of every ISP support call starts with "no internet." Today's fix is a
guess made blind over the phone. This box gives you a diagnosis instead of
a guess — and it never stops working, connected or not.

## How it works

- **Sense** — reads local signals (WAN link, DNS, DHCP, its own AP health, a
  nearby appliance's relay availability). Simulated here via `sensor.py` /
  the admin panel; on real hardware this is Nmap/SNMP/link-state checks.
- **Decide** — `engine.py` is a deterministic rule table (`rules.json`), not
  an LLM. Every verdict comes with a citation to the exact rule that fired.
  This is the ORF pattern: auditable, not probabilistic.
- **Explain, locally, with zero internet** — `templates/portal.html` is
  served directly from the box. A customer's phone joins the appliance's own
  WiFi hotspot (captive portal, same mechanism as hotel/airport WiFi) and
  sees the diagnosis immediately. No call needed.
- **Act** — auto-remediates the safe cases (DNS/DHCP glitches), logs and
  flags the rest.
- **Remember** — `store.py` is a local SQLite event log. It keeps writing
  events indefinitely with no connection at all.
- **Sync (opportunistic)** — `sync_adapters.py` flushes the queue to three
  external apps only when connectivity exists — either the box's own WAN, or
  relayed through a neighboring appliance over local WiFi/Bluetooth mesh
  (simulated here via the "Neighbor Relay Available" scenario).

## Three verdict categories, one engine, one evidence trail

The same sensing/decide/act/log loop now produces two kinds of verdicts:

- **Connectivity** (R1-R5) — the "no internet" story: outage, auto-fixed
  glitch, or genuine hardware fault.
- **Security** (R6) — an unrecognized device or anomalous outbound traffic
  is detected and isolated automatically, tagged with an ATT&CK technique
  ID. Same rule engine, same citation pattern, different question.

Every event, regardless of category, lands in the same local store and the
same OSCAL-style evidence export (`GET /admin/evidence`) — a compliance
buyer or their insurer gets one audit trail covering both "was this site
online" and "was anything anomalous on the network," not two separate
products bolted together.

## The three external apps (hackathon requirement)

1. **Slack** — every event posts an alert (`SLACK_WEBHOOK_URL`)
2. **Trello** — a card is created *only* for truck-roll-worthy events (R3).
   This is deliberate: the demo should visibly create **fewer** tickets, not
   more. (`TRELLO_API_KEY`, `TRELLO_TOKEN`, `TRELLO_LIST_ID`)
3. **Generic webhook** (Sheets via Apps Script, Notion via Zapier, etc.) —
   every event exports as a structured evidence-log entry
   (`GENERIC_WEBHOOK_URL`)

All three degrade gracefully: with no env vars set, they print what they
*would* send to `server.log`, so the full pipeline is demoable right now.
Drop in real webhook URLs before the demo to make it live — takes minutes,
no code changes needed.

## Setup

```bash
pip install flask requests
# optional, for live app integrations:
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
export TRELLO_API_KEY="..."
export TRELLO_TOKEN="..."
export TRELLO_LIST_ID="..."
export GENERIC_WEBHOOK_URL="https://script.google.com/macros/s/.../exec"

python3 app.py
```

- Customer-facing portal: `http://localhost:5000/`
- Demo control panel: `http://localhost:5000/admin`

On real hardware, `/` is what a phone sees after joining the box's own WiFi
AP — no router or internet involved. For the hackathon demo, just open it in
a second browser tab or on your phone over the same laptop WiFi.

## Demo script (~2 minutes)

**Intro (~30 sec, spoken over the three error screens):**

> *[show Blue Screen of Death]*
> Remember this? Windows had a memory error so common it became a meme
> before memes existed. Then memory protection shipped, and the Blue
> Screen basically disappeared. Not a prettier error. A retired one.
>
> *[show Chrome's offline dinosaur]*
> You've seen this one this week. "No internet connection." Something
> broke, here's a dinosaur instead of a fix.
>
> *[show Twitter's Fail Whale]*
> Every platform gets its error screen eventually. It's a rite of
> passage. But notice — none of these three tell you what to do. They
> tell you something broke. That's it. A dead end dressed up as
> information.
>
> If something is truly agentic — truly disruptive — it doesn't just
> display the error better. It retires it. Today, we're retiring one of
> the biggest ones: 404. "No internet."
>
> This isn't three products. It's one box. An L1 tech-support agent, a
> network security system, and a compliance tool — same engine, zero
> internet required to run.

**Then the click-through:**

1. Open `/admin` in one window, `/` in another (or on your phone).
2. Click **Nominal** — show `/` says "connection looks healthy."
3. Click **Carrier Outage** — `/` updates instantly: "we can already see
   this outage, no action needed, no truck roll." Point out this happened
   with zero internet anywhere in the room.
4. Click **Local Glitch** — show it auto-fixes and tells the customer,
   instead of walking them through a manual reset.
5. Click **Hardware Fault** — this is the one case that *does* need a
   truck roll. Point out the Trello card only fires for this one.
6. Let the queue counter tick up for a few seconds on **Hardware Fault** —
   this proves the sense→decide→log loop never stops, connectivity or not.
7. Click **Neighbor Relay Available** — same outage, but now a second
   appliance nearby is reachable. Explain: the box didn't need its own WAN
   or a cellular plan to get the word out.
8. Click **Security Anomaly** — different category, same engine: an
   unrecognized device gets isolated automatically and tagged with the
   ATT&CK technique it matched.
9. Click **View OSCAL Evidence Export** — show that the security event and
   the connectivity events are sitting in the same structured, cited
   evidence stream. Say it plain: **support agent, security system,
   compliance tool — one box.**
10. Click **Sync Now** — watch the queue flush to Slack/Trello/evidence log
    (or check `server.log` if running without real webhook URLs configured).
11. Close: **"If something is truly agentic, truly disruptive, it has to
    retire an error code. Today, we say goodbye to 404."**

## What's simulated vs. real for a hackathon day

- **Real, working code:** the rule engine, the local event store, the
  Flask-served captive portal, the sync fan-out to three apps.
- **Simulated for the demo:** the actual network sensors (real version =
  Nmap/SNMP/DHCP lease checks) and the neighbor mesh relay (real version =
  WiFi Direct/Bluetooth peer discovery between two physical boxes). Both are
  swappable behind the same `sensor.py` interface without touching
  `engine.py`, `store.py`, or `sync_adapters.py` — the architecture is real
  even where the inputs are mocked for the day.
