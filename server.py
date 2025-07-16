from flask import redirect, url_for
from flask import Flask, jsonify, render_template, request
from scheduler import CourseScheduler
from scheduler_data import plans, time_data
#import io
#import sys
import gurobipy as gp
from gurobipy import GRB
import openai
from dotenv import load_dotenv
import os

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

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
            avoid_gaps=False
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
            time_data=time_data
        )

    # Use model 2 for timetable generation
    scheduler = CourseScheduler(
        courses=time_data,  # Use time_data for sections/times
        completed=completed_set,
        required=set(courses.keys())
    )
    desired_courses = list(time_data.keys())
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
    for idx, course in enumerate(time_data.keys()):
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
        if 'labs' in time_data[course]:
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
        time_data=time_data,
        fixed_sections=fixed_sections,
        fixed_labs=fixed_labs
    )


@app.route('/get_courses')
def get_courses():
    major = int(request.args.get('major', 0))
    selected_courses = plans[major]
    result = [{'code': code, 'name': data['name']} for code, data in selected_courses.items()]
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
