"""
Web Routes
Handles web interface routes with clean separation of concerns.
"""

from flask import Blueprint, render_template, request, jsonify
from backend.core.services.schedule_service import ScheduleService
from backend.core.services.ai_service import AIService
from backend.core.data.course_repository import CourseRepository

web_bp = Blueprint('web', __name__)


@web_bp.route('/', methods=['GET', 'POST'])
def home():
    """Home page route - handles course plan generation."""
    if request.method == 'POST':
        try:
            # Extract form data
            major_index = int(request.form['major'])
            completed_raw = request.form['completed']
            completed_semesters = int(request.form['completed_semesters'])
            
            # Generate plan using service
            schedule_service = ScheduleService()
            plan_data = schedule_service.generate_course_plan(
                major_index=major_index,
                completed_raw=completed_raw,
                completed_semesters=completed_semesters
            )
            
            return render_template('plan.html', **plan_data)
            
        except ValueError as e:
            # Handle validation errors
            return render_template('index.html', error=str(e))
        except Exception as e:
            # Handle other errors
            return render_template('index.html', error=f"An error occurred: {str(e)}")
    
    return render_template('index.html')


@web_bp.route('/next_semester', methods=['GET', 'POST'])
def next_semester():
    """Next semester route - handles timetable generation."""
    if request.method == 'GET':
        # Show preferences form
        course_repo = CourseRepository()
        fall25_courses = course_repo.get_fall25_courses()
        
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
    
    # POST: Handle timetable generation
    try:
        # Extract form data
        major_index = int(request.form.get('major', 0))
        completed_raw = request.form.get('completed', '')
        registered_raw = request.form.get('registered', '')
        
        # Parse fixed sections and labs
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
        
        # Check if preferences are submitted
        days_preferred = request.form.getlist('days_preferred') or ['Mon', 'Tue', 'Wed', 'Thu']
        start_hour = int(request.form.get('start_hour', 9))
        start_ampm = request.form.get('start_ampm', 'AM')
        end_hour = int(request.form.get('end_hour', 8))
        end_ampm = request.form.get('end_ampm', 'PM')
        avoid_gaps = 'avoid_gaps' in request.form
        
        preferences_submitted = bool(
            days_preferred or 
            request.form.get('start_hour') or 
            request.form.get('end_hour') or 
            'avoid_gaps' in request.form
        )
        
        if not preferences_submitted:
            # Show preferences form only
            course_repo = CourseRepository()
            fall25_courses = course_repo.get_fall25_courses()
            
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
        
        # Generate timetable using service
        schedule_service = ScheduleService()
        timetable_data = schedule_service.generate_timetable(
            major_index=major_index,
            completed_raw=completed_raw,
            registered_raw=registered_raw,
            fixed_sections=fixed_sections,
            fixed_labs=fixed_labs
        )
        
        # Count labs
        course_repo = CourseRepository()
        fall25_courses = course_repo.get_fall25_courses()
        registered_courses = set(code.strip() for code in registered_raw.split(',') if code.strip())
        lab_count = sum(1 for course in registered_courses 
                       if course in fall25_courses and 'labs' in fall25_courses[course])
        
        return render_template(
            'schedule.html',
            all_timetables=timetable_data['timetables'],
            timetable_courses=timetable_data['timetables'][0] if timetable_data['timetables'] else [],
            solution_count=timetable_data['solution_count'],
            num_solutions=timetable_data['num_solutions'],
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
        
    except Exception as e:
        # Handle errors
        course_repo = CourseRepository()
        fall25_courses = course_repo.get_fall25_courses()
        
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
            error=str(e),
            time_data=fall25_courses
        )


@web_bp.route('/get_courses')
def get_courses():
    """API endpoint to get courses for a major."""
    try:
        major = int(request.args.get('major', 0))
        course_repo = CourseRepository()
        courses = course_repo.get_courses_by_major(major)
        
        result = [{'code': code, 'name': data['name']} for code, data in courses.items()]
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@web_bp.route('/mcp_chat', methods=['POST'])
def mcp_chat():
    """AI chat endpoint for course planning."""
    try:
        # Extract request data
        user_input = request.json.get('message')
        completed_semesters = int(request.json.get('completed_semesters', 0))
        major_index = int(request.json.get('major_index', 0))
        completed_raw = request.json.get('completed_raw', '')
        
        # Process chat request using AI service
        ai_service = AIService()
        result = ai_service.process_chat_request(
            user_input=user_input,
            major_index=major_index,
            completed_raw=completed_raw,
            completed_semesters=completed_semesters
        )
        
        if result['success']:
            # Render the new plan HTML
            from flask import render_template_string
            plan_html = render_template('plan.html', **result['plan_data'])
            
            return jsonify({
                "success": True,
                "raw": result['raw'],
                "plan_html": plan_html
            })
        else:
            # Handle failure
            if result['plan_data']['plan']:
                plan_html = render_template('plan.html', **result['plan_data']['plan'])
            else:
                plan_html = ""
            
            return jsonify({
                "success": False,
                "error": result['plan_data']['error'],
                "plan_html": plan_html
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"An error occurred: {str(e)}",
            "plan_html": ""
        }), 500 