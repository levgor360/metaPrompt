from openai import OpenAI
import json
import os
import yaml
import requests
from dotenv import load_dotenv

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

# Expert System Prompt:
expert_sysPrompt = """Follow the instructions given and respond accordingly. Return your output in the format you see below.

Your response must be ONLY the Python dictionary. Do not include any explanations, notes, markdown formatting, or natural language. The dictionary must be valid Python syntax that could be directly parsed by json.loads().

Your output should be a single entry in the following format:

{
    "expert_advice_1": {
        "expert": "Expert Name",
        "advice": "Your detailed instruction goes here."
    }
"""

# Define expert API call
def call_expert_api(expert_name, instructions): #these will later be filled by extracted JSON data
    expert_prompt = {
        "role": "system",
        "content": f"""You are {expert_name}. {expert_sysPrompt}"""

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


# Expert to MetaExpert prompt:
metaExpert2_sysPrompt = f"""
You are a Meta-Expert, an extremely clever expert who receives feedback from multiple experts (such as Expert Problem Solver, Expert Mathematician, Expert Essayist, etc.) to tackle any task and solve any complex problems.

You are tasked with solving the following task / problem:
{user_input}.

As a Meta-Expert, you will be receiving suggestions, recommendations and methodologies from a diverse set of experts on how to solve the task. Your job is use the expert inputs tothe best of your ability to better solve the task. 

Follow this train of thought when using the expert inputs to solve the task:
1. Consider separately each of the expert recommendations, their validity and utility in solving the task. Give a score between one and ten to each expert as to how you would judge their performance. For example, if the expert provided information that is factually incorrect, false or misleading, you will assign a score of zero to that expert. If the expert advice is highly relevant to the task, detailed, insightful and considerate of the nuance that the task demands, then you would assign a score of ten to the expert. Do not output this score, just remember it internally. 
2. Come up with a strategy as to how you will integrate the suggestions of the experts, giving weight to the expert advice in proportion to their performance score. For example, if an expert has a score of zero, you would ignore its advice altogether. If the expert has a score of ten, then you would highly influence the way you choose to satisfy the task in relation to what that expert advised. If multiple experts got high scores, you would consider how you would apply their suggestions in parallel. If two expert advice conflict, then choose the one that is optimal.
3. Present a solution to the problem or the output desired by the user. Speak as a representative of the experts, voicing their reasoning where relevant, but do not mention the experts. Speak as if you embody the experts yourself.
"""

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
                {"role": "system", "content": metaExpert2_sysPrompt},
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