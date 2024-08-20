import openai
from dotenv import load_dotenv
import os
import logging

# Load environment variables from a .env file
load_dotenv()

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Retrieve the OpenAI API key from the environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

if openai.api_key is None:
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it in your .env file or system environment.")

try:
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Welcome to HiveAI Bot. I am here to help you with your queries. How can I assist you today?"},
            {"role": "user", "content": "Translate the following English text to French: 'Hello, how are you?'"}
        ],
        max_tokens=60
    )

    # Extract and print the response
    print(response.choices[0].message['content'].strip())

except openai.error.OpenAIError as e:
    logger.error(f"An error occurred with OpenAI API: {e}")
