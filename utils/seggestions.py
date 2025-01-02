def generate_suggestions(intent):
    """Generate suggestions based on the detected intent."""
    suggestions = {
        "greeting": ["Ask about features", "Say goodbye", "Request assistance"],
        "help": ["FAQ: How to reset password", "FAQ: Contact support", "Try: 'Show me account settings'"],
        "feedback": ["Submit your feedback here", "Tell us what you love about the service", "Share any issues you're facing"],
        "farewell": ["Say goodbye", "Come back later", "Check out these resources"],
        "default": ["Try asking about account settings", "Search for 'help'", "Ask about available features"],
    }
    return suggestions.get(intent, suggestions["default"])
