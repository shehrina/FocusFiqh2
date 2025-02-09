import logging
from openai import OpenAI
import os
import pandas as pd

# Initialize OpenAI client with API key directly
client = OpenAI(api_key="")

def analyze_kushu_index(kushu_index, aspect):
    try:
        print(f"Analyzing khushu index: {kushu_index}, Aspect: {aspect}")  
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[ 
                {
                    "role": "system",
                    "content": "You are an expert in Islamic spiritual mindfulness and prayer. Based on the provided khushu index, "
                               "analyze how the user can improve their {aspect}. Provide actionable and practical advice from Sharia. However, keep it brief unless user mentions so."
                },
                {
                    "role": "user",
                    "content": f"My khushu index is {kushu_index}. What can I improve about {aspect}?"
                }
            ],
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error during khushu index analysis: {e}")
        return None

def generate_response(text, conditions=None):
    try:
        print(f"Generating response for user question: {text}, Conditions: {conditions}")
        
        # Get the user's khushu index
        khushu_index = get_average_khushu_index()
        
        # Customize system message based on conditions and khushu index
        system_message = (
            "You are an expert in Islamic spiritual mindfulness and prayer, specializing in helping individuals "
            "with various conditions maintain focus during prayer. "
        )
        
        if conditions and len(conditions) > 0:
            conditions_str = ", ".join(conditions)
            system_message += (
                f"\nThe user has the following conditions: {conditions_str}. "
                "Consider how these conditions interact and affect their prayer experience. "
            )
        
        system_message += (
            f"\nThe user's current Khushu (spiritual focus) index is {khushu_index}. "
            "Based on this score and their conditions, provide specific, actionable advice that: "
            "\n1. Addresses their immediate question or concern"
            "\n2. Takes into account their specific conditions and how they might affect their focus"
            "\n3. Suggests practical techniques appropriate for their current khushu level"
            "\n4. Offers encouragement based on their current progress"
            "\nKeep responses concise but personalized."
        )
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[ 
                {
                    "role": "system", 
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            max_tokens=250  # Increased token limit for more detailed responses
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return None

def get_average_khushu_index():
    try:
        csv_path = os.path.join(os.path.dirname(os.getcwd()), 'khushu_results.csv')
        df = pd.read_csv(csv_path)
        average_index = df['Average Khushu Index'].mean()
        return round(average_index, 2)
    except Exception as e:
        logging.error(f"Error reading khushu index from CSV: {e}")
        return None

def chat_with_user():
    try:
        kushu_index = get_average_khushu_index()
        if not kushu_index:
            print("Error reading khushu index from CSV file.")
            return
            
        print(f"Your average khushu index based on historical data is: {kushu_index}")
        aspect = input("Which aspect would you like to improve? ")

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

if __name__ == "__main__":
    chat_with_user()
