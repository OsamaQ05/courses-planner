from flask import redirect, url_for
from flask import Flask, jsonify, render_template, request
from scheduler import CourseScheduler
from scheduler_data import plans  # Removed time_data import
#import io
#import sys
import gurobipy as gp
from gurobipy import GRB
<<<<<<< Updated upstream
=======
import openai
from dotenv import load_dotenv
import os
import json
from loader import load_fall25_courses

# Load course data from loader once
fall25_time_data = load_fall25_courses()

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
>>>>>>> Stashed changes

app = Flask(__name__)

# Store planned courses for next semester in a global dict (per session/major)
planned_courses_cache = {}

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
        courses = fall25_time_data  # Use loader data for all models
        print(completed_set)

        scheduler = CourseScheduler(
            courses=courses,
            completed=completed_set,
            required=set(courses.keys()),
            max=180,
            min=12,
            semesters=12,  
            starting=completed_semesters + 1
        )

        model = scheduler.build_model3(alpha=0, beta=0, gamma=80, delta=30)
        model.optimize()
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        scheduler.get_full_solution()
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        # for output
        result_dict = {}
        for (course, sem), var in scheduler.y.items():
            if var.X > 0.5:
                result_dict.setdefault(sem, []).append(course)
                if sem == completed_semesters + 1:
                    first_semester_courses.append(course)
        # Save planned courses for next semester in the scheduler instance
        scheduler.planned_courses_next_semester = list(first_semester_courses)
        # Also cache by session/major for use in /next_semester
        planned_courses_cache['planned'] = list(first_semester_courses)

        # Transform plan to structured format for frontend
        plan = []
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
        unlocks_map = {code: [] for code in courses}
        for c, info in courses.items():
            for prereq in info.get('prerequisites', []):
                if prereq in unlocks_map:
                    unlocks_map[prereq].append(c)
