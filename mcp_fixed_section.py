import openai
from openai_key import OPENAI_API_KEY
import json

# Load the current courses for the user's major
with open("current_courses.json", "r", encoding="utf-8") as f:
    courses = json.load(f)

# Semester mapping
sem_list = {
    'fall2025': 1,
    'spring2026': 2,
    'summer2026': 3,
    'fall2026': 4,
    'spring2027': 5,
    'summer2027': 6,
    'fall2027': 7,
    'spring2028': 8,
    'summer2028': 9
}

openai.api_key = OPENAI_API_KEY

def get_course_code_from_name(name):
    name = name.lower().strip()
    for code, data in courses.items():
        if name in data['name'].lower() or name == code.lower():
            return code
    # Fuzzy match: try partial
    for code, data in courses.items():
        if name in data['name'].lower():
            return code
    return None

def prompt_engineering(user_input, completed_semesters):
    # Build a list of all courses and their codes
    course_list = "\n".join([f"{code}: {data['name']}" for code, data in courses.items()])
    semester_list = "\n".join([f"{k}: {v}" for k, v in sem_list.items()])
    prompt = f"""
You are an assistant for a university course scheduler. 
You will be given a user request to fix a course in a specific semester. 
You have access to the following course codes and names:

{course_list}

Semester mapping (use the number):
{semester_list}

The user will say something like: "I want to do Artificial Intelligence in spring 2027".
You must:
- Find the course code for the course name mentioned.
- Find the semester number for the semester mentioned.
- The final semester number is: semester_number + completed_semesters (completed_semesters is {completed_semesters}).
- Output ONLY a Python function call in this format:
add_fixed_course('COURSE_CODE', SEMESTER_NUMBER)

Do not output anything else.
Here is the user request:
\"\"\"{user_input}\"\"\"
"""
    return prompt

def call_openai(user_input, completed_semesters):
    prompt = prompt_engineering(user_input, completed_semesters)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that outputs only Python function calls as instructed."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,
        temperature=0
    )
    return response['choices'][0]['message']['content']

if __name__ == "__main__":
    completed_semesters = int(input("Enter the number of completed semesters: "))
    user_input = input("Enter your request (e.g., 'I want to do Artificial Intelligence in spring 2027'): ")
    result = call_openai(user_input, completed_semesters)
    print("Model output:")
    print(result)
