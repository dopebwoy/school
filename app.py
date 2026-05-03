import os
import smtplib
from flask import Flask, render_template, request, jsonify
from flask_mailman import Mail, EmailMessage
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
CORS(app)

# --- DATABASE CONFIGURATION ---
# This looks for your DATABASE_URL and fixes the 'postgres://' prefix for SQLAlchemy
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- DATABASE MODEL ---
# This replaces your JSON file structure
class VoterData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # We store the entire JSON object in one column to keep your logic the same
    content = db.Column(db.JSON, nullable=False)

# Create the database table automatically if it doesn't exist
with app.app_context():
    db.create_all()

# --- EMAIL CONFIGURATION ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER') 
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS') 
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('EMAIL_USER')
app.config['MAIL_TIMEOUT'] = 15 

mail = Mail(app)

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
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/save_db', methods=['POST'])
def save_data():
    try:
        data = request.get_json()
        # Clear old data and save new (simplest way to mimic your JSON file)
        VoterData.query.delete() 
        new_entry = VoterData(content=data)
        db.session.add(new_entry)
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/get_db')
def get_data():
    # Pull the latest data from Postgres
    record = VoterData.query.order_by(VoterData.id.desc()).first()
    if record:
        return jsonify(record.content)
    return jsonify({"schools": []}) # Return empty if no data exists yet

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
