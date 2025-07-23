from flask import redirect, url_for
from flask import Flask, jsonify, render_template, request
from scheduler import CourseScheduler
from scheduler_data import plans, time_data
from fall25_courses_data import fall25_courses
#import io
#import sys
import gurobipy as gp
from gurobipy import GRB
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()

# Robustly load the OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    try:
        from openai_key import OPENAI_API_KEY as api_key_from_file
        api_key = api_key_from_file
        print("Loaded API key from openai_key.py")
    except (ImportError, ModuleNotFoundError):
        raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in your .env file or create an openai_key.py with OPENAI_API_KEY = 'your-key'.")

client = OpenAI(api_key=api_key)


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    plan = []
    first_semester_courses = []
    next_output = None

    if request.method == 'POST':
        major_index = int(request.form['major'])
        completed_raw = request.form['completed']
        completed_semesters = int(request.form['completed_semesters'])

        completed_set = set(code.strip() for code in completed_raw.split(',') if code.strip())
        courses = plans[major_index]
        print(completed_set)


        scheduler = CourseScheduler(
            courses=courses,
            completed=completed_set,
            required=set(courses.keys()),
            max=18,
            min=12,
            semesters=12,
            starting=completed_semesters + 1
        )

        model = scheduler.build_model3(alpha=0, beta=0, gamma=80, delta=30)
        model.optimize()
        #scheduler.get_full_solution()
        # for output
        result_dict = {}
        for (course, sem), var in scheduler.y.items():
            if var.X > 0.5:
                result_dict.setdefault(sem, []).append(course)
                if sem == completed_semesters + 1:
                    first_semester_courses.append(course)
        # Transform plan to structured format for frontend
        plan = []
        # Build a reverse map for prerequisites (unlocks)
        unlocks_map = {code: [] for code in courses}
        for c, info in courses.items():
            for prereq in info.get('prerequisites', []):
                if prereq in unlocks_map:
                    unlocks_map[prereq].append(c)
        for sem, course_codes in sorted(result_dict.items()):
            semester_courses = []
            for code in course_codes:
                course_info = courses.get(code, {})
                semester_courses.append({
                    "code": code,
                    "name": course_info.get("name", code),
                    "credits": course_info.get("credits", 0),
                    "prerequisites": course_info.get("prerequisites", []),
                    "unlocks": unlocks_map.get(code, [])
                })
            plan.append({
                "number": sem,
                "credits": sum(c["credits"] for c in semester_courses),
                "courses": semester_courses
            })
        # Calculate stats for the plan
        total_semesters = len(plan)
        total_courses = sum(len(sem['courses']) for sem in plan)
        total_credits = sum(sem['credits'] for sem in plan)
        avg_credits_per_semester = round(total_credits / total_semesters, 2) if total_semesters else 0

        return render_template(
            'plan.html',
            plan=plan,
            total_semesters=total_semesters,
            total_courses=total_courses,
            total_credits=total_credits,
            avg_credits_per_semester=avg_credits_per_semester,
            first_semester_courses=first_semester_courses,
            major_index=major_index,
            completed_raw=completed_raw,
            completed_semesters=completed_semesters
        )

    return render_template('index.html')
