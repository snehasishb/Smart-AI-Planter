import Adafruit_DHT
import time

# Sensor type and GPIO pin
SENSOR = Adafruit_DHT.DHT11
GPIO_PIN = 4  # GPIO4 = Pin 7

try:
    while True:
        humidity, temperature = Adafruit_DHT.read_retry(SENSOR, GPIO_PIN)

        if humidity is not None and temperature is not None:
            print(f"🌡️  Temperature: {temperature:.1f}°C  |  💧 Humidity: {humidity:.1f}%")
        else:
            print("❌ Sensor error — no valid readings yet.")

        time.sleep(2)

except KeyboardInterrupt:
    print("\n👋 Exiting gracefully...")

