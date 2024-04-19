from datetime import datetime
import sqlite3
from flask import Flask, render_template
import json 
import markdown

app = Flask(__name__)

DATABASE = 'webui.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    query = """
    SELECT c.id, c.title, c.timestamp, u.name as user_name
    FROM chat c
    JOIN user u ON c.user_id = u.id
    """
    chats = conn.execute(query).fetchall()
    conn.close()
    chats = [{
        'id': chat['id'],
        'title': chat['title'],
        'timestamp': datetime.fromtimestamp(int(chat['timestamp'])).strftime('%y-%m-%d %H:%M'),
        'user_name': chat['user_name']
    } for chat in chats]
    return render_template('index.html', chats=chats)


@app.route('/chat/<id>')
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
