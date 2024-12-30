from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from models.database import db, Conversation, FAQ
from utils.sanitization import sanitize_input

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot.db'
db.init_app(app)

with app.app_context():
    db.create_all()  # Create tables
    # if not FAQ.query.first():  # Avoid duplicating FAQs
    #     db.session.add(FAQ(question="What is this?", answer="This is a chatbot."))
    #     db.session.add(FAQ(question="How does it work?", answer="You ask questions, I respond."))
    #     db.session.commit()
    #     print("FAQ data has been populated.")

@app.route('/chat', methods=['POST'])
def chat():
    user_input = sanitize_input(request.json.get('message', ''))
    if not user_input:
        return jsonify({"reply": "Invalid input. Please try again."})

    # Check for matching FAQ
    faq = FAQ.query.filter(FAQ.question.ilike(f"%{user_input}%")).first()
    if faq:
        response_text = faq.answer
    else:
        response_text = "Sorry, I don't have an answer for that."

    # Save to database
    new_entry = Conversation(user_input=user_input, bot_response=response_text)
    db.session.add(new_entry)
    db.session.commit()

    return jsonify({
        "input": user_input,
        "reply": response_text })


if __name__ == '__main__':
    app.run(debug=True)
