from flask import Flask 
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, reqparse, fields, marshal_with, abort
from scheduler import CourseScheduler
from scheduler_data import plans, time_data
import json
import gurobipy as gp
from gurobipy import GRB


app = Flask(__name__) 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app) 
api = Api(app)

class UserModel(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    major_index = db.Column(db.Integer)
    completed_courses = db.Column(db.Text)  # CSV string
    completed_semesters = db.Column(db.Integer)

    def __repr__(self): 
        return f"User(name = {self.name}, email = {self.email})"
class UserScheduleResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_model.id'), nullable=False)
    plan_json = db.Column(db.Text)

user_args = reqparse.RequestParser()
user_args.add_argument('name', type=str, required=True, help="Name cannot be blank")
user_args.add_argument('email', type=str, required=True, help="Email cannot be blank")
user_args.add_argument('major_index', type=int, required=True, help="Major index required")
user_args.add_argument('completed_courses', type=str, required=True, help="Completed courses required")
user_args.add_argument('completed_semesters', type=int, required=True, help="Completed semesters required")

userFields = {
    'id': fields.Integer,
    'name': fields.String,
    'email': fields.String,
    'major_index': fields.Integer,
    'completed_courses': fields.String,
    'completed_semesters': fields.Integer,
}


class Users(Resource):
    @marshal_with(userFields)
    def get(self):
        users = UserModel.query.all() 
        return users 
    
    @marshal_with(userFields)
    def post(self):
        args = user_args.parse_args()
        user = UserModel(
            name=args["name"],
            email=args["email"],
            major_index=args["major_index"],
            completed_courses=args["completed_courses"],
            completed_semesters=args["completed_semesters"]
        )
        db.session.add(user) 
        db.session.commit()
        users = UserModel.query.all()
        return users, 201
    
class User(Resource):
    @marshal_with(userFields)
    def get(self, id):
        user = UserModel.query.filter_by(id=id).first() 
        if not user: 
            abort(404, message="User not found")
        return user 
    
    @marshal_with(userFields)
    def patch(self, id):
        args = user_args.parse_args()
        user = UserModel.query.filter_by(id=id).first() 
        if not user: 
            abort(404, message="User not found")
        user.name = args["name"]
        user.email = args["email"]
        user.major_index = args["major_index"]
        user.completed_courses = args["completed_courses"]
        user.completed_semesters = args["completed_semesters"]
        db.session.commit()
        return user 
    
    @marshal_with(userFields)
    def delete(self, id):
        user = UserModel.query.filter_by(id=id).first() 
        if not user: 
            abort(404, message="User not found")
        db.session.delete(user)
        db.session.commit()
        users = UserModel.query.all()
        return users

    
api.add_resource(Users, '/api/users/')
api.add_resource(User, '/api/users/<int:id>')

# Scheduler Route
@app.route('/api/users/<int:user_id>/schedule', methods=['POST'])
def run_scheduler(user_id):
    user = UserModel.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    completed = set(c.strip() for c in user.completed_courses.split(','))
    courses = plans[user.major_index]

    scheduler = CourseScheduler(
        courses=courses,
        completed=completed,
        required=set(time_data.keys()),
        max=180,
        min=12,
        semesters=12,
        starting=user.completed_semesters + 1
    )

    model = scheduler.build_model3(alpha=0, beta=0, gamma=80, delta=30)
    model.optimize()
    

    if model.status == GRB.OPTIMAL:
        result_dict = {}
        for (course, sem), var in scheduler.y.items():
            if var.X > 0.5:
                result_dict.setdefault(sem, []).append(course)
    # save or return results
    else:
        # Return error or fallback
        return {"message": "Optimization failed or was interrupted."}, 400


    

    result = UserScheduleResult(user_id=user.id, plan_json=json.dumps(result_dict))
    db.session.add(result)
    db.session.commit()

    return jsonify({
        "user": user.name,
        "plan": result_dict
    })

@app.route('/')
def home():
    return '<h1>Flask REST API</h1>'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)