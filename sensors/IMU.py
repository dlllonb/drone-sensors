#!/usr/bin/env python3
import sys, os, json, time, signal

RUN = True

def _stop(*_):
    global RUN; RUN = False;
signal.signal(signal.SIGINT, _stop)
signal.signal(signal.SIGTERM, _stop)

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB1"

VENDOR_DIR = os.path.join(os.path.dirname(__file__), "yei_threesapce")
sys.path.insert(0, VENDOR_DIR)
import threespace_api as ts

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

def emit(obj): 
    print(json.dumps(obj), flush=True)

emit({"type":"imu_status", "event":"open", "port": PORT, "time":time.time())
dev = ts.TSUSBSensor(com_port=PORT)

try:
    while RUN:
        q = dev.getTaredOrientationAsQuaternion()  # (w,x,y,z)
        ax, ay, az = dev.getCorrectedAccelerometerVector()
        emit({"type":"imu","ts":time.time(),"quat":q,"accel_mps2":[ax,ay,az]})
        time.sleep(0.02)  # ~50 Hz; adjust as needed
finally:
    dev.close()
    emit({"type":"imu_status","event":"close","ts":time.time()})
