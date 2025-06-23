import time
import board
import busio
from adafruit_ads1x15.ads1115 import ADS1115, P1
from adafruit_ads1x15.analog_in import AnalogIn

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS1115(i2c)
channel_soil = AnalogIn(ads, P1)  # A1

try:
    while True:
        voltage = channel_soil.voltage
        print(f"Soil Sensor Voltage (A1): {voltage:.4f} V")
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopped")

