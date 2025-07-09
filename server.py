from flask import redirect, url_for
from flask import Flask, jsonify, render_template, request
from scheduler import CourseScheduler
from scheduler_data import plans, time_data
#import io
#import sys
import gurobipy as gp
from gurobipy import GRB

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
            max=180,
            min=12,
            semesters=12,  
            starting=completed_semesters + 1
        )

        model = scheduler.build_model3(alpha=0, beta=0, gamma=80, delta=30)
        model.optimize()
        scheduler.get_full_solution()
        # for output
        result_dict = {}
        for (course, sem), var in scheduler.y.items():
            if var.X > 0.5:
                result_dict.setdefault(sem, []).append(course)
                if sem == completed_semesters + 1:
                    first_semester_courses.append(course)
        # Transform plan to structured format for frontend
        plan = []
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
@app.route('/next_semester', methods=['POST'])
def next_semester():
    major_index = int(request.form['major'])
    completed_raw = request.form['completed']
    completed_set = set(code.strip() for code in completed_raw.split(',') if code.strip())
    registered_raw = request.form['registered']
    registered_set = set(code.strip() for code in registered_raw.split(',') if code.strip())
    courses = plans[major_index]

    # Use model 2 for timetable generation
    scheduler = CourseScheduler(
        courses=time_data,  # Use time_data for sections/times
        completed=completed_set,
        required=set(courses.keys())
    )
    desired_courses = list(time_data.keys())
    scheduler.build_model2(desired_courses=desired_courses)
    scheduler.model2.optimize()

    # Gather schedule info for visualization
    timetable_courses = []
    # Assign a color per course for timetable
    import random
    color_palette = ['#3182ce', '#38a169', '#e53e3e', '#d69e2e', '#805ad5', '#319795', '#f56565', '#ed8936', '#ecc94b', '#48bb78', '#4299e1', '#9f7aea']
    course_colors = {}
    for idx, course in enumerate(time_data.keys()):
        course_colors[course] = color_palette[idx % len(color_palette)]

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


    # Count labs actually scheduled in this semester (from timetable_courses)
    lab_count = 0
    for course in desired_courses:
        if 'labs' in time_data[course]:
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
        lab_count=lab_count
    )


@app.route('/get_courses')
def get_courses():
    major = int(request.args.get('major', 0))
    selected_courses = plans[major]
    result = [{'code': code, 'name': data['name']} for code, data in selected_courses.items()]
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
