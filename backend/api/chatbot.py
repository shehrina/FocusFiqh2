import logging
from openai import OpenAI
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=openai_key)

def analyze_kushu_index(kushu_index, aspect):
    try:
        print(f"Analyzing khushu index: {kushu_index}, Aspect: {aspect}")  
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[ 
                {
                    "role": "system",
                    "content": "You are an expert in Islamic spiritual mindfulness and prayer. Based on the provided khushu index, "
                               "analyze how the user can improve their {aspect}. Provide actionable and practical advice from Sharia."
                },
                {
                    "role": "user",
                    "content": f"My khushu index is {kushu_index}. What can I improve about {aspect}?"
                }
            ],
            max_tokens=150
        )
        print(f"Response received: {response}")  
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error during khushu index analysis: {e}")
        return None


def generate_response(text):
    try:
        print(f"Generating response for user question: {text}")  
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[ 
                {
                    "role": "system", 
                    "content": "You are a helpful assistant. Answer the user's question in a clear and concise manner."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            max_tokens=150
        )
        print(f"Response generated: {response}")  
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return None


def chat_with_user():
    try:
        kushu_index = input("Please enter your khushu index (e.g., 1-10): ")
        aspect = input("Which aspect would you like to improve ? ")

        khushu_advice = analyze_kushu_index(kushu_index, aspect)
        if khushu_advice:
            print(f"Advice on improving your {aspect}: {khushu_advice}")
        else:
            print("Sorry, there was an error retrieving advice.")
     
        while True:
            user_question = input("Do you have any other questions? (type 'exit' to stop): ")
            if user_question.lower() == 'exit':
                break
            else:
                response = generate_response(user_question)
                print(f"Answer: {response}")
    except Exception as e:
        logging.error(f"Error during user interaction: {e}")
        print("An error occurred, please try again.")


chat_with_user()
