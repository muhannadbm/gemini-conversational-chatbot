import os
from dotenv import load_dotenv
from google import genai

# Load environment variables from .env file
load_dotenv()

# Get API key and model from environment variables
API_KEY = os.environ.get("GEN_AI_API_KEY")
MODEL_NAME = os.environ.get("GEN_AI_MODEL")

if not API_KEY:
    raise ValueError("GEN_AI_API_KEY is not set in the environment.")
if not MODEL_NAME:
    raise ValueError("GEN_AI_MODEL is not set in the environment.")

client = genai.Client(api_key=API_KEY)


def _history_for_api(memory):
    history = []
    for turn in memory:
        role = "model" if turn["role"] == "assistant" else "user"
        history.append({"role": role, "parts": [{"text": turn["content"]}]})
    return history


def gen_ai_assistant(memory):
    """Takes conversation history as memory and gets a response from the GenAI chat model."""
    prior = memory[:-1]
    user_message = memory[-1]["content"]
    chat = client.chats.create(model=MODEL_NAME, history=_history_for_api(prior))
    response = chat.send_message(user_message)
    return response.text or ""

def main():
    memory = []
    while True:
        user_input = input("I am your AI Assistant. How can I help you today? (type 'quit' to exit) ")
        if user_input.strip().lower() == "quit":
            print("Goodbye!")
            break
        memory.append({"role": "user", "content": user_input})
        response = gen_ai_assistant(memory)
        memory.append({"role": "assistant", "content": response})
        print("--------------------------------")
        print(response)

if __name__ == "__main__":
    main()