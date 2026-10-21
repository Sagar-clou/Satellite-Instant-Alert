import os, time, threading
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template, request
import requests

app = Flask(__name__)

# Put your NASA FIRMS MAP_KEY in an environment variable:
# Windows: set FIRMS_MAP_KEY=YOUR_KEY
# Linux/macOS: export FIRMS_MAP_KEY=YOUR_KEY
FIRMS_MAP_KEY = os.getenv("FIRMS_MAP_KEY", "")
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "60"))

# South Asia monitoring box: west,south,east,north
BBOX = os.getenv("FIRMS_BBOX", "60,5,100,40")
SENSOR = os.getenv("FIRMS_SENSOR", "VIIRS_NOAA21_NRT")

state = {
    "mode": "SATELLITE" if FIRMS_MAP_KEY else "DEMO",
    "last_update": None,
    "alerts": [],
    "fires": [],
    "error": None,
}

def fetch_firms():
    if not FIRMS_MAP_KEY:
        return [], "No FIRMS_MAP_KEY configured; running in DEMO mode."

    url = (
        f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
        f"{FIRMS_MAP_KEY}/{SENSOR}/{BBOX}/1"
    )
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    lines = r.text.strip().splitlines()
    if len(lines) <= 1:
        return [], None

    headers = lines[0].split(",")
    rows = []
    for line in lines[1:]:
        vals = line.split(",")
        if len(vals) != len(headers):
            continue
        d = dict(zip(headers, vals))
        try:
            rows.append({
                "latitude": float(d["latitude"]),
                "longitude": float(d["longitude"]),
                "confidence": d.get("confidence", ""),
                "frp": float(d.get("frp") or 0),
                "acq_date": d.get("acq_date", ""),
                "acq_time": d.get("acq_time", ""),
                "satellite": d.get("satellite", SENSOR),
                "daynight": d.get("daynight", "")
            })
        except (ValueError, KeyError):
            pass
    return rows, None

def make_alerts(fires):
    alerts = []
    # Demo/engineering threshold. Production thresholds must be calibrated.
    for f in fires:
        if f["frp"] >= 50:
            level = "CRITICAL"
        elif f["frp"] >= 20:
            level = "HIGH"
        else:
            level = "WATCH"
        alerts.append({
            "id": f'{f["latitude"]:.4f}_{f["longitude"]:.4f}_{f["acq_date"]}_{f["acq_time"]}',
            "hazard": "Satellite-detected active fire",
            "level": level,
            "lat": f["latitude"],
            "lon": f["longitude"],
            "frp": f["frp"],
            "satellite": f["satellite"],
            "time": f["acq_date"] + " " + f["acq_time"],
            "message": "Move away from the detected hotspot and follow official emergency instructions."
        })
    # strongest first
    order = {"CRITICAL": 0, "HIGH": 1, "WATCH": 2}
    return sorted(alerts, key=lambda x: (order[x["level"]], -x["frp"]))[:50]

def update():
    try:
        fires, err = fetch_firms()
        state["fires"] = fires[:500]
        state["alerts"] = make_alerts(fires)
        state["last_update"] = datetime.now(timezone.utc).isoformat()
        state["error"] = err
    except Exception as e:
        state["error"] = str(e)
        state["last_update"] = datetime.now(timezone.utc).isoformat()

def worker():
    while True:
        update()
        time.sleep(POLL_SECONDS)

@app.get("/")
def index():
    return render_template("index.html", mode=state["mode"])

@app.get("/api/status")
def status():
    return jsonify({
        **state,
        "poll_seconds": POLL_SECONDS,
        "bbox": BBOX,
        "sensor": SENSOR
    })

@app.post("/api/refresh")
def refresh():
    update()
    return jsonify({"ok": True, **state})

if __name__ == "__main__":
    threading.Thread(target=worker, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
