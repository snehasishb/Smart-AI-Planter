import RPi.GPIO as GPIO

# Define the GPIO pin
RELAY_PIN = 14  # GPIO14 (physical pin 8)

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)

print("\nRelay Control via Keyboard")
print("Type 'on' to turn ON the relay")
print("Type 'off' to turn OFF the relay")
print("Type 'exit' to quit\n")

try:
    while True:
        cmd = input("Command (on/off/exit): ").strip().lower()
        
        if cmd == "on":
            GPIO.output(RELAY_PIN, GPIO.HIGH)
            print("Relay is ON")

        elif cmd == "off":
            GPIO.output(RELAY_PIN, GPIO.LOW)
            print("Relay is OFF")

        elif cmd == "exit":
            print("Exiting program.")
            break

        else:
            print("Invalid command. Use 'on', 'off', or 'exit'.")

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    GPIO.cleanup()
    print("GPIO cleanup done.")
