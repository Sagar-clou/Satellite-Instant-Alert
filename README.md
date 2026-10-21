# SAFE-NET Satellite Instant Alert Prototype

This is a working prototype of the SAFE-NET architecture.

## What is live

The prototype can ingest NASA FIRMS near-real-time active-fire satellite products and turn detections into:
- live map markers
- risk levels
- browser notifications
- alert history in the dashboard

NASA FIRMS provides MODIS/VIIRS active-fire products globally in near real time. Exact latency depends on the product and region.

## Run

1. Install Python 3.10+.
2. Create a virtual environment (optional).
3. Install:
   pip install -r requirements.txt

4. Get a NASA FIRMS MAP_KEY from the FIRMS service.
5. Set it:

Windows:
   set FIRMS_MAP_KEY=YOUR_KEY

Linux/macOS:
   export FIRMS_MAP_KEY=YOUR_KEY

6. Start:
   python app.py

7. Open:
   http://localhost:5000

If no MAP_KEY is provided, the application starts in DEMO mode.

## Important engineering note

Satellite observations are not guaranteed to be instantaneous. This prototype therefore labels the data as near-real-time and displays the last successful update. A production emergency system must combine satellite observations with ground sensors and official emergency authorities.

## Patent-oriented architecture

Satellite data -> data fusion -> hazard detection -> risk scoring -> propagation/geofence -> differentiated alert -> emergency response.

The current connector is active-fire detection. Flood, landslide, cyclone and earthquake modules should use validated/authorized feeds and domain-specific models before any real-world emergency deployment.
