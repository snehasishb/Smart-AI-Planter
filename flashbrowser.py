from flask import Flask, render_template_string, request, render_template, redirect
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
VARIABLES_FILE = "variables.conf"

# OpenAI Client Initialization
client = OpenAI()

# --- HTML Templates ---
HTML_CONFIG = """
<!DOCTYPE html>
<html>
<head>
    <title>Config Editor</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        input[type=text] { width: 300px; }
        input[type=submit] { padding: 6px 12px; }
        a { text-decoration: none; display: inline-block; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>Edit Configuration</h1>
    <form method="post">
        {% for key, value in config.items() %}
            <p>
                <label><b>{{ key }}:</b></label><br>
                <input type="text" name="{{ key }}" value="{{ value }}">
            </p>
        {% endfor %}
        <input type="submit" value="Save">
    </form>
    {% if message %}
        <p style="color:green;">{{ message }}</p>
    {% endif %}
    <a href="/ask">🔙 Back to Ask GPT</a>
</body>
</html>
"""

HTML_CHAT = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Plant Q&A</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        input[type=text] { width: 400px; padding: 8px; }
        input[type=submit] { padding: 8px 16px; }
        textarea { width: 100%; height: 200px; margin-top: 20px; }
        a { text-decoration: none; display: inline-block; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>Smart Plant Assistant</h1>
    <form method="post">
        <input type="text" name="prompt" placeholder="Why did the plant die?" value="{{ prompt or '' }}">
        <input type="submit" value="Ask">
    </form>
    {% if answer %}
        <h3>Answer:</h3>
        <textarea readonly>{{ answer }}</textarea>
    {% elif error %}
        <p style="color:red;">Error: {{ error }}</p>
    {% endif %}
    <a href="/config">⚙️ Edit Config</a>
</body>
</html>
"""

# --- Config Helper Functions ---
def read_config():
    config = {}
    if not os.path.exists(VARIABLES_FILE):
        return config
    with open(VARIABLES_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line and '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
    return config

def write_config(config):
    with open(VARIABLES_FILE, 'w') as f:
        for key, value in config.items():
            f.write(f"{key}={value}\n")

# --- Routes ---
@app.route("/config", methods=["GET", "POST"])
def edit_config():
    message = ""
    config = read_config()
    if request.method == "POST":
        for key in config:
            config[key] = request.form.get(key, config[key])
        write_config(config)
        message = "Configuration saved successfully."
    return render_template_string(HTML_CONFIG, config=config, message=message)

@app.route("/", methods=["GET", "POST"])
@app.route("/ask", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_prompt = request.form.get("prompt")
        if not user_prompt:
            return render_template_string(HTML_CHAT, error="Please enter a prompt.")
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful plant monitoring assistant."},
                    {"role": "user", "content": user_prompt}
                ]
            )
            answer = response.choices[0].message.content
            return render_template_string(HTML_CHAT, answer=answer, prompt=user_prompt)
        except Exception as e:
            return render_template_string(HTML_CHAT, error=str(e))
    return render_template_string(HTML_CHAT)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

