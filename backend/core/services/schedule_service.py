"""
Schedule Service
Handles course scheduling business logic.
"""

from typing import Dict, List, Any, Optional, Set
from backend.core.data.course_repository import CourseRepository
from backend.core.data.user_repository import UserRepository
from backend.core.scheduler.course_scheduler import CourseScheduler


class ScheduleService:
    """Service for course scheduling business logic."""
    
    def __init__(self, course_repo: Optional[CourseRepository] = None, 
                 user_repo: Optional[UserRepository] = None):
        self.course_repo = course_repo or CourseRepository()
        self.user_repo = user_repo or UserRepository()
    
    def generate_course_plan(self, major_index: int, completed_raw: str, 
                           completed_semesters: int, max_credits: int = 18, 
                           min_credits: int = 12, total_semesters: int = 12) -> Dict[str, Any]:
        """
        Generate a course plan for the given parameters.
        
        Args:
            major_index: Index of the major
            completed_raw: Comma-separated completed courses
            completed_semesters: Number of completed semesters
            max_credits: Maximum credits per semester
            min_credits: Minimum credits per semester
            total_semesters: Total semesters to plan for
            
        Returns:
            Dictionary containing the generated plan and metadata
        """
        # Validate input
        validation = self.user_repo.validate_user_input(
            major_index, completed_raw, completed_semesters
        )
        if not validation['is_valid']:
            raise ValueError(f"Invalid input: {', '.join(validation['errors'])}")
        
        # Get course data
        courses = self.course_repo.get_courses_by_major(major_index)
        completed_courses = validation['completed_courses']
        
        # Create scheduler
        scheduler = CourseScheduler(
            courses=courses,
            completed=completed_courses,
            required=set(courses.keys()),
            max=max_credits,
            min=min_credits,
            semesters=total_semesters,
            starting=completed_semesters + 1
        )
        
        # Add fixed courses
        fixed_courses = self.user_repo.get_fixed_courses()
        for course_code, semester in fixed_courses:
            scheduler.add_fixed_course(course_code, semester)
        
        # Build and optimize model
        model = scheduler.build_model3(alpha=0, beta=0, gamma=80, delta=30)
        model.optimize()
        
        # Extract results
        result_dict = {}
        for (course, sem), var in scheduler.y.items():
            if var.X > 0.5:
                result_dict.setdefault(sem, []).append(course)
        
        # Transform to structured format
        plan = self._transform_to_structured_plan(result_dict, courses, completed_semesters)
        
        # Calculate statistics
        stats = self._calculate_plan_statistics(plan)
        
        # Save last plan
        plan_data = {
            'plan': plan,
            'major_index': major_index,
            'completed_raw': completed_raw,
            'completed_semesters': completed_semesters,
            **stats
        }
        self.user_repo.save_last_plan(plan_data)
        
        return plan_data
    
    def generate_timetable(self, major_index: int, completed_raw: str, 
                          registered_raw: str, fixed_sections: Dict[str, str] = None,
                          fixed_labs: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Generate a timetable for the next semester.
        
        Args:
            major_index: Index of the major
            completed_raw: Comma-separated completed courses
            registered_raw: Comma-separated registered courses
            fixed_sections: Dictionary of fixed section assignments
            fixed_labs: Dictionary of fixed lab assignments
            
        Returns:
            Dictionary containing timetable data
        """
        # Get course data
        courses = self.course_repo.get_courses_by_major(major_index)
        fall25_courses = self.course_repo.get_fall25_courses()
        completed_courses = self.user_repo.parse_completed_courses(completed_raw)
        registered_courses = self.user_repo.parse_completed_courses(registered_raw)
        
        # Create scheduler for timetable
        scheduler = CourseScheduler(
            courses=fall25_courses,
            completed=completed_courses,
            required=set(courses.keys())
        )
        
        # Build timetable model
        scheduler.build_model2(
            desired_courses=list(registered_courses),
            fixed_sections=fixed_sections or {},
            fixed_labs=fixed_labs or {}
        )
        
        # Set optimization parameters
        import gurobipy as gp
        scheduler.model2.setParam(gp.GRB.Param.PoolSearchMode, 2)
        scheduler.model2.setParam(gp.GRB.Param.PoolSolutions, 50)
        scheduler.model2.optimize()
        
        # Extract solutions
        timetables = self._extract_timetable_solutions(scheduler, registered_courses)
        
        return {
            'timetables': timetables,
            'solution_count': len(timetables),
            'num_solutions': scheduler.model2.SolCount,
            'registered_courses': list(registered_courses)
        }
    
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
    
    def _extract_timetable_solutions(self, scheduler: CourseScheduler, 
                                   desired_courses: Set[str]) -> List[List[Dict[str, Any]]]:
        """Extract timetable solutions from the scheduler."""
        import random
        
        # Color palette for courses
        color_palette = ['#3182ce', '#38a169', '#e53e3e', '#d69e2e', '#805ad5', 
                        '#319795', '#f56565', '#ed8936', '#ecc94b', '#48bb78', 
                        '#4299e1', '#9f7aea']
        course_colors = {}
        for idx, course in enumerate(desired_courses):
            course_colors[course] = color_palette[idx % len(color_palette)]
        
        # Extract solutions
        num_solutions = scheduler.model2.SolCount
        all_timetables = []
        
        for sol_idx in range(num_solutions):
            scheduler.model2.params.SolutionNumber = sol_idx
            timetable_courses = []
            
            for (course, section), var in scheduler.x2.items():
                if var.Xn > 0.5:
                    cinfo = scheduler.courses[course]
                    secinfo = self._get_section_info(cinfo, section)
                    
                    raw_time = secinfo.get('time', secinfo.get('name', ''))
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
                        'length': CourseScheduler.to_minutes(end) - CourseScheduler.to_minutes(start) if start and end else 0
                    })
            
            all_timetables.append(timetable_courses)
        
        # Return top 10 solutions
        return all_timetables[:10]
    
    def _get_section_info(self, course_info: Dict[str, Any], section: str) -> Dict[str, Any]:
        """Get section information from course info."""
        is_lab = False
        if 'labs' in course_info and section in course_info['labs']:
            is_lab = True
        
        if is_lab:
            return {'name': section}
        
        sections = course_info.get('sections', [])
        if isinstance(sections, dict):
            return sections.get(section, {})
        elif isinstance(sections, list):
            for s in sections:
                if isinstance(s, dict):
                    if (s.get('name') == section) or (s.get('section') == section):
                        return s
                elif isinstance(s, str) and s == section:
                    return {'name': s}
        
        return {'name': section} 