"""
AquaSentry — Water Tank Level Indicator & Alarm System
--------------------------------------------------------
Flask backend.

Responsible for:
  1. Reading the water level (real sensor OR simulator — see WaterLevelSensor
     below) on a background thread.
  2. Evaluating the reading against LOW / HIGH thresholds to decide the
     alarm state.
  3. Exposing a small JSON REST API that the web UI polls.

Run with:  python app.py
Then open: http://127.0.0.1:5000
"""

import json
import random
import threading
import time
from collections import deque
from datetime import datetime

from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

# ----------------------------------------------------------------------
# Tank / sensor configuration
# ----------------------------------------------------------------------
TANK_HEIGHT_CM = 150        # physical height of the tank
SENSOR_OFFSET_CM = 5        # gap between sensor mount and max water level
UPDATE_INTERVAL_SEC = 1.5   # how often the sensor is polled

state_lock = threading.Lock()

state = {
    "level_percent": 55.0,
    "level_cm": 0.0,
    "distance_cm": 0.0,
    "volume_liters": 0.0,
    "tank_capacity_liters": 1000.0,
    "status": "NORMAL",          # NORMAL | LOW_ALARM | HIGH_ALARM
    "trend": "IDLE",             # FILLING | DRAINING | IDLE
    "mode": "AUTO",              # AUTO | FILL | DRAIN | HOLD
    "low_threshold": 20.0,
    "high_threshold": 90.0,
    "last_updated": None,
}

alarm_log = deque(maxlen=25)   # rolling event log shown in the UI


# ----------------------------------------------------------------------
# Sensor abstraction
# ----------------------------------------------------------------------
class WaterLevelSensor:
    """
    Simulated ultrasonic water level sensor.

    In a real deployment (e.g. Raspberry Pi + HC-SR04 ultrasonic sensor
    mounted at the top of the tank) you would replace `read_distance_cm()`
    with actual GPIO timing code. Everything downstream (percent, volume,
    alarm logic) stays identical, since it all works off the distance
    reading. A ready-to-use hardware version is provided at the bottom of
    this file, commented out.
    """

    def __init__(self, tank_height_cm):
        self.tank_height_cm = tank_height_cm
        self._sim_level = 55.0      # starting percent for the simulator
        self._sim_direction = 1     # 1 = filling, -1 = draining

    def read_distance_cm(self):
        """Return the simulated distance from the sensor to the water surface."""
        with state_lock:
            mode = state["mode"]

        if mode == "FILL":
            self._sim_direction = 1
        elif mode == "DRAIN":
            self._sim_direction = -1
        elif mode == "HOLD":
            self._sim_direction = 0
        else:  # AUTO — bounce between empty and full like a real usage cycle
            if self._sim_level >= 97:
                self._sim_direction = -1
            elif self._sim_level <= 5:
                self._sim_direction = 1

        step = random.uniform(0.4, 1.3) * self._sim_direction
        noise = random.uniform(-0.15, 0.15)
        self._sim_level = max(0.0, min(100.0, self._sim_level + step + noise))

        # Convert simulated percent -> a physical distance reading, exactly
        # like a real ultrasonic sensor would report (closer = fuller tank).
        water_height_cm = (self._sim_level / 100.0) * (self.tank_height_cm - SENSOR_OFFSET_CM)
        distance_cm = self.tank_height_cm - water_height_cm
        return round(distance_cm, 2)


sensor = WaterLevelSensor(TANK_HEIGHT_CM)


