
def recognize_intent(user_input):
    intents = {
        "greeting": ["hello", "hi", "hey", "good morning", "good evening"],
        "help": ["help", "assist", "support", "can you help", "guide me"],
        "feedback": ["feedback", "rate", "review", "how was it"],
        "farewell": ["bye", "goodbye", "see you later", "take care"]
    }
    
    user_input = user_input.lower()  # Convert input to lowercase for case-insensitivity

    # Check each intent and match based on keywords
    for intent, keywords in intents.items():
        if any(keyword in user_input for keyword in keywords):
            return intent
    return "unknown"  # Default to 'unknown' if no match is found
