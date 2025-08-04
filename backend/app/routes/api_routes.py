"""
API Routes
Handles REST API endpoints with clean separation of concerns.
"""

from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, reqparse, fields, marshal_with, abort
from backend.core.services.schedule_service import ScheduleService
from backend.core.data.course_repository import CourseRepository

api_bp = Blueprint('api', __name__)
api = Api(api_bp)

# Database models (simplified for API)
class UserModel:
    def __init__(self, id, name, email, major_index, completed_courses, completed_semesters):
        self.id = id
        self.name = name
        self.email = email
        self.major_index = major_index
        self.completed_courses = completed_courses
        self.completed_semesters = completed_semesters

class UserScheduleResult:
    def __init__(self, id, user_id, plan_json):
        self.id = id
        self.user_id = user_id
        self.plan_json = plan_json

# In-memory storage for API (replace with database in production)
users_db = []
schedules_db = []
user_id_counter = 1
schedule_id_counter = 1

# Request parsers
user_args = reqparse.RequestParser()
user_args.add_argument('name', type=str, required=True, help="Name cannot be blank")
user_args.add_argument('email', type=str, required=True, help="Email cannot be blank")
user_args.add_argument('major_index', type=int, required=True, help="Major index required")
user_args.add_argument('completed_courses', type=str, required=True, help="Completed courses required")
user_args.add_argument('completed_semesters', type=int, required=True, help="Completed semesters required")

# Response fields
user_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'email': fields.String,
    'major_index': fields.Integer,
    'completed_courses': fields.String,
    'completed_semesters': fields.Integer,
}

schedule_fields = {
    'id': fields.Integer,
    'user_id': fields.Integer,
    'plan_json': fields.String,
}


class Users(Resource):
    """Resource for managing users."""
    
    @marshal_with(user_fields)
    def get(self):
        """Get all users."""
        return users_db
    
    @marshal_with(user_fields)
    def post(self):
        """Create a new user."""
        args = user_args.parse_args()
        
        global user_id_counter
        user = UserModel(
            id=user_id_counter,
            name=args["name"],
            email=args["email"],
            major_index=args["major_index"],
            completed_courses=args["completed_courses"],
            completed_semesters=args["completed_semesters"]
        )
        
        users_db.append(user)
        user_id_counter += 1
        
        return user, 201


class User(Resource):
    """Resource for managing individual users."""
    
    @marshal_with(user_fields)
    def get(self, id):
        """Get a specific user."""
        user = next((u for u in users_db if u.id == id), None)
        if not user:
            abort(404, message="User not found")
        return user
    
    @marshal_with(user_fields)
    def patch(self, id):
        """Update a user."""
        args = user_args.parse_args()
        user = next((u for u in users_db if u.id == id), None)
        if not user:
            abort(404, message="User not found")
        
        user.name = args["name"]
        user.email = args["email"]
        user.major_index = args["major_index"]
        user.completed_courses = args["completed_courses"]
        user.completed_semesters = args["completed_semesters"]
        
        return user
    
    @marshal_with(user_fields)
    def delete(self, id):
        """Delete a user."""
        user = next((u for u in users_db if u.id == id), None)
        if not user:
            abort(404, message="User not found")
        
        users_db.remove(user)
        return users_db


class UserSchedule(Resource):
    """Resource for generating user schedules."""
    
    def post(self, user_id):
        """Generate a schedule for a user."""
        user = next((u for u in users_db if u.id == user_id), None)
        if not user:
            return {"error": "User not found"}, 404
        
        try:
            # Generate schedule using service
            schedule_service = ScheduleService()
            plan_data = schedule_service.generate_course_plan(
                major_index=user.major_index,
                completed_raw=user.completed_courses,
                completed_semesters=user.completed_semesters
            )
            
            # Save schedule result
            import json
            global schedule_id_counter
            schedule_result = UserScheduleResult(
                id=schedule_id_counter,
                user_id=user.id,
                plan_json=json.dumps(plan_data)
            )
            schedules_db.append(schedule_result)
            schedule_id_counter += 1
            
            return {
                "user": user.name,
                "plan": plan_data['plan'],
                "statistics": {
                    "total_semesters": plan_data['total_semesters'],
                    "total_courses": plan_data['total_courses'],
                    "total_credits": plan_data['total_credits'],
                    "avg_credits_per_semester": plan_data['avg_credits_per_semester']
                }
            }
            
        except Exception as e:
            return {"error": f"Failed to generate schedule: {str(e)}"}, 500


class Courses(Resource):
    """Resource for course data."""
    
    def get(self):
        """Get courses for a major."""
        major_index = request.args.get('major', 0, type=int)
        
        try:
            course_repo = CourseRepository()
            courses = course_repo.get_courses_by_major(major_index)
            
            result = [{'code': code, 'name': data['name']} for code, data in courses.items()]
            return result
            
        except Exception as e:
            return {"error": str(e)}, 400


class Majors(Resource):
    """Resource for major data."""
    
    def get(self):
        """Get available majors."""
        try:
            course_repo = CourseRepository()
            majors = course_repo.get_available_majors()
            return majors
            
        except Exception as e:
            return {"error": str(e)}, 400


# Register resources
api.add_resource(Users, '/users/')
api.add_resource(User, '/users/<int:id>')
api.add_resource(UserSchedule, '/users/<int:user_id>/schedule')
api.add_resource(Courses, '/courses/')
api.add_resource(Majors, '/majors/')


@api_bp.route('/')
def home():
    """API home endpoint."""
    return {
        "message": "Course Planner API",
        "version": "1.0.0",
        "endpoints": {
            "users": "/users/",
            "user": "/users/<id>",
            "schedule": "/users/<user_id>/schedule",
            "courses": "/courses/?major=<major_index>",
            "majors": "/majors/"
        }
    } 