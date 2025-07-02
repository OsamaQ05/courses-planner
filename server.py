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


        scheduler = CourseScheduler(
            courses=courses,
            completed=completed_set,
            required=set(time_data.keys()),
            max=180,
            min=12,
            semesters=12,  # always plan for max semesters
            starting=completed_semesters + 1
        )

        model = scheduler.build_model3(alpha=0, beta=0, gamma=80, delta=30)
        model.optimize()
      

        # Get structured output
        result_dict = {}
        for (course, sem), var in scheduler.y.items():
            if var.X > 0.5:
                result_dict.setdefault(sem, []).append(course)
                if sem == completed_semesters + 1:
                    first_semester_courses.append(course)

        plan = sorted(result_dict.items())

      

        return render_template(
            'plan.html',
            plan=plan,
            first_semester_courses=first_semester_courses,
            major_index=major_index,
            completed_raw=completed_raw,
            completed_semesters=completed_semesters
        )

    return render_template('index.html')
@app.route('/next_semester', methods=['POST'])
def next_semester():
    major_index = int(request.form['major'])
    completed_set = set(code.strip() for code in request.form['completed'].split(',') if code.strip())
    registered_set = set(code.strip() for code in request.form['registered'].split(',') if code.strip())
    courses = plans[major_index]

    scheduler = CourseScheduler(
        courses=time_data,
        completed=completed_set,
        required=set(courses.keys())
    )
    model = scheduler.build_model2(desired_courses=registered_set)
    
    model.optimize()
    #scheduler.get_full_solution()
    next_plan = [
        f"{scheduler.courses[course]['name']} → {section}"
        for (course, section), var in scheduler.x2.items() if var.X > 0.5
    ]
    return render_template(
        'schedule.html',
        next_plan=next_plan
    )


@app.route('/get_courses')
def get_courses():
    major = int(request.args.get('major', 0))
    selected_courses = plans[major]
    result = [{'code': code, 'name': data['name']} for code, data in selected_courses.items()]
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
