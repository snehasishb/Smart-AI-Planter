import time
import board
import busio
import RPi.GPIO as GPIO
from adafruit_ads1x15.ads1115 import ADS1115, P0, P1, P2
from adafruit_ads1x15.analog_in import AnalogIn

# Setup GPIO for motor control
RELAY_PIN = 14  # GPIO14 (physical pin 8)
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.LOW)

# Setup I2C and ADS1115
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS1115(i2c)

# Analog channels
channel_dht11 = AnalogIn(ads, P0)
channel_soil = AnalogIn(ads, P1)
channel_water = AnalogIn(ads, P2)

# Calibrated voltage levels (based on your readings)
SOIL_DRY_VOLTAGE = 3.8378    # 0% moisture
SOIL_WET_VOLTAGE = 3.8403    # 100% moisture

WATER_EMPTY_VOLTAGE = 0.04
WATER_FULL_VOLTAGE = 3.0

# Helper Functions
def read_avg_voltage(channel, samples=10):
    return sum(channel.voltage for _ in range(samples)) / samples

def soil_moisture_percent(voltage):
    if voltage <= SOIL_DRY_VOLTAGE:
        return 0
    elif voltage >= SOIL_WET_VOLTAGE:
        return 100
    else:
        return int((voltage - SOIL_DRY_VOLTAGE) / (SOIL_WET_VOLTAGE - SOIL_DRY_VOLTAGE) * 100)

def water_level_percent(voltage):
    if voltage <= WATER_EMPTY_VOLTAGE:
        return 0
    elif voltage >= WATER_FULL_VOLTAGE:
        return 100
    else:
        return int((voltage - WATER_EMPTY_VOLTAGE) / (WATER_FULL_VOLTAGE - WATER_EMPTY_VOLTAGE) * 100)

# Main loop
try:
    while True:
        dht_voltage = read_avg_voltage(channel_dht11)
        soil_voltage = read_avg_voltage(channel_soil)
        water_voltage = read_avg_voltage(channel_water)

        soil_percent = soil_moisture_percent(soil_voltage)
        water_percent = water_level_percent(water_voltage)

        print("\n--- Sensor Readings ---")
        print(f"DHT11 analog voltage (A0):      {dht_voltage:.4f} V (for reference only)")
        print(f"Soil Moisture Sensor (A1):      {soil_voltage:.4f} V → {soil_percent}% moisture")
        print(f"Water Level Sensor (A2):        {water_voltage:.4f} V → {water_percent}% water level")

        if soil_percent == 0:
            GPIO.output(RELAY_PIN, GPIO.HIGH)
            print("Motor ON: Soil is completely dry.")
        else:
            GPIO.output(RELAY_PIN, GPIO.LOW)
            print("Motor OFF: Soil has moisture.")

        time.sleep(2)

except KeyboardInterrupt:
    print("\nExiting...")

finally:
    GPIO.output(RELAY_PIN, GPIO.LOW)
    GPIO.cleanup()

