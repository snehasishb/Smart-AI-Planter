from flask import Flask, request, render_template_string, redirect, url_for
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Load Hugging Face API token and URL
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"}

VARIABLES_FILE = "variables.conf"
ALERTS_LOG = "alerts.log"

# Templates
HOME_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>AI Plant Assistant</title></head>
<body>
    <h1>Ask AI about your plant</h1>
    <form method="post" action="/ask">
        <input type="text" name="prompt" placeholder="e.g. Why did my plant die?" size="60">
        <input type="submit" value="Ask">
    </form>
    {% if ai_response %}
        <p><strong>AI Response:</strong> {{ ai_response }}</p>
    {% endif %}
    {% if error %}
        <p style="color:red;"><strong>Error:</strong> {{ error }}</p>
    {% endif %}
    <br>
    <a href="{{ url_for('edit_config') }}">Edit Configuration</a>
</body>
</html>
"""

CONFIG_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Edit Configuration</title>
</head>
<body>
    <h1>Edit Configuration</h1>
    <form method="post">
        {% for key, value in config.items() %}
            <p>
                <label>{{ key }}</label><br>
                <input type="text" name="{{ key }}" value="{{ value }}">
            </p>
        {% endfor %}
        <input type="submit" value="Save">
    </form>
    {% if message %}
        <p style="color:green;">{{ message }}</p>
    {% endif %}
    <br>
    <a href="{{ url_for('index') }}">Back to AI Assistant</a>
</body>
</html>
"""

# Config read/write functions
def read_config():
    config = {}
    if os.path.exists(VARIABLES_FILE):
        with open(VARIABLES_FILE, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    config[key.strip()] = value.strip()
    return config

def write_config(config):
    with open(VARIABLES_FILE, 'w') as f:
        for key, value in config.items():
            f.write(f"{key}={value}\n")

# Routes
@app.route("/", methods=["GET"])
def index():
    return render_template_string(HOME_TEMPLATE)

@app.route("/ask", methods=["POST"])
def ask_ai():
    prompt = request.form.get("prompt", "").strip()
    if not prompt:
        return render_template_string(HOME_TEMPLATE, error="Prompt is empty.")

    if not HF_API_TOKEN:
        return render_template_string(HOME_TEMPLATE, error="Missing Hugging Face API token.")

    if not os.path.exists(ALERTS_LOG):
        return render_template_string(HOME_TEMPLATE, error="alerts.log file not found.")

    try:
        with open(ALERTS_LOG, "r") as log_file:
            alerts_text = log_file.read()
    except Exception as e:
        return render_template_string(HOME_TEMPLATE, error=f"Error reading alerts.log: {e}")

    full_prompt = f"""Act as a smart plant monitoring assistant.

Here is the recent sensor alert log from a smart planter:

{alerts_text}

Now, based on this log, answer this user question in simple language:

Q: {prompt}
A:"""

    try:
        response = requests.post(HF_API_URL, headers=HEADERS, json={"inputs": full_prompt})
        if response.status_code == 200:
            output = response.json()
            if isinstance(output, list) and "generated_text" in output[0]:
                ai_text = output[0]["generated_text"]
            elif isinstance(output, dict) and "generated_text" in output:
                ai_text = output["generated_text"]
            else:
                ai_text = str(output)
            if ai_text.strip() == "...":
                ai_text = "Sorry, I couldn't understand the log well enough to answer that."
        else:
            ai_text = f"API error: {response.status_code} - {response.text}"
    except Exception as e:
        ai_text = f"Exception occurred: {e}"

    return render_template_string(HOME_TEMPLATE, ai_response=ai_text, error="")

@app.route("/config", methods=["GET", "POST"])
def edit_config():
    config = read_config()
    message = ""
    if request.method == "POST":
        for key in config:
            config[key] = request.form.get(key, config[key])
        write_config(config)
        message = "Configuration saved."
    return render_template_string(CONFIG_TEMPLATE, config=config, message=message)

# Start app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
