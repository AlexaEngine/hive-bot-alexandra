import openai
from app.config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def get_chatbot_response(prompt):
    try:
        response = openai.Completion.create(
            engine="davinci-codex",  # Specify the engine to use (e.g., davinci, curie, etc.)
            prompt=prompt,
            max_tokens=150,  # You can adjust the max tokens as needed
            n=1,
            stop=None,
            temperature=0.5,
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"An error occurred: {e}"
