import sqlite3

# Step 1: Create or connect to the database
connection = sqlite3.connect('chatbot.db')

# Step 2: Create a cursor to execute SQL commands
cursor = connection.cursor()

# Step 3: Create the knowledge_base table if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS knowledge_base (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL
)
''')

# Step 4: Insert sample FAQs
faqs = [
    ("What is your name?", "I am your AI chatbot, here to assist you!"),
    ("How can I reset my password?", "To reset your password, click on 'Forgot Password' on the login page."),
    ("What is the weather like today?", "I recommend checking a weather app for up-to-date information!"),
]

cursor.executemany('INSERT INTO knowledge_base (question, answer) VALUES (?, ?)', faqs)

# Step 5: Save changes and close the connection
connection.commit()
connection.close()

print("Knowledge base setup complete and populated with sample data!")
