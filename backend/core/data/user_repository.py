"""
User Repository
Handles all user data access operations.
"""

import os
import json
from typing import Dict, List, Optional, Any, Set


class UserRepository:
    """Repository for user data access operations."""
    
    def __init__(self):
        self._fixed_courses_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            'database', 'fixed_courses.json'
        )
        self._last_plan_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            'database', 'last_plan.json'
        )
    
    def load_fixed_courses(self) -> List[List[str]]:
        """
        Load fixed course assignments from file.
        
        Returns:
            List of [course_code, semester] pairs
        """
        if not os.path.exists(self._fixed_courses_file):
            return []
        
        try:
            with open(self._fixed_courses_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    def save_fixed_courses(self, fixed_courses: List[List[str]]) -> None:
        """
        Save fixed course assignments to file.
        
        Args:
            fixed_courses: List of [course_code, semester] pairs
        """
        os.makedirs(os.path.dirname(self._fixed_courses_file), exist_ok=True)
        with open(self._fixed_courses_file, "w", encoding="utf-8") as f:
            json.dump(fixed_courses, f, indent=2)
    
    def add_fixed_course(self, course_code: str, semester: int) -> None:
        """
        Add a fixed course assignment.
        
        Args:
            course_code: Course code to fix
            semester: Semester number to fix it in
        """
        fixed_courses = self.load_fixed_courses()
        if [course_code, semester] not in fixed_courses:
            fixed_courses.append([course_code, semester])
            self.save_fixed_courses(fixed_courses)
    
    def remove_fixed_course(self, course_code: str, semester: int) -> None:
        """
        Remove a fixed course assignment.
        
        Args:
            course_code: Course code to remove
            semester: Semester number
        """
        fixed_courses = self.load_fixed_courses()
        fixed_courses = [fc for fc in fixed_courses if fc != [course_code, semester]]
        self.save_fixed_courses(fixed_courses)
    
    def get_fixed_courses(self) -> List[List[str]]:
        """
        Get all fixed course assignments.
        
        Returns:
            List of [course_code, semester] pairs
        """
        return self.load_fixed_courses()
    
    def load_last_plan(self) -> Optional[Dict[str, Any]]:
        """
        Load the last generated plan from file.
        
        Returns:
            Plan data dictionary or None if not found
        """
        if not os.path.exists(self._last_plan_file):
            return None
        
        try:
            with open(self._last_plan_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def save_last_plan(self, plan_data: Dict[str, Any]) -> None:
        """
        Save the last generated plan to file.
        
        Args:
            plan_data: Plan data dictionary
        """
        os.makedirs(os.path.dirname(self._last_plan_file), exist_ok=True)
        with open(self._last_plan_file, "w", encoding="utf-8") as f:
            json.dump(plan_data, f, indent=2)
    
    def parse_completed_courses(self, completed_raw: str) -> Set[str]:
        """
        Parse completed courses from comma-separated string.
        
        Args:
            completed_raw: Comma-separated course codes
            
        Returns:
            Set of completed course codes
        """
        if not completed_raw:
            return set()
        
        return set(code.strip() for code in completed_raw.split(',') if code.strip())
    
    def format_completed_courses(self, completed_courses: Set[str]) -> str:
        """
        Format completed courses set to comma-separated string.
        
        Args:
            completed_courses: Set of completed course codes
            
        Returns:
            Comma-separated string of course codes
        """
        return ','.join(sorted(completed_courses))
    
    def validate_user_input(self, major_index: int, completed_raw: str, 
                           completed_semesters: int) -> Dict[str, Any]:
        """
        Validate user input data.
        
        Args:
            major_index: Major index
            completed_raw: Comma-separated completed courses
            completed_semesters: Number of completed semesters
            
        Returns:
            Dictionary with validation results and parsed data
        """
        errors = []
        
        # Validate major index
        from backend.models.scheduler_data import plans
        if major_index < 0 or major_index >= len(plans):
            errors.append(f"Invalid major index: {major_index}")
        
        # Validate completed semesters
        if completed_semesters < 0:
            errors.append("Completed semesters cannot be negative")
        
        # Parse and validate completed courses
        completed_courses = self.parse_completed_courses(completed_raw)
        
        # Validate each completed course exists in the major
        if major_index < len(plans):
            valid_courses = set(plans[major_index].keys())
            invalid_courses = completed_courses - valid_courses
            if invalid_courses:
                errors.append(f"Invalid completed courses: {', '.join(invalid_courses)}")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'completed_courses': completed_courses,
            'major_index': major_index,
            'completed_semesters': completed_semesters
        } 