@app.route('/next_semester', methods=['POST', 'GET'])
def next_semester():
    if request.method == 'GET':
        # Show preferences form only
        return render_template(
            'schedule.html',
            preferences_submitted=False,
            all_timetables=None,
            solution_count=0,
            num_solutions=0,
            major_index=0,
            completed_raw='',
            registered_raw='',
            lab_count=0,
            days_preferred=['Mon', 'Tue', 'Wed', 'Thu'],
            start_hour=9,
            start_ampm='AM',
            end_hour=8,
            end_ampm='PM',
            avoid_gaps=False,
            time_data=fall25_courses
        )

    # POST: check if preferences are submitted
    major_index = int(request.form.get('major', 0))
    completed_raw = request.form.get('completed', '')
    completed_set = set(code.strip() for code in completed_raw.split(',') if code.strip())
    registered_raw = request.form.get('registered', '')
    registered_set = set(code.strip() for code in registered_raw.split(',') if code.strip())
    courses = plans[major_index]

    # Parse fixed_sections and fixed_labs from form (JSON strings)
    import json
    fixed_sections = request.form.get('fixed_sections', '{}')
    fixed_labs = request.form.get('fixed_labs', '{}')
    try:
        fixed_sections = json.loads(fixed_sections)
    except Exception:
        fixed_sections = {}
    try:
        fixed_labs = json.loads(fixed_labs)
    except Exception:
        fixed_labs = {}
    

    # Preferences
    days_preferred = request.form.getlist('days_preferred') or ['Mon', 'Tue', 'Wed', 'Thu']
    start_hour = int(request.form.get('start_hour', 9))
    start_ampm = request.form.get('start_ampm', 'AM')
    end_hour = int(request.form.get('end_hour', 8))
    end_ampm = request.form.get('end_ampm', 'PM')
    avoid_gaps = 'avoid_gaps' in request.form
    preferences_submitted = bool(days_preferred or request.form.get('start_hour') or request.form.get('end_hour') or 'avoid_gaps' in request.form)

    if not preferences_submitted:
        # Show preferences form only
        return render_template(
            'schedule.html',
            preferences_submitted=False,
            all_timetables=None,
            solution_count=0,
            num_solutions=0,
            major_index=major_index,
            completed_raw=completed_raw,
            registered_raw=registered_raw,
            lab_count=0,
            fixed_sections=fixed_sections,
            fixed_labs=fixed_labs,
            days_preferred=days_preferred,
            start_hour=start_hour,
            start_ampm=start_ampm,
            end_hour=end_hour,
            end_ampm=end_ampm,
            avoid_gaps=avoid_gaps,
            time_data=fall25_courses
        )

    # Use model 2 for timetable generation
    scheduler = CourseScheduler(
        courses=fall25_courses,  # Use time_data for sections/times
        completed=completed_set,
        required=set(courses.keys())
    )
    desired_courses = list(registered_set)
    print('desired_courses passed to build_model2:', desired_courses)
    print('fixed_sections:', fixed_sections)
    print('fixed_labs:', fixed_labs)
    scheduler.build_model2(desired_courses=desired_courses, fixed_sections=fixed_sections, fixed_labs=fixed_labs)
    # Set Gurobi parameters for multiple solutions
    scheduler.model2.setParam(gp.GRB.Param.PoolSearchMode, 2)
    scheduler.model2.setParam(gp.GRB.Param.PoolSolutions, 50)
    scheduler.model2.optimize()

    # Assign a color per course for timetable
    import random
    color_palette = ['#3182ce', '#38a169', '#e53e3e', '#d69e2e', '#805ad5', '#319795', '#f56565', '#ed8936', '#ecc94b', '#48bb78', '#4299e1', '#9f7aea']
    course_colors = {}
    for idx, course in enumerate(desired_courses):
        course_colors[course] = color_palette[idx % len(color_palette)]

    # Extract all solutions from model 2
    num_solutions = scheduler.model2.SolCount
    all_timetables = []
    for sol_idx in range(num_solutions):
        scheduler.model2.params.SolutionNumber = sol_idx
        timetable_courses = []
        for (course, section), var in scheduler.x2.items():
            if var.Xn > 0.5:  # Xn gives value in current solution
                cinfo = scheduler.courses[course]
                secinfo = {}
                is_lab = False
                if 'labs' in cinfo and section in cinfo['labs']:
                    is_lab = True
                if is_lab:
                    secinfo = {'name': section}
                elif 'sections' in cinfo:
                    sections = cinfo['sections']
                    if isinstance(sections, dict):
                        secinfo = sections.get(section, {})
                    elif isinstance(sections, list):
                        for s in sections:
                            if isinstance(s, dict):
                                if (s.get('name') == section) or (s.get('section') == section):
                                    secinfo = s
                                    break
                            elif isinstance(s, str):
                                if s == section:
                                    secinfo = {'name': s}
                                    break
                raw_time = secinfo.get('time')
                if not raw_time:
                    raw_time = secinfo.get('name', '')
                days, start, end = CourseScheduler.parse_time(raw_time) if raw_time else ([], '', '')
                timetable_courses.append({
                    'code': course,
                    'name': cinfo.get('name', course),
                    'section': section,
                    'days': days,
                    'start': start,
                    'end': end,
                    'room': secinfo.get('room', ''),
                    'color': course_colors[course],
                    'raw_time': raw_time,
                })
        # Add 'length' field to each timetable_courses entry using to_minutes
        for entry in timetable_courses:
            start = entry.get('start', '')
            end = entry.get('end', '')
            length = CourseScheduler.to_minutes(end) - CourseScheduler.to_minutes(start)
            entry['length'] = length
        all_timetables.append(timetable_courses)

    # Count labs actually scheduled in this semester (from timetable_courses)
    lab_count = 0
    for course in desired_courses:
        if course in fall25_courses and 'labs' in fall25_courses[course]:
            lab_count += 1

    # Just take the first 10 timetables (default logic)
    top_timetables = all_timetables[:10]

    return render_template(
        'schedule.html',
        all_timetables=top_timetables,
        solution_count=len(top_timetables),
        num_solutions=num_solutions,
        major_index=major_index,
        completed_raw=completed_raw,
        registered_raw=registered_raw,
        lab_count=lab_count,
        preferences_submitted=True,
        days_preferred=days_preferred,
        start_hour=start_hour,
        start_ampm=start_ampm,
        end_hour=end_hour,
        end_ampm=end_ampm,
        avoid_gaps=avoid_gaps,
        time_data=fall25_courses,
        fixed_sections=fixed_sections,
        fixed_labs=fixed_labs
    )


