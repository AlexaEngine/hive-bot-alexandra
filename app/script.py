import openai
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "Welcome to HiveAI Bot. I am here to help you with your queries. How can I assist you today?"},
        {"role": "user", "content": "Translate the following English text to French: 'Hello, how are you?'"}
    ],
    max_tokens=60
)

print(response.choices[0].message['content'].strip())