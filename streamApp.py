from openai import OpenAI
import json
import os
from phoenix.otel import register
import requests
from openinference.instrumentation.openai import OpenAIInstrumentor

# Phoenix API key
phoenix_api_key = "4402d414c66202f090f:9b282ce"
os.environ["PHOENIX_CLIENT_HEADERS"] = "api_key=4402d414c66202f090f:9b282ce"

# configure the Phoenix tracer
tracer_provider = register(
  project_name="my-llm-app", # Default is 'default'
  endpoint="https://app.phoenix.arize.com/v1/traces",
)

OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)

# sidebar setup
with st.sidebar:
    # Title displayed on the side bar
    st.title('Enter your model parameters here')
    # Request OpenAI API key
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    # Check that the key provided starts with sk and has 40 characters
    if not ((openai_api_key.startswith('sk')) and len(openai_api_key) == 51):
        st.warning('Enter a valid API key', icon='⚠️')
    else:
        st.success('Proceed to entering your prompt message!', icon='👉')

# sidebar toggles setup
selected_model = st.sidebar.selectbox('Choose OpenAI models', ['GPT-4', 'GPT-3.5'], key='selected_model')
if selected_model == 'GPT-3.5':
    chosen_model = "gpt-3.5-turbo"
elif selected_model == 'GPT-4':
    chosen_model = "gpt-4"
chosen_temperature = st.sidebar.slider('temperature', min_value=0.01, max_value=5.0, value=1.0, step=0.01)
chosen_top_p = st.sidebar.slider('top_p', min_value=0.01, max_value=1.0, value=1.0, step=0.01)
chosen_max_length = st.sidebar.slider('max_length', min_value=32, max_value=10000, value=2000, step=8)
chosen_number_of_samples = st.sidebar.slider('Number of samples', min_value=1, max_value=3, value=1, step=1)

# main window title setup
st.subheader('Meta Expert')
st.text('Enter a problem or task and have the model')
st.text('consult an array of relevant bot experts on')
st.text('the matter and then give you the best solution')
st.text('based on expert feedback')



# Create a list called "messages" in Streamlit database with an embedded dictionary which has keys "role" and "content".
# These are to be populated by future user interactions, with role specifying whether it is the user or model interacting
# and content documenting the user input or generated output
if "messages" not in st.session_state.keys():
    st.session_state["messages"] = [{"role": "assistant", "content": "Decribe the task or problem you would like me to tackle."}]

# Show the relevant content from the database on the front end
for message in st.session_state.messages[2:]:
    with st.chat_message(message["role"]):
        st.write(message["content"])

#Make a button which clears the conversation and starts a new chat
def clear_chat_history():
    st.session_state["messages"] = [{"role": "assistant", "content": "Decribe the task or problem you would like me to tackle."}]
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)


def back_end_prompt(user_input):
    system_prompt = """
You are Meta-Expert, an extremely clever expert with the unique ability to collaborate with multiple experts (such as Expert Problem Solver, Expert Mathematician, Expert Essayist, etc.) to tackle any task and solve any complex problems. Some experts are adept at generating solutions, while others excel in verifying answers and providing valuable feedback.

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
Each interaction is treated as an isolated event, so include all relevant details in every call. The experts cannot communicate with each other. The experts cannot pass on their outputs to each other. The experts can only work in isolation from one another. 
 
Note that you also have special access to Expert Python, which has the unique ability to generate and execute Python code given natural-language instructions. Expert Python is highly capable of crafting code to perform complex calculations when given clear and precise directions. You might therefore want to use it especially for computational tasks.

Refrain from repeating the very same questions to experts. Examine their responses carefully and seek clarification if required, keeping in mind they don't recall past interactions.

Return your output only in form of python dictionary. Do not include any explanations, notes, or natural language before or after the dictionary. The dictionary should be valid Python syntax that could be directly parsed by json.loads().

You must always consult with at least three different experts, even if the task seems simple enough for one expert to handle. Each expert should focus on a different aspect of the problem.
"""
    user_prompt = """
Generate a list of expert_request functions to deliver on the task described under the heading "Task". Consider the list of experts you deem necessary to execute on the task described under the heading "Task". Append detailed instructions to each expert on what they should execute in order to help you as the Meta-Expert to deliver on the overall task. 
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
    }}
Your response must be ONLY the Python dictionary. Do not include any explanations, notes, markdown formatting, or natural language. The dictionary must be valid Python syntax that could be directly parsed by json.loads().

# Task:""" + user_input
    return system_prompt + user_prompt

#Reach out to OpenAI, generate content and show the content to the user
def OpenAI_call(usr_prompt):
    client = OpenAI(api_key=openai_api_key) # Initialize the OpenAI client

    if len(st.session_state.messages) == 1: #apply the backend prompt to the users input, but only on their first input
        st.session_state.messages.append({"role": "user", "content": back_end_prompt(usr_prompt)})
    else:
        st.session_state.messages.append({"role": "user", "content": str((usr_prompt))})
