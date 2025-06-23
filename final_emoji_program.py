import time
import board
import busio
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
from luma.core.interface.serial import spi
from luma.lcd.device import st7735
from adafruit_ads1x15.ads1115 import ADS1115, P1, P2
from adafruit_ads1x15.analog_in import AnalogIn
import Adafruit_DHT

# --- GPIO Setup ---
RELAY_PIN = 14
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.LOW)

# --- I2C and ADS1115 Setup ---
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS1115(i2c)

channel_soil = AnalogIn(ads, P1)
channel_water = AnalogIn(ads, P2)

SOIL_DRY_VOLTAGE = 3.8378
SOIL_WET_VOLTAGE = 3.8403

WATER_EMPTY_VOLTAGE = 2.4000
WATER_FULL_VOLTAGE = 2.9000

# --- DHT11 Setup ---
DHT_SENSOR = Adafruit_DHT.DHT11
DHT_PIN = 4

# --- TFT Setup ---
serial = spi(port=0, device=0, gpio_DC=24, gpio_RST=25)  # Adjust pins as per your wiring
device = st7735(serial, width=128, height=160, rotation=90)

# Load emoji icons (32x32) - path to your extracted PNGs
EMOJI_PATH = "/home/pi/emoji_icons/"  # Update path to your emoji PNG folder

emoji_files = {
    "too_cold": "too_cold.png",
    "too_hot": "too_hot.png",
    "humidity": "humidity.png",
    "watering": "watering.png",
    "fill_water": "fill_water.png",
    "ok": "ok.png"
}

# Preload emojis
emojis = {key: Image.open(EMOJI_PATH + fname).convert("RGBA") for key, fname in emoji_files.items()}

# Font for text (default PIL font, or replace with TTF)
font = ImageFont.load_default()

def read_avg_voltage(channel, samples=10):
    total = 0
    for _ in range(samples):
        total += channel.voltage
        time.sleep(0.01)
    return total / samples

def soil_moisture_percent(v):
    if v <= SOIL_DRY_VOLTAGE:
        return 0
    elif v >= SOIL_WET_VOLTAGE:
        return 100
    else:
        return int((v - SOIL_DRY_VOLTAGE) / (SOIL_WET_VOLTAGE - SOIL_DRY_VOLTAGE) * 100)

def water_level_percent(v):
    if v <= WATER_EMPTY_VOLTAGE:
        return 0
    elif v >= WATER_FULL_VOLTAGE:
        return 100
    else:
        return int((v - WATER_EMPTY_VOLTAGE) / (WATER_FULL_VOLTAGE - WATER_EMPTY_VOLTAGE) * 100)

def display_message(device, emoji_img, lines):
    # Clear screen
    img = Image.new("RGB", (device.width, device.height), "black")
    draw = ImageDraw.Draw(img)
    # Paste emoji top-left corner
    img.paste(emoji_img, (5, 5), emoji_img)
    # Draw text to the right of emoji
    y = 10
    x = 45
    for line in lines:
        draw.text((x, y), line, font=font, fill="white")
        y += 15
    device.display(img)

try:
    while True:
        # Read sensors
        soil_v = read_avg_voltage(channel_soil)
        water_v = read_avg_voltage(channel_water)
        soil_pct = soil_moisture_percent(soil_v)
        water_pct = water_level_percent(water_v)

        humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)

        messages = []
        emojis_to_show = []

        # Temperature/Humidity checks
        if temperature is not None:
            if temperature < 18:
                messages.append("Too cold! Temp below 18C")
                emojis_to_show.append(emojis["too_cold"])
            elif temperature > 24:
                messages.append("Too hot! Temp above 24C")
                emojis_to_show.append(emojis["too_hot"])
        else:
            messages.append("Temp: Error reading sensor")

        if humidity is not None:
            if humidity > 60:
                messages.append("High humidity > 60%")
                emojis_to_show.append(emojis["humidity"])
        else:
            messages.append("Humidity: Error reading sensor")

        # Watering logic
        if soil_pct == 0:
            if water_pct > 0:
                messages.append("Watering plant 🌱💧")
                emojis_to_show.append(emojis["watering"])
                GPIO.output(RELAY_PIN, GPIO.HIGH)
                time.sleep(2)
                # Re-check water level during watering
                water_v = read_avg_voltage(channel_water)
                water_pct = water_level_percent(water_v)
                if water_pct == 0:
                    messages.append("Water ran out! Stop motor")
                    emojis_to_show.append(emojis["fill_water"])
                    GPIO.output(RELAY_PIN, GPIO.LOW)
                else:
                    messages.append(f"Watering... Level: {water_pct}%")
            else:
                messages.append("No water! Fill tank 🚱")
                emojis_to_show.append(emojis["fill_water"])
                GPIO.output(RELAY_PIN, GPIO.LOW)
        else:
            messages.append("Soil moisture OK")
            emojis_to_show.append(emojis["ok"])
            GPIO.output(RELAY_PIN, GPIO.LOW)

        # If no critical conditions, show all is well
        if not messages:
            messages = ["All is well."]
            emojis_to_show = [emojis["ok"]]

        # Show messages and emojis on TFT one by one with delay
        for emoji_img, msg in zip(emojis_to_show, messages):
            display_message(device, emoji_img, [msg])
            print(msg)
            time.sleep(4)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    GPIO.output(RELAY_PIN, GPIO.LOW)
    GPIO.cleanup()