@app.route('/get_courses')
def get_courses():
    major = int(request.args.get('major', 0))
    selected_courses = plans[major]
    result = [{'code': code, 'name': data['name']} for code, data in selected_courses.items()]
    return jsonify(result)


FIXED_COURSES_FILE = "fixed_courses.json"

def load_fixed_courses():
    if not os.path.exists(FIXED_COURSES_FILE):
        return []
    with open(FIXED_COURSES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_fixed_courses(fixed_courses):
    with open(FIXED_COURSES_FILE, "w", encoding="utf-8") as f:
        json.dump(fixed_courses, f)

def add_fixed_course_to_store(course_code, semester):
    fixed_courses = load_fixed_courses()
    if [course_code, semester] not in fixed_courses:
        fixed_courses.append([course_code, semester])
        save_fixed_courses(fixed_courses)

LAST_PLAN_FILE = "last_plan.json"

def load_last_plan():
    if not os.path.exists(LAST_PLAN_FILE):
        return None
    with open(LAST_PLAN_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_last_plan(plan_data):
    with open(LAST_PLAN_FILE, "w", encoding="utf-8") as f:
        json.dump(plan_data, f)

@app.route('/mcp_chat', methods=['POST'])
def mcp_chat():
    import re
    user_input = request.json.get('message')
    completed_semesters = int(request.json.get('completed_semesters', 0))
    major_index = int(request.json.get('major_index', 0))
    completed_raw = request.json.get('completed_raw', '')
    completed_set = set(code.strip() for code in completed_raw.split(',') if code.strip())
    courses = plans[major_index]

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

    def prompt_engineering(user_input, completed_semesters):
        course_list = "\n".join([f"{code}: {data['name']}" for code, data in courses.items()])
        semester_list = "\n".join([f"{k}: {v}" for k, v in sem_list.items()])
        prompt = f"""
You are an assistant for a university course scheduler.
You will be given a user request to fix a course in a specific semester, set max credits, or set graduation timing.
You have access to the following course codes and names:

{course_list}

Semester mapping (use the number):
{semester_list}

You can also handle these special user requests:
- If the user says they want a maximum number of credits per semester (e.g., 'no more than 16 credits'), output set_max_credits(NUM) with the number.
- If the user says they want to graduate early (e.g., 'I want to graduate in summer 2027'), output set_total_semesters(NUM) where NUM = completed_semesters + the semester number for the requested graduation term (from the semester mapping).
- If the user says they want to graduate late, output set_graduate_late().
- If you cannot find a solution, do not output anything else.

For fixing a course, output ONLY a Python function call in this format:
add_fixed_course('COURSE_CODE', SEMESTER_NUMBER)

You may output multiple function calls, one per line, for multiple requests.
Here is the user request:
'{user_input}'
"""
        return prompt

    prompt = prompt_engineering(user_input, completed_semesters)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that outputs only Python function calls as instructed."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200,
        temperature=0
    )
    model_output = response.choices[0].message.content

    # Defaults
    max_credits = 18
    total_semesters = 12
    delta = 30
    fixed_courses = load_fixed_courses()
    new_fixed_courses = []
    found_special = False

    # Parse all lines for commands
    for line in model_output.splitlines():
        line = line.strip()
        # set_max_credits(NUM)
        m = re.match(r"set_max_credits\((\d+)\)", line)
        if m:
            max_credits = int(m.group(1))
            found_special = True
        # set_total_semesters(NUM)
        m = re.match(r"set_total_semesters\((\d+)\)", line)
        if m:
            total_semesters = int(m.group(1))
            found_special = True
        # set_graduate_late()
        if line.startswith("set_graduate_late()"):
            total_semesters = 15
            delta = 0
            found_special = True
        # add_fixed_course('CODE', SEM)
        m = re.match(r"add_fixed_course\(['\"](\w+)['\"],\s*(\d+)\)", line)
        if m:
            code = m.group(1)
            sem = int(m.group(2))
            new_fixed_courses.append([code, sem])

    # Store new fixed courses
    for code, sem in new_fixed_courses:
        add_fixed_course_to_store(code, sem)
    # Always reload all fixed courses
    all_fixed_courses = load_fixed_courses()

    # Rebuild the scheduler and apply all fixed courses and special params
    scheduler = CourseScheduler(
        courses=courses,
        completed=completed_set,
        required=set(courses.keys()),
        max=max_credits,
        min=12,
        semesters=total_semesters,
        starting=completed_semesters + 1
    )
    model = scheduler.build_model3(alpha=0, beta=0, gamma=80, delta=delta)
    for code, sem in all_fixed_courses:
        scheduler.add_fixed_course(code, sem)
    model.optimize()

    # Check for infeasibility
    if model.status == gp.GRB.INFEASIBLE:
        last_plan = load_last_plan()
        msg = "No solution found for your request. Showing your previous plan."
        if last_plan:
            rendered_plan = render_template(
                'plan.html',
                **last_plan
            )
            return jsonify({"success": False, "error": msg, "plan_html": rendered_plan})
        else:
            return jsonify({"success": False, "error": msg, "plan_html": ""})

    # Build the new plan as in your main route
    result_dict = {}
    for (course, sem), var in scheduler.y.items():
        if var.X > 0.5:
            result_dict.setdefault(sem, []).append(course)
    plan = []
    unlocks_map = {code: [] for code in courses}
    for c, info in courses.items():
        for prereq in info.get('prerequisites', []):
            if prereq in unlocks_map:
                unlocks_map[prereq].append(c)
    for sem, course_codes in sorted(result_dict.items()):
        semester_courses = []
        for code in course_codes:
            course_info = courses.get(code, {})
            semester_courses.append({
                "code": code,
                "name": course_info.get("name", code),
                "credits": course_info.get("credits", 0),
                "prerequisites": course_info.get("prerequisites", []),
                "unlocks": unlocks_map.get(code, [])
            })
        plan.append({
            "number": sem,
            "credits": sum(c["credits"] for c in semester_courses),
            "courses": semester_courses
        })
    total_semesters = len(plan)
    total_courses = sum(len(sem['courses']) for sem in plan)
    total_credits = sum(sem['credits'] for sem in plan)
    avg_credits_per_semester = round(total_credits / total_semesters, 2) if total_semesters else 0

    # Save this plan for fallback
    plan_data = dict(
        plan=plan,
        total_semesters=total_semesters,
        total_courses=total_courses,
        total_credits=total_credits,
        avg_credits_per_semester=avg_credits_per_semester,
        first_semester_courses=plan[0]['courses'] if plan else [],
        major_index=major_index,
        completed_raw=completed_raw,
        completed_semesters=completed_semesters
    )

    save_last_plan(plan_data)

    # Render the new plan HTML
    rendered_plan = render_template(
        'plan.html',
        **plan_data
    )
    return jsonify({"success": True, "raw": model_output, "plan_html": rendered_plan})


if __name__ == '__main__':
    app.run(debug=True)