>>>>>>> Stashed changes
        for sem, course_codes in sorted(result_dict.items()):
            semester_courses = []
            for code in course_codes:
                course_info = courses.get(code, {})
                semester_courses.append({
                    "code": code,
                    "name": course_info.get("name", code),
                    "credits": course_info.get("credits", 0)
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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
@app.route('/next_semester', methods=['POST'])
def next_semester():
    major_index = int(request.form['major'])
    completed_raw = request.form['completed']
=======
=======
>>>>>>> Stashed changes

@app.route('/next_semester', methods=['POST', 'GET'])
def next_semester():
    if request.method == 'GET':
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

    major_index = int(request.form.get('major', 0))
    completed_raw = request.form.get('completed', '')
>>>>>>> Stashed changes
    completed_set = set(code.strip() for code in completed_raw.split(',') if code.strip())
    registered_raw = request.form['registered']
    registered_set = set(code.strip() for code in registered_raw.split(',') if code.strip())
    # Use loader data for all models
    courses = fall25_time_data

<<<<<<< Updated upstream
<<<<<<< Updated upstream
    # Use model 2 for timetable generation
=======
=======
>>>>>>> Stashed changes
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
    
    days_preferred = request.form.getlist('days_preferred') or ['Mon', 'Tue', 'Wed', 'Thu']
    start_hour = int(request.form.get('start_hour', 9))
    start_ampm = request.form.get('start_ampm', 'AM')
    end_hour = int(request.form.get('end_hour', 8))
    end_ampm = request.form.get('end_ampm', 'PM')
    avoid_gaps = 'avoid_gaps' in request.form
    preferences_submitted = bool(days_preferred or request.form.get('start_hour') or request.form.get('end_hour') or 'avoid_gaps' in request.form)

    if not preferences_submitted:
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
            time_data={},  # No courses shown until planned
        )

    completed_semesters = int(request.form.get('completed_semesters', 0))
    # Use planned courses from cache if available
    planned_courses = planned_courses_cache.get('planned', [])
    print(f"Planned courses for next semester: {planned_courses}")
    # Filter the course data to only include planned courses
    planned_courses_data = {code: fall25_time_data[code] for code in planned_courses if code in fall25_time_data}

    # --- LOGGING START ---
    print("\n=== Model 2 Data Debug ===")
    print(f"Total planned courses: {len(planned_courses_data)}")
    for code, course in list(planned_courses_data.items())[:3]:
        print(f"Course: {code}")
        print(f"  Name: {course.get('name')}")
        print(f"  Credits: {course.get('credits')}")
        print(f"  Sections: {list(course.get('sections', {}).keys())[:3]}")
        print(f"  Labs: {course.get('labs', [])[:3]}")
    print("========================\n")
    # --- LOGGING END ---
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    scheduler = CourseScheduler(
        courses=fall25_time_data,  # Use loader data
        completed=completed_set,
        required=set(planned_courses_data.keys())
    )
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    desired_courses = list(time_data.keys())
    scheduler.build_model2(desired_courses=desired_courses)
=======
=======
>>>>>>> Stashed changes
    desired_courses = planned_courses
    print('fixed_sections:', fixed_sections)
    print('fixed_labs:', fixed_labs)
    scheduler.build_model2(desired_courses=desired_courses, fixed_sections=fixed_sections, fixed_labs=fixed_labs)
    scheduler.planned_courses_next_semester = planned_courses
    # Set Gurobi parameters for multiple solutions
    scheduler.model2.setParam(gp.GRB.Param.PoolSearchMode, 2)
    scheduler.model2.setParam(gp.GRB.Param.PoolSolutions, 50)
>>>>>>> Stashed changes
    scheduler.model2.optimize()

    # Gather schedule info for visualization
    timetable_courses = []
    # Assign a color per course for timetable
    import random
    color_palette = ['#3182ce', '#38a169', '#e53e3e', '#d69e2e', '#805ad5', '#319795', '#f56565', '#ed8936', '#ecc94b', '#48bb78', '#4299e1', '#9f7aea']
    course_colors = {}
    for idx, course in enumerate(planned_courses):
        course_colors[course] = color_palette[idx % len(color_palette)]

<<<<<<< Updated upstream
    for (course, section), var in scheduler.x2.items():
        if var.X > 0.5:
            cinfo = scheduler.courses[course]
            secinfo = {}
            # Check if this section is a lecture or a lab
            is_lab = False
            if 'labs' in cinfo and section in cinfo['labs']:
                is_lab = True
            # Find the section info
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

=======
    # Extract all solutions from model 2
    num_solutions = scheduler.model2.SolCount
    all_timetables = []
    for sol_idx in range(num_solutions):
        scheduler.model2.params.SolutionNumber = sol_idx
        timetable_courses = []
        for (course, section), var in scheduler.x2.items():
            if var.Xn > 0.5:
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
>>>>>>> Stashed changes

    # Count labs actually scheduled in this semester (from timetable_courses)
    lab_count = 0
    for course in planned_courses:
        if 'labs' in fall25_time_data[course]:
            lab_count += 1
            

    # Add 'length' field to each timetable_courses entry using to_minutes
    for entry in timetable_courses:
        start = entry.get('start', '')
        end = entry.get('end', '')
        length = CourseScheduler.to_minutes(end) - CourseScheduler.to_minutes(start)
        entry['length'] = length

    return render_template(
        'schedule.html',
        timetable_courses=timetable_courses,
        major_index=major_index,
        completed_raw=completed_raw,
        registered_raw=registered_raw,
<<<<<<< Updated upstream
        lab_count=lab_count
=======
        lab_count=lab_count,
        preferences_submitted=True,
        days_preferred=days_preferred,
        start_hour=start_hour,
        start_ampm=start_ampm,
        end_hour=end_hour,
        end_ampm=end_ampm,
        avoid_gaps=avoid_gaps,
        time_data=planned_courses_data,  # Only planned courses!
        fixed_sections=fixed_sections,
        fixed_labs=fixed_labs
>>>>>>> Stashed changes
    )

@app.route('/get_courses')
def get_courses():
    major = int(request.args.get('major', 0))
    if major == 0:
        # Computer Science: only return courses in the hardcoded plan
        course_placement = [
            'GENS101', 'ENGL101', 'MATH111', 'CHEM115', 'GENS100',
            'ENGL102', 'MATH112', 'PHYS121', 'COSC114', 'HUMAXXX',
            'COSC101', 'ECCE230', 'MATH204', 'MATH242', 'ENGR202',
            'COSC201', 'ECCE342', 'MATH232', 'MATH214', 'MATH234', 'HUMA123',
            'BUSS322', 'COSC301', 'ECCE336', 'ECCE354', 'ECCE356',
            'COSC312', 'COSC320', 'COSC330', 'COSC340', 'GENS300', 'ENGR399',
            'COSC497', 'ECCE434', 'TECH_ELECTIVE_5', 'TECH_ELECTIVE_1', 'TECH_ELECTIVE_2',
            'TECH_ELECTIVE_3', 'TECH_ELECTIVE_4', 'COSC498', 'BUXXX', 'GENS400', 'ENGR399(2)'
        ]
        result = []
        for code in course_placement:
            if code in fall25_time_data:
                result.append({'code': code, 'name': fall25_time_data[code]['name']})
            else:
                # For placeholders like TECH_ELECTIVE_1, BUXXX, etc.
                result.append({'code': code, 'name': code})
        return jsonify(result)
    else:
        # Other majors: return plan for selected major, with year/semester info if available
        plan = plans[major]
        result = []
        for code, data in plan.items():
            result.append({
                'code': code,
                'name': data['name'],
                'year': data.get('year', 'freshman'),
                'semester': data.get('semester', 'fall'),
                'credits': data.get('credits', 0),
                'prerequisites': data.get('prerequisites', [])
            })
        return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
