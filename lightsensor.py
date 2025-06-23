import time
import board
import busio
from adafruit_ads1x15.ads1115 import ADS1115, P0
from adafruit_ads1x15.analog_in import AnalogIn

# --- I2C and ADS1115 Setup ---
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS1115(i2c)

# TEMT6000 on ADS1115 A0
light_channel = AnalogIn(ads, P0)

# --- Lux Calculation ---
def voltage_to_lux(voltage):
    """
    Approximate conversion from voltage to lux.
    This is a rough linear estimation:
    TEMT6000 = ~1 µA per lux → via 10K pull-down = ~0.01V per lux
    """
    # For example: 1 lux = 0.01V → lux = voltage / 0.01
    lux = voltage / 0.01
    return int(lux)

# --- Read Loop ---
try:
    while True:
        voltage = light_channel.voltage
        lux = voltage_to_lux(voltage)

        print(f"🔆 Light Sensor Voltage: {voltage:.4f} V → Estimated Lux: {lux} lx")

        time.sleep(1)

except KeyboardInterrupt:
    print("\nExiting gracefully.")

