import json
import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
DB_FILE = 'voterwa_db.json'

# Function to read the database
def get_db():
    if not os.path.exists(DB_FILE):
        return {"schools": []} # Return empty if file doesn't exist
    with open(DB_FILE, 'r') as f:
        return json.load(f)

# Route to save data from the website to the server
@app.route('/api/save_db', methods=['POST'])
def save_data():
    data = request.get_json()
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)
    return jsonify({"status": "success"})

# Route to send the database to the website
@app.route('/api/get_db')
def get_data():
    return jsonify(get_db())

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<page>')
def show_page(page):
    if not page.endswith('.html'): page += '.html'
    return render_template(page)

if __name__ == '__main__':
    app.run(debug=True)
