import json
import os
from flask import Flask, render_template, request, jsonify
from flask_mailman import Mail, EmailMessage

app = Flask(__name__)
DB_FILE = 'voterwa_db.json'

# --- EMAIL CONFIGURATION ---
app.config['MAIL_SERVER'] = '://gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True  # Use SSL for Port 465
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER') 
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS') 
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('EMAIL_USER')


mail = Mail(app)

# Helper function to read the database
def get_db():
    if not os.path.exists(DB_FILE):
        return {"schools": []}
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"schools": []}

# --- ROUTES ---

@app.route('/')
def index():
    # If database doesn't exist, you might want to redirect to setup
    # For now, just serving the index
    return render_template('index.html')

@app.route('/api/contact', methods=['POST'])
def handle_contact():
    data = request.get_json()
    school = data.get('school_name', 'Unknown School')
    sender_email = data.get('email', 'No email provided')
    message_body = data.get('message', '')

    msg = EmailMessage(
        subject=f"New VoteRwa Inquiry: {school}",
        body=f"From: {school}\nContact: {sender_email}\n\nMessage:\n{message_body}",
        to=[os.environ.get('EMAIL_USER')] 
    )
    
    try:
        msg.send()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# This matches the 'initializeDB()' function in your HTML
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
    # Automatically add .html if user types /login instead of /login.html
    if not page.endswith('.html'): 
        page += '.html'
    try:
        return render_template(page)
    except Exception:
        return render_template('index.html') # Fallback to home if page missing

if __name__ == '__main__':
    # Use the PORT environment variable for Render compatibility
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
