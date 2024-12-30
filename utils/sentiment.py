from textblob import TextBlob

def analyze_sentiment(text):
    # Create a TextBlob object
    blob = TextBlob(text)
    # Get sentiment polarity (-1 to 1, where -1 is negative, 1 is positive)
    return blob.sentiment.polarity
