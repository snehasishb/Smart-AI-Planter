import time
import board
import busio
import RPi.GPIO as GPIO
from adafruit_ads1x15.ads1115 import ADS1115, P0, P1, P2
from adafruit_ads1x15.analog_in import AnalogIn

# Setup relay pin
RELAY_PIN = 14
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)

# Setup I2C and ADS1115
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS1115(i2c)

# Setup analog input channels
channel_dht22 = AnalogIn(ads, P0)  # A0
channel_soil = AnalogIn(ads, P1)   # A1
channel_water = AnalogIn(ads, P2)  # A2

try:
    while True:
        print("\n--- Sensor Readings ---")
        print(f"DHT22 Analog Voltage (A0):     {channel_dht22.voltage:.2f} V")
        print(f"Soil Moisture Sensor (A1):     {channel_soil.voltage:.2f} V")
        print(f"Water Level Sensor (A2):       {channel_water.voltage:.2f} V")

        print("Turning Relay ON")
        GPIO.output(RELAY_PIN, GPIO.HIGH)
        time.sleep(2)

        print("Turning Relay OFF")
        GPIO.output(RELAY_PIN, GPIO.LOW)
        time.sleep(2)

        time.sleep(1)

except KeyboardInterrupt:
    print("\nExiting...")

finally:
    GPIO.cleanup()

