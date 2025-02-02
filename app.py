from flask import Flask, request, jsonify, render_template, session
from flask_sqlalchemy import SQLAlchemy
from models.database import db, Conversation, FAQ
from utils.sanitization import sanitize_input
from utils.sentiment import analyze_sentiment
from fuzzywuzzy import process
from utils.intent_recognition import recognize_intent
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from utils.seggestions import generate_suggestions
from flask_session import Session
from utils.personalities import personalities
from utils.access_database import search_knowledge_base
from flask_caching import Cache

app = Flask(__name__)
CORS(app)  # Allow CORS for the Flask app
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow CORS for SocketIO on initialization
# cors_allowed_origins="*": This allows requests from all origins.
# For stricter security, you can specify a list of allowed origins (e.g., ["http://127.0.0.1:5000", "http://localhost:5000"]).
app.config['SECRET_KEY'] = 'your_secret_key'  # Required for session to work
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot.db'
db.init_app(app)

# Configure Flask-Caching
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

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

@app.route('/set-personality', methods=['POST'])
def set_personality():
    # Get the selected personality from user input
    selected_personality = request.json.get('personality', 'friendly')
    
    if selected_personality not in personalities:
        return jsonify({"error": "Invalid personality selected."}), 400
    
    # Store the selected personality in session
    session['personality'] = selected_personality
    return jsonify({"message": f"Personality set to {selected_personality}!"})

#reply as per the personality user selects 
@app.route('/chat2', methods=['POST'])
def chat2():
    user_input = request.json.get('message', '')
    if not user_input:
        return jsonify({"reply": "Please provide a message."})

    # Get the current personality (defaults to 'friendly' if not set)
    current_personality = session.get('personality', 'friendly')
    personality_responses = personalities.get(current_personality, personalities['friendly'])

    # Example logic to handle different user inputs
    if "hello" in user_input.lower() or "hi" in user_input.lower():
        response_text = personality_responses['greeting']
    elif "bye" in user_input.lower() or "goodbye" in user_input.lower():
        response_text = personality_responses['farewell']
    else:
        response_text = personality_responses['help']

    return jsonify({"reply": response_text})

@app.route('/search_kb_with_caching', methods =['POST'])
def search_kb_with_caching():
    user_input = sanitize_input(request.json.get('message', ''))
    if not user_input:
        return jsonify({"reply": "Invalid input. Please try again."})

    #search for cach
    # Check cache first
    cached_response = cache.get(user_input)
    if cached_response:
        return jsonify({"reply": cached_response})

    #search for the ans in knoledge base
    kb_ans = search_knowledge_base(user_input)
    if kb_ans:
        cache.set(user_input, kb_ans, timeout=300)  # Cache for 5 minutes
        return jsonify({"reply":kb_ans})
    
    # Default response if no match is found
    default_reply= "I'm sorry, I couldn't find an answer to that. Can you try rephrasing?"
    cache.set(user_input, default_reply, timeout=300)#Stores the user's input and the default reply in the cache.
    #If the user asks the same question again, the bot can quickly provide the default reply without re-processing the input.
    return jsonify({"reply": default_reply})


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

    # Generate suggestions
    suggestions = generate_suggestions(intent)

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

    return jsonify({"intent": intent, "reply": response_text, "suggestions": suggestions})

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
