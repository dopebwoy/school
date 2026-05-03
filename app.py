import json
import os
import smtplib
from flask import Flask, render_template, request, jsonify
from flask_mailman import Mail, EmailMessage
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
DB_FILE = 'voterwa_db.json'

# --- FIXED EMAIL CONFIGURATION ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# Option A: Use Port 465 with SSL (Very stable for Render)
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
# Option B (If A fails): Use Port 587, set SSL=False, TLS=True

app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER') 
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS') 
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('EMAIL_USER')
# Added a timeout to prevent the "Worker Timeout" crash
app.config['MAIL_TIMEOUT'] = 10 

mail = Mail(app)

def get_db():
    if not os.path.exists(DB_FILE):
        return {"schools": []}
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"schools": []}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/contact', methods=['POST'])
def handle_contact():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400

        school = data.get('school_name', 'Unknown School')
        sender_email = data.get('email', 'No email provided')
        message_body = data.get('message', '')

        msg = EmailMessage(
            subject=f"New VoteRwa Inquiry: {school}",
            body=f"From: {school}\nContact: {sender_email}\n\nMessage:\n{message_body}",
            to=[os.environ.get('EMAIL_USER')] 
        )
        
        msg.send()
        return jsonify({"status": "success"})

    except smtplib.SMTPAuthenticationError:
        return jsonify({"status": "error", "message": "Login failed. Check App Password."}), 401
    except Exception as e:
        print(f"MAIL ERROR: {str(e)}") 
        return jsonify({"status": "error", "message": "Mail server busy. Please try again."}), 500

@app.route('/api/save_db', methods=['POST'])
def save_data():
    try:
        data = request.get_json()
        with open(DB_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/get_db')
def get_data():
    return jsonify(get_db())

@app.route('/<path:page>')
def show_page(page):
    if not page.endswith('.html'): 
        page += '.html'
    try:
        return render_template(page)
    except Exception:
        return render_template('index.html') 

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
