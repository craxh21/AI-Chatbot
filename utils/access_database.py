import sqlite3
from flask import request, jsonify

def search_knowledge_base(query):
    connection = sqlite3.connect('models/chatbot.db')
    cursor = connection.cursor()
    cursor.execute("SELECT answer FROM knowledge_base WHERE question LIKE ?", (f"%{query}%",))
    result = cursor.fetchone()
    connection.close()
    return result[0] if result else None
