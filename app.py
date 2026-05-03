import os
import smtplib
from flask import Flask, render_template, request, jsonify
from flask_mailman import Mail, EmailMessage
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import flag_modified

app = Flask(__name__)
CORS(app)

# --- DATABASE CONFIGURATION ---
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- DATABASE MODEL ---
class VoterData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.JSON, nullable=False)

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

# --- SECURE VOTING ROUTE (THE FIX) ---
@app.route('/api/cast_vote', methods=['POST'])
def cast_vote():
    try:
        data = request.get_json()
        student_code = data.get('student_code')
        selections = data.get('selections') # List of candidate IDs
        school_code = data.get('school_code')

        record = VoterData.query.first()
        if not record:
            return jsonify({"status": "error", "message": "Database empty"}), 404
        
        # Access the JSON data
        db_content = record.content
        
        # Find the specific school in the list
        school = next((s for s in db_content['schools'] if s['schoolCode'] == school_code), None)
        if not school:
            return jsonify({"status": "error", "message": "School not found"}), 404

        # 1. Safety Check: Already voted?
        if school['settings'].get('votedStudents', {}).get(student_code):
            return jsonify({"status": "error", "message": "You have already voted!"}), 400

        # 2. Increment votes for each selected candidate
        if 'votes' not in school['settings']:
            school['settings']['votes'] = {}
            
        for cid in selections:
            cid_str = str(cid)
            current_count = school['settings']['votes'].get(cid_str, 0)
            school['settings']['votes'][cid_str] = current_count + 1
        
        # 3. Mark student as having voted
        if 'votedStudents' not in school['settings']:
            school['settings']['votedStudents'] = {}
        school['settings']['votedStudents'][student_code] = True

        # 4. Save changes
        # Tell SQLAlchemy the JSON was modified so it actually saves
        record.content = db_content
        flag_modified(record, "content") 
        db.session.commit()
        
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/save_db', methods=['POST'])
def save_data():
    try:
        data = request.get_json()
        VoterData.query.delete() 
        new_entry = VoterData(content=data)
        db.session.add(new_entry)
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/get_db')
def get_data():
    record = VoterData.query.first()
    if record:
        return jsonify(record.content)
    return jsonify({"schools": []})

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
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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
