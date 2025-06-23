import RPi.GPIO as GPIO
import time

# --- GPIO Setup ---
PIR_PIN = 17  # GPIO17 / Pin 11
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)

print("📡 SR505 PIR Sensor Test Running...")
print("👉 Waiting for motion... (Press Ctrl+C to exit)")

try:
    while True:
        if GPIO.input(PIR_PIN):
            print("🚶 Motion Detected (HIGH)")
        else:
            print("🔇 No Motion (LOW)")
        time.sleep(1)

except KeyboardInterrupt:
    print("\n❌ Test stopped by user.")

finally:
    GPIO.cleanup()
    print("GPIO cleanup complete.")

