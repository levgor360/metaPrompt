from openai import OpenAI
import json
import os
import yaml
import requests
from dotenv import load_dotenv

# TO DO
# Transfer rest of promtps to YAML

# Use this to activate virtual environment
# .\venv\Scripts\activate

# Load .env file
load_dotenv(override=True) 

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("API key not found. Please set the 'OPENAI_API_KEY' environment variable.")

# Load YAML file
with open('prompts.yaml', 'r') as file:
    prompts = yaml.safe_load(file)

# Initialize the OpenAI client
client = OpenAI(api_key=openai_api_key)

# User input variable
user_input = """
You are a mathematics expert, specializing in the fields of geometry and algebra. Compute the Euclidean distance between the points (-2, 5) and (3, 7).
"""

# Function to send a prompt to the OpenAI API
def call_openai_api():
    try:
        # Call the OpenAI API's completion endpoint
        response = client.chat.completions.create(
            model="gpt-4",  # Specify the model to use
            messages=[
                {"role": "system", "content": prompts['system_prompt']},
                {"role": "user", "content": f"{prompts['user_prompt']}".replace("{user_input}", user_input)}],
            temperature=0.7,
            max_tokens=4000,
        )
        return response  # Return the API response

    except Exception as e:
        print(f"Error occurred while calling OpenAI API: {e}")
        return None

response = call_openai_api()

# Print output to terminal
if response:
    print(response.choices[0].message.content)
else:
    print("Failed to get a response from the API.")

# Meta-expert's output is clasified into a JSON dictionary:
expert_requests = json.loads(response.choices[0].message.content)

# Define expert API call
def call_expert_api(expert_name, instructions): #these will later be filled by extracted JSON data
    expert_prompt = {
        "role": "system",
        "content": f"""You are {expert_name}. {prompts['expert_sysPrompt']}"""

    }
    user_message = {"role": "user", "content": instructions}
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[expert_prompt, user_message],
            temperature=0.7,
            max_tokens=3000,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error occurred while calling OpenAI API for {expert_name}: {e}")
        return None

expert_responses = {}  # Create a dictionary to store expert responses

for i, (request_key, request_data) in enumerate(expert_requests.items(), 1): # Creates a counter in the loop to assign them to "expert_advice_N" dictionary key
    try:
        expert_response = call_expert_api(
            request_data['expert'],
            request_data['instructions']
        )
        # Create new key in the format "expert_advice_N"
        new_key = f"expert_advice_{i}" # Assigns to the dictionary key the counter launched by the for loop
        # Parse the response and extract just the advice content
        response_data = json.loads(expert_response)
        expert_responses[new_key] = {
            "expert": request_data['expert'],
            "advice": response_data["expert_advice_1"]["advice"]
        }
    except Exception as e:
        print(f"Unexpected error processing expert API call for expert {request_data['expert']}: {e}")

# print(json.dumps(expert_responses, indent=4))

metaExpert2_userPrompt = ""

for advice_key, advice_data in expert_responses.items():
    metaExpert2_userPrompt += f"Advice from {advice_data['expert']}: '{advice_data['advice']}'\n --- \n"

print(metaExpert2_userPrompt)

# Expert to MetaExpert API call

def meta_expert_call2():
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompts['metaExpert2_sysPrompt'].replace("{user_input}", user_input)},
                {"role": "user", "content": metaExpert2_userPrompt}],
                temperature=0.7,
                max_tokens=4000,
        )
        return response
    except Exception as e:
        print(f"Error when handling second API call to Meta Expert: {e}")
        return None

final_output = meta_expert_call2()

if final_output:
    print(final_output.choices[0].message.content)
else:
    print("Failed to get a response from the 3rd API call.")