"""
Course Repository
Handles all course data access operations.
"""

import os
import json
from typing import Dict, List, Optional, Any


class CourseRepository:
    """Repository for course data access operations."""
    
    def __init__(self):
        self._courses_cache = {}
        self._fall25_courses_cache = {}
    
    def get_courses_by_major(self, major_index: int) -> Dict[str, Any]:
        """
        Get courses for a specific major.
        
        Args:
            major_index: Index of the major
            
        Returns:
            Dictionary of courses for the major
        """
        from backend.models.scheduler_data import plans
        
        if major_index >= len(plans):
            raise ValueError(f"Invalid major index: {major_index}")
        
        return plans[major_index]
    
    def get_fall25_courses(self) -> Dict[str, Any]:
        """
        Get Fall 2025 course data with sections and times.
        
        Returns:
            Dictionary of Fall 2025 courses with schedule information
        """
        if not self._fall25_courses_cache:
            from backend.models.fall25_courses_data import fall25_courses
            self._fall25_courses_cache = fall25_courses
        
        return self._fall25_courses_cache
    
    def get_course_info(self, course_code: str, major_index: int) -> Optional[Dict[str, Any]]:
        """
        Get information for a specific course.
        
        Args:
            course_code: Course code (e.g., 'COSC101')
            major_index: Major index
            
        Returns:
            Course information dictionary or None if not found
        """
        courses = self.get_courses_by_major(major_index)
        return courses.get(course_code)
    
    def get_course_schedule(self, course_code: str) -> Optional[Dict[str, Any]]:
        """
        Get schedule information for a course from Fall 2025 data.
        
        Args:
            course_code: Course code
            
        Returns:
            Schedule information or None if not found
        """
        fall25_courses = self.get_fall25_courses()
        return fall25_courses.get(course_code)
    
    def get_available_majors(self) -> List[Dict[str, Any]]:
        """
        Get list of available majors.
        
        Returns:
            List of major information dictionaries
        """
        from backend.models.scheduler_data import plans
        
        majors = [
            {"index": 0, "name": "Computer Science", "code": "CS"},
            {"index": 1, "name": "Computer Engineering", "code": "CE"},
            # Add more majors as needed
        ]
        
        return majors[:len(plans)]
    
    def validate_course_code(self, course_code: str, major_index: int) -> bool:
        """
        Validate if a course code exists for the given major.
        
        Args:
            course_code: Course code to validate
            major_index: Major index
            
        Returns:
            True if course exists, False otherwise
        """
        courses = self.get_courses_by_major(major_index)
        return course_code in courses
    
    def get_prerequisites(self, course_code: str, major_index: int) -> List[str]:
        """
        Get prerequisites for a course.
        
        Args:
            course_code: Course code
            major_index: Major index
            
        Returns:
            List of prerequisite course codes
        """
        course_info = self.get_course_info(course_code, major_index)
        if course_info:
            return course_info.get('prerequisites', [])
        return []
    
    def get_course_credits(self, course_code: str, major_index: int) -> int:
        """
        Get credit hours for a course.
        
        Args:
            course_code: Course code
            major_index: Major index
            
        Returns:
            Number of credit hours
        """
        course_info = self.get_course_info(course_code, major_index)
        if course_info:
            return course_info.get('credits', 0)
        return 0 