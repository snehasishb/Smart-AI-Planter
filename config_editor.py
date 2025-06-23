from flask import Flask, render_template_string, request, redirect
import os

app = Flask(__name__)
VARIABLES_FILE = "variables.conf"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Config Editor</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        input[type=text] { width: 300px; }
        input[type=submit] { padding: 6px 12px; }
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
</body>
</html>
"""

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

@app.route("/", methods=["GET", "POST"])
def edit_config():
    message = ""
    config = read_config()
    if request.method == "POST":
        for key in config:
            config[key] = request.form.get(key, config[key])
        write_config(config)
        message = "Configuration saved successfully."
    return render_template_string(HTML_TEMPLATE, config=config, message=message)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

