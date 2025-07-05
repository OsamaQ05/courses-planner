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

        # Debug information
        print(f"Total courses in major: {len(courses)}")
        print(f"Completed courses: {len(completed_set)}")
        print(f"Remaining courses: {len(courses) - len(completed_set)}")
        print(f"Completed semesters: {completed_semesters}")

        scheduler = CourseScheduler(
            courses=courses,
            completed=completed_set,
            required=set(courses.keys()),  # Use all courses in the major, not just time_data
            max=18,  # Changed from 180 to 18 (max credits per semester)
            min=12,
            semesters=8,  # Reduced from 12 to 8 semesters to make it more feasible
            starting=completed_semesters + 1
        )

        # Set timeout for optimization
        model = scheduler.build_model3(alpha=0, beta=0, gamma=80, delta=30)
        model.setParam('TimeLimit', 30)  # 30 second timeout
        model.setParam('OutputFlag', 0)  # Reduce output for cleaner logs
        model.optimize()
      
        # Check if model has a solution
        if model.Status == GRB.OPTIMAL:
            # Get structured output
            result_dict = {}
            for (course, sem), var in scheduler.y.items():
                if var.X > 0.5:
                    result_dict.setdefault(sem, []).append(course)
                    if sem == completed_semesters + 1:
                        first_semester_courses.append(course)

            plan = sorted(result_dict.items())
        elif model.Status == GRB.INFEASIBLE:
            plan = []
            first_semester_courses = []
            error_message = "No valid schedule found. The constraints are infeasible. This might be due to conflicting prerequisites or credit requirements."
        elif model.Status == GRB.TIME_LIMIT:
            plan = []
            first_semester_courses = []
            error_message = "Optimization timed out. The problem is too complex. Try selecting fewer courses or adjusting your parameters."
        else:
            # Model has no solution or other issues
            plan = []
            first_semester_courses = []
            error_message = f"Optimization failed with status {model.Status}. Please try again with different parameters."

      

        return render_template(
            'plan.html',
            plan=plan,
            first_semester_courses=first_semester_courses,
            major_index=major_index,
            completed_raw=completed_raw,
            completed_semesters=completed_semesters,
            error=error_message if 'error_message' in locals() else None
        )

    return render_template('index.html')
@app.route('/next_semester', methods=['POST'])
def next_semester():
    major_index = int(request.form['major'])
    completed_set = set(code.strip() for code in request.form['completed'].split(',') if code.strip())
    registered_set = set(code.strip() for code in request.form['registered'].split(',') if code.strip())
    courses = plans[major_index]

    scheduler = CourseScheduler(
        courses=courses,
        completed=completed_set,
        required=set(courses.keys())
    )
    model = scheduler.build_model2(desired_courses=registered_set)
    
    model.optimize()
    #scheduler.get_full_solution()
    
    if model.Status == GRB.OPTIMAL:
        next_plan = [
            f"{scheduler.courses[course]['name']} → {section}"
            for (course, section), var in scheduler.x2.items() if var.X > 0.5
        ]
    else:
        # Model is infeasible or has no solution
        next_plan = []
        error_message = "No valid schedule found for the selected courses. Check for time conflicts or missing prerequisites."
    return render_template(
        'schedule.html',
        next_plan=next_plan,
        error_message=error_message if 'error_message' in locals() else None
    )


@app.route('/get_courses')
def get_courses():
    major = int(request.args.get('major', 0))
    selected_courses = plans[major]
    result = []
    for code, data in selected_courses.items():
        # Convert set to list for JSON serialization
        available_in = data.get('available_in', {'fall', 'spring', 'summer'})
        if isinstance(available_in, set):
            available_in = list(available_in)
        
        course_info = {
            'code': code, 
            'name': data['name'],
            'credits': data.get('credits', 0),
            'weight': data.get('weight', 1),
            'year': data.get('year', 1),  # Default to year 1 if not specified
            'prerequisites': data.get('prerequisites', []),
            'available_in': available_in
        }
        result.append(course_info)
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
