import time
import board
import busio
from adafruit_ads1x15.ads1115 import ADS1115, P2
from adafruit_ads1x15.analog_in import AnalogIn

# Setup I2C and ADS1115
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS1115(i2c)

# Water level sensor is connected to A2
channel_water = AnalogIn(ads, P2)

def read_avg_voltage(channel, samples=10):
    return sum(channel.voltage for _ in range(samples)) / samples

try:
    print("Measuring water level sensor voltage. Press Ctrl+C to stop.\n")
    while True:
        voltage = read_avg_voltage(channel_water)
        print(f"Water Sensor Voltage (A2): {voltage:.4f} V")
        time.sleep(2)

except KeyboardInterrupt:
    print("\nMeasurement stopped. Use the highest stable voltage reading as your full water level value.")
