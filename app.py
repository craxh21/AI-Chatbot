from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from models.database import db, Conversation

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot.db'
db.init_app(app)

with app.app_context():
    db.create_all()  # Create tables

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '').strip()
    response_text = "This is a basic response!"

    # Save to database
    new_entry = Conversation(user_input=user_input, bot_response=response_text)
    db.session.add(new_entry)
    db.session.commit()

    return jsonify({"reply": response_text})


if __name__ == '__main__':
    app.run(debug=True)
