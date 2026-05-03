import json
import os
from flask import Flask, render_template, request, jsonify
from flask_mailman import Mail, EmailMessage

app = Flask(__name__)
DB_FILE = 'voterwa_db.json'

# --- EMAIL CONFIGURATION ---
# Use environment variables (set these in Render settings)
app.config['MAIL_SERVER'] = 'smtp.gmail.com' # Fixed the URL here
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER') 
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS') # Your 16-char App Password
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('EMAIL_USER')

mail = Mail(app)

# Function to read the database
def get_db():
    if not os.path.exists(DB_FILE):
        return {"schools": []}
    with open(DB_FILE, 'r') as f:
        return json.load(f)

# --- ROUTES ---

@app.route('/api/contact', methods=['POST'])
def handle_contact():
    data = request.get_json()
    school = data.get('school_name', 'Unknown School')
    # Fallback if email is not provided
    sender_email = data.get('email') if data.get('email') else 'No email provided'
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

@app.route('/api/save_db', methods=['POST'])
def save_data():
    data = request.get_json()
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)
    return jsonify({"status": "success"})

@app.route('/api/get_db')
def get_data():
    return jsonify(get_db())

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<page>')
def show_page(page):
    if not page.endswith('.html'): page += '.html'
    try:
        return render_template(page)
    except:
        return "Page not found", 404

if __name__ == '__main__':
    app.run(debug=True)
