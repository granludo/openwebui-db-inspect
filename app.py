from datetime import datetime
import sqlite3
from flask import Flask, render_template, request  # Add 'request' to your imports
from flask_httpauth import HTTPBasicAuth
import json 
import markdown
import os 


DATABASE = os.getenv('DATABASE_PATH', 'webui.db')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'llmentor')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'llmprimer')


auth = HTTPBasicAuth()

users = {
    "llmentor": "llmprimer",  # You can replace 'admin' and 'password' with your desired credentials
}

@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username


app = Flask(__name__)

DATABASE = 'webui.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_unique_models():
    conn = get_db_connection()
    query = "SELECT DISTINCT json_each.value as model FROM chat, json_each(chat, '$.models')"
    models = conn.execute(query).fetchall()
    conn.close()
    return [model['model'] for model in models]



@app.route('/')
@auth.login_required
def index():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    model_name = request.args.get('model_name')

    models_list = get_unique_models()  # Get the list of unique models from the database

    conn = get_db_connection()
    where_clauses = []
    parameters = []

    if start_date and end_date and start_time and end_time:
        start_datetime = datetime.strptime(f"{start_date} {start_time}", '%Y-%m-%d %H:%M')
        end_datetime = datetime.strptime(f"{end_date} {end_time}", '%Y-%m-%d %H:%M')
        where_clauses.append("c.timestamp >= ? AND c.timestamp <= ?")
        parameters.extend([start_datetime.timestamp(), end_datetime.timestamp()])

    if model_name:
        where_clauses.append("json_extract(c.chat, '$.models') LIKE ?")
        parameters.append(f"%{model_name}%")

    if where_clauses:
        query = f"SELECT c.id, c.title, c.timestamp, c.chat FROM chat c WHERE {' AND '.join(where_clauses)}"
        chats = conn.execute(query, parameters).fetchall()
    else:
        chats = conn.execute("SELECT c.id, c.title, c.timestamp, c.chat FROM chat c").fetchall()
    
    conn.close()

    processed_chats = [{
        'id': chat['id'],
        'title': chat['title'],
        'timestamp': datetime.fromtimestamp(int(chat['timestamp'])).strftime('%Y-%m-%d %H:%M'),
        'models': ", ".join(json.loads(chat['chat']).get("models", []))
    } for chat in chats]

    return render_template('index.html', chats=processed_chats, models=models_list)



@app.route('/chat/<id>')
@auth.login_required
def chat(id):
    conn = get_db_connection()
    chat_record = conn.execute('SELECT * FROM chat WHERE id = ?', (id,)).fetchone()
    conn.close()
    if chat_record:
        # Parse the JSON data from the 'chat' field
        chat_data = json.loads(chat_record['chat'])
        messages = chat_data.get("messages", [])
        # Process each message to convert Markdown content to HTML
        for message in messages:
            message['content'] = markdown.markdown(message['content'])
        return render_template('chat.html', title=chat_record['title'], messages=messages, timestamp=chat_record['timestamp'])
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
