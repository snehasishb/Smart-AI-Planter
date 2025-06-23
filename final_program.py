import time
import board
import busio
import RPi.GPIO as GPIO
import Adafruit_DHT
import os
import zipfile
from datetime import datetime
from adafruit_ads1x15.ads1115 import ADS1115, P0, P1, P2
from adafruit_ads1x15.analog_in import AnalogIn

# --- Load Variables from variables.txt ---
def load_variables(filepath="variables.conf"):
    variables = {}
    with open(filepath) as file:
        for line in file:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                try:
                    variables[key] = float(value)
                except ValueError:
                    variables[key] = value
    return variables

config = load_variables()

# --- GPIO Setup ---
RELAY_PIN = 14
PIR_PIN = 17  # GPIO17 for SR505 PIR Motion Sensor
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.setup(PIR_PIN, GPIO.IN)
GPIO.output(RELAY_PIN, GPIO.LOW)  # Motor off initially

# --- I2C and ADS1115 Setup ---
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS1115(i2c)

# --- Sensor Channels ---
channel_light = AnalogIn(ads, P0)
channel_soil = AnalogIn(ads, P1)
channel_water = AnalogIn(ads, P2)

# --- DHT11 Sensor Setup ---
DHT_SENSOR = Adafruit_DHT.DHT11
DHT_PIN = 4  # GPIO4

# --- Watering Control Variables ---
last_watering_time = 0
watering_wait_period = 300  # 5 minutes
watering_duration = 5       # 5 seconds

# --- Alert Log Setup ---
LOG_FILE = "alerts.log"

def log_alert(message):
    timestamp = datetime.now().strftime("%d-%m %H:%M")
    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")

    # Compress if log grows too big
    if os.path.getsize(LOG_FILE) > 50_000:  # ~50 KB
        archive_name = f"alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(LOG_FILE)
        open(LOG_FILE, "w").close()  # Clear log

# --- Helper Functions ---

def read_avg_voltage(channel, samples=10):
    total = 0
    for _ in range(samples):
        total += channel.voltage
        time.sleep(0.01)
    return total / samples

def soil_moisture_percent(voltage):
    dry = config["SOIL_DRY_VOLTAGE"]
    wet = config["SOIL_WET_VOLTAGE"]
    if voltage <= dry:
        return 0
    elif voltage >= wet:
        return 100
    return int((voltage - dry) / (wet - dry) * 100)

def water_level_percent(voltage):
    empty = config["WATER_EMPTY_VOLTAGE"]
    full = config["WATER_FULL_VOLTAGE"]
    if voltage <= empty:
        return 0
    elif voltage >= full:
        return 100
    return int((voltage - empty) / (full - empty) * 100)

def classify_light_level(lux):
    if lux < config["LIGHT_THRESHOLDS_dark"]:
        return "🌑 Dark room (<10 lx)"
    elif config["LIGHT_THRESHOLDS_low_min"] <= lux <= config["LIGHT_THRESHOLDS_low_max"]:
        return "🌥️ Low light (300–500 lx)"
    elif config["LIGHT_THRESHOLDS_ideal_min"] <= lux <= config["LIGHT_THRESHOLDS_ideal_max"]:
        return "🌞 Ideal light (1000–5000 lx)"
    elif lux > config["LIGHT_THRESHOLDS_too_much"]:
        return "☀️ Too much light (>5000 lx)"
    return "🕶️ Moderate light"

def calculate_lux_from_voltage(voltage):
    return voltage * 1000  # Approximation: 1V ≈ 1000 lux

# --- Main Loop ---

try:
    while True:
        messages = []

        # Read sensors
        soil_voltage = read_avg_voltage(channel_soil)
        water_voltage = read_avg_voltage(channel_water)
        light_voltage = read_avg_voltage(channel_light)
        soil_percent = soil_moisture_percent(soil_voltage)
        water_percent = water_level_percent(water_voltage)
        lux = calculate_lux_from_voltage(light_voltage)

        humidity, temperature_c = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)

        # Motion Detection
        motion_detected = GPIO.input(PIR_PIN)
        print(f"\n[Motion] {'Detected 👀' if motion_detected else 'No motion'}")

        # Display Sensor Readings
        print("\n--- Sensor Readings ---")
        print(f"Soil Moisture: {soil_voltage:.4f} V → {soil_percent}%")
        print(f"Water Level:   {water_voltage:.4f} V → {water_percent}%")
        print(f"Ambient Light: {light_voltage:.4f} V → {lux:.0f} lux")
        print(f"Light Level:   {classify_light_level(lux)}")

        if temperature_c is not None and humidity is not None:
            print(f"Temperature:   {temperature_c} °C")
            print(f"Humidity:      {humidity} %")
        else:
            print("❌ DHT11 Sensor Read Error")

        # Alerts
        if temperature_c is not None:
            if temperature_c < config["TEMP_THRESHOLDS_low"]:
                alert = "⚠️ Too cold! Temperature below threshold."
                messages.append(alert)
                log_alert(alert)
            elif temperature_c > config["TEMP_THRESHOLDS_high"]:
                alert = "⚠️ Too hot! Temperature above threshold."
                messages.append(alert)
                log_alert(alert)

        if humidity is not None and humidity > config["HUMIDITY_THRESHOLD"]:
            alert = "⚠️ Too much humidity! Above 60%."
            messages.append(alert)
            log_alert(alert)

        light_class = classify_light_level(lux)
        messages.append(f"Light Level: {light_class}")

        # Watering Logic
        current_time = time.time()
        if soil_percent == 0:
            if water_percent > 0:
                if current_time - last_watering_time >= watering_wait_period:
                    msg = "🌱 Soil dry and water available → Starting burst watering..."
                    print(msg)
                    log_alert(msg)
                    GPIO.output(RELAY_PIN, GPIO.HIGH)
                    time.sleep(watering_duration)
                    GPIO.output(RELAY_PIN, GPIO.LOW)
                    log_alert("💧 Pump OFF. Waiting for moisture absorption.")
                    last_watering_time = current_time
                else:
                    wait_left = int((watering_wait_period - (current_time - last_watering_time)) / 60)
                    messages.append(f"⏳ Waiting for absorption ({wait_left} min left)...")
            else:
                alert = "❌ No water available! Fill the tank."
                messages.append(alert)
                log_alert(alert)
                GPIO.output(RELAY_PIN, GPIO.LOW)
        else:
            print("✅ Soil moisture is sufficient.")
            GPIO.output(RELAY_PIN, GPIO.LOW)

        # Display System Messages
        print("\n--- System Messages ---")
        for msg in messages:
            print(msg)
            time.sleep(1)

        time.sleep(3)

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    GPIO.cleanup()
    print("GPIO cleanup complete.")