# ----------------------------------------------------------------------
# Reading -> state conversion + alarm evaluation
# ----------------------------------------------------------------------
def update_reading():
    distance_cm = sensor.read_distance_cm()
    water_height_cm = max(0.0, (TANK_HEIGHT_CM - SENSOR_OFFSET_CM) - distance_cm)
    level_percent = round((water_height_cm / (TANK_HEIGHT_CM - SENSOR_OFFSET_CM)) * 100, 1)
    level_percent = max(0.0, min(100.0, level_percent))

    with state_lock:
        previous_percent = state["level_percent"]
        previous_status = state["status"]

        volume = round((level_percent / 100.0) * state["tank_capacity_liters"], 1)

        if level_percent - previous_percent > 0.05:
            trend = "FILLING"
        elif previous_percent - level_percent > 0.05:
            trend = "DRAINING"
        else:
            trend = "IDLE"

        if level_percent <= state["low_threshold"]:
            status = "LOW_ALARM"
        elif level_percent >= state["high_threshold"]:
            status = "HIGH_ALARM"
        else:
            status = "NORMAL"

        state.update({
            "level_percent": level_percent,
            "level_cm": round(water_height_cm, 1),
            "distance_cm": distance_cm,
            "volume_liters": volume,
            "status": status,
            "trend": trend,
            "last_updated": datetime.now().strftime("%H:%M:%S"),
        })

        if status != previous_status:
            alarm_log.appendleft({
                "time": state["last_updated"],
                "message": f"Status changed to {status.replace('_', ' ')} at {level_percent}%",
                "level": status,
            })

        snapshot = dict(state)

    return snapshot


def sensor_loop():
    while True:
        try:
            update_reading()
        except Exception as exc:  # keep the background thread alive
            print(f"[sensor_loop] error: {exc}")
        time.sleep(UPDATE_INTERVAL_SEC)


# ----------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    with state_lock:
        snapshot = dict(state)
        log_snapshot = list(alarm_log)
    snapshot["tank_height_cm"] = TANK_HEIGHT_CM
    snapshot["alarm_log"] = log_snapshot
    return jsonify(snapshot)


@app.route("/api/thresholds", methods=["POST"])
def api_thresholds():
    data = request.get_json(force=True, silent=True) or {}
    with state_lock:
        if "low" in data:
            state["low_threshold"] = max(0.0, min(100.0, float(data["low"])))
        if "high" in data:
            state["high_threshold"] = max(0.0, min(100.0, float(data["high"])))
        if state["low_threshold"] >= state["high_threshold"]:
            # keep thresholds sane — low must stay below high
            state["low_threshold"] = max(0.0, state["high_threshold"] - 5)
        snapshot = {"low_threshold": state["low_threshold"], "high_threshold": state["high_threshold"]}
    return jsonify(snapshot)


@app.route("/api/mode", methods=["POST"])
def api_mode():
    data = request.get_json(force=True, silent=True) or {}
    mode = data.get("mode", "AUTO").upper()
    if mode not in {"AUTO", "FILL", "DRAIN", "HOLD"}:
        return jsonify({"error": "invalid mode"}), 400
    with state_lock:
        state["mode"] = mode
    return jsonify({"mode": mode})


if __name__ == "__main__":
    threading.Thread(target=sensor_loop, daemon=True).start()
    app.run(debug=True, host="0.0.0.0", port=5000)


# ----------------------------------------------------------------------
# REAL HARDWARE VERSION (Raspberry Pi + HC-SR04 ultrasonic sensor)
# ----------------------------------------------------------------------
# Swap the WaterLevelSensor class above for this one on real hardware.
# Wiring: VCC->5V, GND->GND, TRIG->GPIO23, ECHO->GPIO24 (through a
# voltage divider, since ECHO outputs 5V and the Pi's GPIO expects 3.3V).
#
# import RPi.GPIO as GPIO
#
# TRIG_PIN, ECHO_PIN = 23, 24
#
# class WaterLevelSensor:
#     def __init__(self, tank_height_cm):
#         self.tank_height_cm = tank_height_cm
#         GPIO.setmode(GPIO.BCM)
#         GPIO.setup(TRIG_PIN, GPIO.OUT)
#         GPIO.setup(ECHO_PIN, GPIO.IN)
#
#     def read_distance_cm(self):
#         GPIO.output(TRIG_PIN, True)
#         time.sleep(0.00001)
#         GPIO.output(TRIG_PIN, False)
#
#         start, stop = time.time(), time.time()
#         while GPIO.input(ECHO_PIN) == 0:
#             start = time.time()
#         while GPIO.input(ECHO_PIN) == 1:
#             stop = time.time()
#
#         elapsed = stop - start
#         distance_cm = (elapsed * 34300) / 2   # speed of sound = 34300 cm/s
#         return round(distance_cm, 2)
