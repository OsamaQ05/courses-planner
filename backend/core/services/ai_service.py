"""
AI Service
Handles OpenAI integration and AI-powered course planning.
"""

import re
import os
from typing import Dict, List, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from backend.core.data.course_repository import CourseRepository
from backend.core.data.user_repository import UserRepository
from backend.core.scheduler.course_scheduler import CourseScheduler

load_dotenv()


class AIService:
    """Service for AI-powered course planning features."""
    
    def __init__(self, course_repo: Optional[CourseRepository] = None,
                 user_repo: Optional[UserRepository] = None):
        self.course_repo = course_repo or CourseRepository()
        self.user_repo = user_repo or UserRepository()
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            try:
                from backend.config.openai_key import OPENAI_API_KEY as api_key_from_file
                api_key = api_key_from_file
                print("Loaded API key from openai_key.py")
            except (ImportError, ModuleNotFoundError):
                raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in your .env file or create an openai_key.py with OPENAI_API_KEY = 'your-key'.")
        
        self.client = OpenAI(api_key=api_key)
    
    def process_chat_request(self, user_input: str, major_index: int, 
                           completed_raw: str, completed_semesters: int) -> Dict[str, Any]:
        """
        Process a chat request and generate a new course plan.
        
        Args:
            user_input: User's natural language request
            major_index: Major index
            completed_raw: Comma-separated completed courses
            completed_semesters: Number of completed semesters
            
        Returns:
            Dictionary containing the response and new plan
        """
        # Get course data
        courses = self.course_repo.get_courses_by_major(major_index)
        completed_courses = self.user_repo.parse_completed_courses(completed_raw)
        
        # Generate AI prompt
        prompt = self._generate_prompt(user_input, completed_semesters, courses)
        
        # Get AI response
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs only Python function calls as instructed."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0
        )
        
        model_output = response.choices[0].message.content
        
        # Parse AI commands
        commands = self._parse_ai_commands(model_output)
        
        # Apply commands and generate new plan
        plan_data = self._apply_commands_and_generate_plan(
            commands, major_index, completed_raw, completed_semesters
        )
        
        return {
            "success": True,
            "raw": model_output,
            "plan_data": plan_data
        }
    
    def _generate_prompt(self, user_input: str, completed_semesters: int, 
                        courses: Dict[str, Any]) -> str:
        """Generate the prompt for the AI model."""
        course_list = "\n".join([f"{code}: {data['name']}" for code, data in courses.items()])
        
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
    
    def _parse_ai_commands(self, model_output: str) -> Dict[str, Any]:
        """Parse AI model output into structured commands."""
        commands = {
            'max_credits': 18,
            'total_semesters': 12,
            'delta': 30,
            'fixed_courses': []
        }
        
        for line in model_output.splitlines():
            line = line.strip()
            
            # Parse set_max_credits(NUM)
            m = re.match(r"set_max_credits\((\d+)\)", line)
            if m:
                commands['max_credits'] = int(m.group(1))
            
            # Parse set_total_semesters(NUM)
            m = re.match(r"set_total_semesters\((\d+)\)", line)
            if m:
                commands['total_semesters'] = int(m.group(1))
            
            # Parse set_graduate_late()
            if line.startswith("set_graduate_late()"):
                commands['total_semesters'] = 15
                commands['delta'] = 0
            
            # Parse add_fixed_course('CODE', SEM)
            m = re.match(r"add_fixed_course\(['\"](\w+)['\"],\s*(\d+)\)", line)
            if m:
                code = m.group(1)
                sem = int(m.group(2))
                commands['fixed_courses'].append([code, sem])
        
        return commands
    
    def _apply_commands_and_generate_plan(self, commands: Dict[str, Any], 
                                        major_index: int, completed_raw: str, 
                                        completed_semesters: int) -> Dict[str, Any]:
        """Apply AI commands and generate a new course plan."""
        # Apply fixed courses
        for code, sem in commands['fixed_courses']:
            self.user_repo.add_fixed_course(code, sem)
        
        # Get all fixed courses
        all_fixed_courses = self.user_repo.get_fixed_courses()
        
        # Get course data
        courses = self.course_repo.get_courses_by_major(major_index)
        completed_courses = self.user_repo.parse_completed_courses(completed_raw)
        
        # Create scheduler
        scheduler = CourseScheduler(
            courses=courses,
            completed=completed_courses,
            required=set(courses.keys()),
            max=commands['max_credits'],
            min=12,
            semesters=commands['total_semesters'],
            starting=completed_semesters + 1
        )
        
        # Build and optimize model
        model = scheduler.build_model3(alpha=0, beta=0, gamma=80, delta=commands['delta'])
        
        # Add fixed courses
        for code, sem in all_fixed_courses:
            scheduler.add_fixed_course(code, sem)
        
        model.optimize()
        
        # Check if solution is feasible
        import gurobipy as gp
        if model.status == gp.GRB.INFEASIBLE:
            # Return last plan as fallback
            last_plan = self.user_repo.load_last_plan()
            if last_plan:
                return {
                    "success": False,
                    "error": "No solution found for your request.",
                    "plan": last_plan
                }
            else:
                return {
                    "success": False,
                    "error": "No solution found for your request.",
                    "plan": None
                }
        
        # Extract results
        result_dict = {}
        for (course, sem), var in scheduler.y.items():
            if var.X > 0.5:
                result_dict.setdefault(sem, []).append(course)
        
        # Transform to structured format
        plan = self._transform_to_structured_plan(result_dict, courses, completed_semesters)
        
        # Calculate statistics
        stats = self._calculate_plan_statistics(plan)
        
        # Save plan
        plan_data = {
            'plan': plan,
            'major_index': major_index,
            'completed_raw': completed_raw,
            'completed_semesters': completed_semesters,
            **stats
        }
        self.user_repo.save_last_plan(plan_data)
        
        return plan_data
    
    def _transform_to_structured_plan(self, result_dict: Dict[int, List[str]], 
                                    courses: Dict[str, Any], 
                                    completed_semesters: int) -> List[Dict[str, Any]]:
        """Transform raw result dictionary to structured plan format."""
        plan = []
        
        # Build unlocks map
        unlocks_map = {code: [] for code in courses}
        for c, info in courses.items():
            for prereq in info.get('prerequisites', []):
                if prereq in unlocks_map:
                    unlocks_map[prereq].append(c)
        
        # Transform each semester
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
        
        return plan
    
    def _calculate_plan_statistics(self, plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics for the plan."""
        if not plan:
            return {
                'total_semesters': 0,
                'total_courses': 0,
                'total_credits': 0,
                'avg_credits_per_semester': 0,
                'first_semester_courses': []
            }
        
        total_semesters = len(plan)
        total_courses = sum(len(sem['courses']) for sem in plan)
        total_credits = sum(sem['credits'] for sem in plan)
        avg_credits_per_semester = round(total_credits / total_semesters, 2)
        first_semester_courses = plan[0]['courses'] if plan else []
        
        return {
            'total_semesters': total_semesters,
            'total_courses': total_courses,
            'total_credits': total_credits,
            'avg_credits_per_semester': avg_credits_per_semester,
            'first_semester_courses': first_semester_courses
        } 