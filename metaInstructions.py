from openai import OpenAI
import json
import os
## print("Current working directory:", os.getcwd())
import requests
from dotenv import load_dotenv

# Load .env file
load_dotenv(override=True) 

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("API key not found. Please set the 'OPENAI_API_KEY' environment variable.")

# Initialize the OpenAI client
client = OpenAI(api_key=openai_api_key)

# Initial meta prompt; system & user
system_prompt = """You are Meta-Expert, an extremely clever expert with the unique ability to collaborate with multiple experts (such as Expert Problem Solver, Expert Mathematician, Expert Essayist, etc.) to tackle any task and solve any complex problems. Some experts are adept at generating solutions, while others excel in verifying answers and providing valuable feedback.

Note that you also have special access to Expert Python, which has the unique ability to generate and execute Python code given natural-language instructions. Expert Python is highly capable of crafting code to perform complex calculations when given clear and precise directions. You might therefore want to use it especially for computational tasks.

As Meta-Expert, your role is to oversee the communication between the experts, effectively using their skills to answer a given question while applying your own critical thinking and verification abilities.

To communicate with an expert, structure your request as a Python dictionary with the following format:
expert_request = {
    'expert_name': 'Expert Name',  # e.g., 'Expert Linguist' or 'Expert Puzzle Solver'
    'instruction': '''Your detailed instruction goes here, including any necessary context and specific requirements'''
}
For example:
expert_request = {
    'expert_name': 'Expert Mathematician',
    'instruction': '''You are a mathematics expert, specializing in the fields of geometry and algebra. Compute the Euclidean distance between the points (-2, 5) and (3, 7).'''
}
```"
 Each interaction is treated as an isolated event, so include all relevant details in every call.
 
Note that you also have special access to Expert Python, which has the unique ability to generate and execute Python code given natural-language instructions. Expert Python is highly capable of crafting code to perform complex calculations when given clear and precise directions. You might therefore want to use it especially for computational tasks.

Refrain from repeating the very same questions to experts. Examine their responses carefully and seek clarification if required, keeping in mind they don't recall past interactions.

Return your output only in form of python dictionary. Do not include any explanations, notes, or natural language before or after the dictionary. The dictionary should be valid Python syntax that could be directly parsed by json.loads().

You must always consult with at least three different experts, even if the task seems simple enough for one expert to handle. Each expert should focus on a different aspect of the problem.

"""

user_prompt = """Generate a list of expert_request functions to deliver on the task described under the heading "Task". Consider the list of experts you deem necessary to execute on the task described under the heading "Task". Append detailed instructions to each expert on what they should execute in order to help you as the Meta-Expert to deliver on the overall task. 
Follow this chain of thought when executing on the task:
1. Analyze the task to be solved in the request described under the heading "Task".
2. Break down the task into 3 to 5 subcomponents. Do no return these components. Just remember them.
3. Come up with an expert title which would be best fitted to solve each subcomponent
4. Consider what instructions to pass to each expert in order to help you solve the overarching task
5. Return AT LEAST THREE expert name and their respective instructions in the following format: 
{
    "expert_request_1": {
        "expert": "Expert Name",
        "instructions": "Your detailed instruction goes here."
    },
    "expert_request_2": {
        "expert": "Expert Name",
        "instructions": "Your detailed instruction goes here."
    },
    "expert_request_3": {
        "expert": "Expert Name",
        "instructions": "Your detailed instruction goes here."
    }
Your response must be ONLY the Python dictionary. Do not include any explanations, notes, markdown formatting, or natural language. The dictionary must be valid Python syntax that could be directly parsed by json.loads().

# Task:
You are a mathematics expert, specializing in the fields of geometry and algebra. Compute the Euclidean distance between the points (-2, 5) and (3, 7)."""


# Function to send a prompt to the OpenAI API
def call_openai_api():
    try:
        # Call the OpenAI API's completion endpoint
        response = client.chat.completions.create(
            model="gpt-4",  # Specify the model to use
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}],
            temperature=0.7,  # Adjust creativity level
            max_tokens=4000,  # Adjust token limit as needed
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
    # print(f"\n{expert_prompt}")
    user_message = {"role": "user", "content": instructions}
    # print(f"\n{user_message}")
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

# Process each expert request
# for request_key, request_data in expert_requests.items():
#     expert_response = call_expert_api(
#         request_data['expert'],
#         request_data['instructions']
#     )
#     expert_responses[request_key] = json.loads(expert_response)  # Store the response

for i, (request_key, request_data) in enumerate(expert_requests.items(), 1): # Creates a counter in the loop to assign them to "expert_advice_N" dictionary key
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

print(expert_responses)



# def call_meta_expert_api(responses):
#     meta_expert_prompt = f"""You are Meta-Expert. You have access to the following responses from the experts:

# {json.dumps(responses, indent=4)}

# Your task is to analyze all the provided responses and synthesize them into a coherent, comprehensive final conclusion or solution to the overarching problem described in the task. Carefully verify each expert's response, integrate their findings, resolve any conflicts, and ensure the final answer is accurate and complete.

# Return your final output only as text without any additional formatting or explanations.
# """
#     try:
#         response = client.chat.completions.create(
#             model="gpt-4",
#             messages=[
#                 {"role": "system", "content": ""},
#                 {"role": "user", "content": meta_expert_prompt},
#             ],
#             temperature=0.7,
#             max_tokens=2000,
#         )
#         return response.choices[0].message.content
#     except Exception as e:
#         print(f"Error occurred while calling Meta-Expert API: {e}")
#         return None