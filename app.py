import json
import os
import smtplib  # Added to catch specific mail errors
from flask import Flask, render_template, request, jsonify
from flask_mailman import Mail, EmailMessage

app = Flask(__name__)
DB_FILE = 'voterwa_db.json'

# --- EMAIL CONFIGURATION ---
# FIXED: Changed '://gmail.com' to 'smtp.gmail.com'
app.config['MAIL_SERVER'] = 'smtp.gmail.com' 
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True  
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER') 
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS') 
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('EMAIL_USER')

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
        return jsonify({"status": "error", "message": "Email login failed. Check your App Password."}), 401
    except smtplib.SMTPConnectError:
        return jsonify({"status": "error", "message": "Could not connect to Gmail. Try Port 587 or 465."}), 503
    except Exception as e:
        # This catches "Name or service not known" and other general errors
        print(f"DEBUG ERROR: {str(e)}") 
        return jsonify({"status": "error", "message": f"Server Error: {str(e)}"}), 500

@app.route('/api/save_db', methods=['POST'])
def save_data():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400
            
        with open(DB_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        return jsonify({"status": "success", "message": "Database Initialized"})
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
