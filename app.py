from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from models.database import db, Conversation, FAQ
from utils.sanitization import sanitize_input
from utils.sentiment import analyze_sentiment
from fuzzywuzzy import process
from utils.intent_recognition import recognize_intent
from flask_cors import CORS
from flask_socketio import SocketIO, emit

app = Flask(__name__)
CORS(app)  # Allow CORS for the Flask app
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow CORS for SocketIO on initialization
# cors_allowed_origins="*": This allows requests from all origins.
# For stricter security, you can specify a list of allowed origins (e.g., ["http://127.0.0.1:5000", "http://localhost:5000"]).

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot.db'
db.init_app(app)

with app.app_context():
    db.create_all()  # Create tables
    # if not FAQ.query.first():  # Avoid duplicating FAQs
    #     db.session.add(FAQ(question="What is this?", answer="This is a chatbot."))
    #     db.session.add(FAQ(question="How does it work?", answer="You ask questions, I respond."))
    #     db.session.commit()
    #     print("FAQ data has been populated.")

@app.route('/')
def index():
    return render_template('chat.html')
    # return "WebSocket-based chat is working!"

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

#usg fuzzy logic 
@app.route('/fuzzy_faq', methods=['POST'])
def fuzzy_faq():
    """
    Endpoint to find the best FAQ match for a user's query using fuzzy matching.
    """
    user_input = request.json.get('message', '').strip()
    if not user_input:
        return jsonify({"reply": "Invalid input. Please provide a query."}), 400
    
    #fetch faqs
    faqs = FAQ.query.all()
    faq_questions = [faq.question for faq in faqs]

    # Perform fuzzy matching
    best_match, score = process.extractOne(user_input, faq_questions)

    # Set a threshold for matching accuracy
    threshold = 70
    if score > threshold:
        # Find the matching FAQ in the database
        matching_faq = next(faq for faq in faqs if faq.question == best_match)
        response_text = matching_faq.answer
    else:
        response_text = "Sorry, I couldn't find a relevant answer. Please try rephrasing your question."

    return jsonify({
        "query": user_input,
        "best_match": best_match,
        "match_score": score,
        "reply": response_text
    })

#sentiment analysis
@app.route('/sentiment', methods=['POST'])
def sentiment():
    user_input = sanitize_input(request.json.get('message', ''))
    if not user_input:
        return jsonify({"reply": "Invalid input. Please try again."})

    # Analyze sentiment
    sentiment = analyze_sentiment(user_input)

    # Choose response based on sentiment
    if sentiment > 0:
        response_text = "I can sense you're in a good mood! How can I help?"
    elif sentiment < 0:
        response_text = "It seems like you're upset. Can I help you with something?"
    else:
        response_text = "Let's chat! How can I assist you today?"

    # Save conversation to database
    new_entry = Conversation(user_input=user_input, bot_response=response_text)
    db.session.add(new_entry)
    db.session.commit()

    return jsonify({"reply": response_text})

@app.route('/intent-recognition', methods=['POST'])
def intent_recognition():
    user_input = sanitize_input(request.json.get('message', ''))
    if not user_input:
        return jsonify({"reply": "Invalid input. Please try again."})

    # Recognize the user's intent
    intent = recognize_intent(user_input)

    # Respond based on recognized intent
    if intent == "greeting":
        response_text = "Hello! How can I assist you today?"
    elif intent == "help":
        response_text = "I can help you with various tasks. What do you need assistance with?"
    elif intent == "feedback":
        response_text = "Thank you for your feedback! How can I improve?"
    elif intent == "farewell":
        response_text = "Goodbye! Have a great day!"
    else:
        response_text = "I'm not sure what you mean. Can you clarify?"

    return jsonify({"intent": intent, "reply": response_text})

# WebSocket event to handle incoming messages
@socketio.on('message')
def handle_message(message):
    print(f"Received message: {message}")  # Debug: Check if the message is being received

    # Sanitize and process the message
    user_input = sanitize_input(message)
    if not user_input:
        emit('response', "Invalid input. Please try again.")
        return
    
    # Recognize intent (reuse the function you created earlier)
    intent = recognize_intent(user_input)

    # Send a response based on intent
    if intent == "greeting":
        response_text = "Hello! How can I assist you today?"
    elif intent == "help":
        response_text = "I can help you with various tasks. What do you need assistance with?"
    elif intent == "feedback":
        response_text = "Thank you for your feedback! How can I improve?"
    elif intent == "farewell":
        response_text = "Goodbye! Have a great day!"
    else:
        response_text = "I'm not sure what you mean. Can you clarify?"

    # Emit the response back to the client
    emit('response', response_text)

if __name__ == '__main__':
    socketio.run(app, debug=True)
