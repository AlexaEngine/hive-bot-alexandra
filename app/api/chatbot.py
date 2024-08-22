import openai
from app.config import OPENAI_API_KEY, logger

# Set the OpenAI API key
openai.api_key = OPENAI_API_KEY

async def get_chatbot_response(prompt):
    """Get a response from the GPT model based on the provided prompt."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            n=1,
            temperature=0.5,
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        logger.error(f"Error during OpenAI API call: {e}")
        return "Sorry, I'm having trouble processing your request right now. Please try again later."
