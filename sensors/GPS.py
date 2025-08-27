#!/usr/bin/env python3
import sys, json, time, signal
import serial, pynmea2, datetime

RUN = True
def _stop(*_): 
    global RUN; RUN = False
signal.signal(signal.SIGINT, _stop)
signal.signal(signal.SIGTERM, _stop)

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
BAUD = int(sys.argv[2]) if len(sys.argv) > 2 else 9600

# line-buffer stdout so parent sees lines immediately
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

def emit(obj):
    print(json.dumps(obj), flush=True)

ser = serial.Serial(PORT, BAUD, timeout=1)
emit({"type":"gps_status","event":"open","port":PORT,"baud":BAUD,"ts":time.time()})

try:
    while RUN:
        line = ser.readline().decode("ascii", errors="replace").strip()
        if not line or not line.startswith("$"):
            continue
        try:
            msg = pynmea2.parse(line)
        except pynmea2.nmea.ParseError:
            continue

        now = time.time()  # POSIX seconds (UTC)
        if msg.sentence_type == "RMC" and getattr(msg, "status", "") == "A":
            emit({
                "type":"gps_rmc","ts":now,
                "lat": msg.latitude, "lon": msg.longitude,
                "speed_mps": (float(msg.spd_over_grnd or 0.0)*0.514444),
                "date": getattr(msg, "datestamp", None).isoformat() if getattr(msg,"datestamp",None) else None,
                "time": getattr(msg, "timestamp", None).isoformat() if getattr(msg,"timestamp",None) else None,
                "raw": line
            })
        elif msg.sentence_type == "GGA":
            emit({
                "type":"gps_gga","ts":now,
                "fix": int(getattr(msg, "gps_qual", 0) or 0),
                "sats": int(getattr(msg, "num_sats", 0) or 0),
                "alt_m": float(msg.altitude) if msg.altitude not in (None, "") else float("nan"),
                "raw": line
            })
finally:
    ser.close()
    emit({"type":"gps_status","event":"close","ts":time.time()})
