from transformers import pipeline
import logging
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize the model
try:
    # Using a smaller model suitable for conversation
    generator = pipeline('text2text-generation', model='tiiuae/falcon-7b-instruct')
except Exception as e:
    logging.error(f"Error loading model: {e}")
    generator = None

def analyze_kushu_index(kushu_index, aspect):
    try:
        prompt = (f"Pretend that you're Islamic spiritual advisor, provide advice for improving {aspect} "
                 f"in prayer when the kushoo (concentration) level is {kushu_index}/100. "
                 f"Give practical Islamic advice from Sharia.")
        
        response = generator(prompt, max_length=150, min_length=50)
        return response[0]['generated_text'].strip()
    except Exception as e:
        logging.error(f"Error during kushu index analysis: {e}")
        return None

def generate_response(text):
    try:
        prompt = (f"Respond as if you were Islamic sheikh {text}")
        response = generator(prompt, max_length=150, min_length=30)
        return response[0]['generated_text'].strip()
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return None

if __name__ == "__main__":
    # Example: Analyze khushu index for "sujjud"
    kushu_index = 50  
    aspect = "sujjud"
    
    advice = analyze_kushu_index(kushu_index, aspect)
    print("Khushu Advice:", advice)

    # Example: Allow user to ask follow-up questions
    user_question = input("Feel free to ask any questions: ")
    response = generate_response(user_question)
    print("Response:", response)