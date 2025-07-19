import os
import json
from scheduler_data import plans

def load_fall25_courses(data_dir='courses_fall25'):
    all_courses = {}
    total_files = 0
    total_entries = 0
    # Temporary mapping to collect prerequisites per course
    course_prereqs = {}
    # Build a mapping from all plans for quick lookup
    plan_lookup = {}
    for plan in plans:
        plan_lookup.update(plan)
    for filename in os.listdir(data_dir):
        if filename.endswith('.json'):
            total_files += 1
            with open(os.path.join(data_dir, filename), 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
                    continue
                entries = data.get('data', [])
                print(f"{filename}: {len(entries)} entries")
                total_entries += len(entries)
                for entry in entries:
                    section_id = entry.get('id')
                    course_code = entry.get('subjectCourse')
                    if section_id is None or not course_code:
                        continue
                    # Collect prerequisites if present
                    prereqs = entry.get('prerequisites')
                    if prereqs is not None:
                        if course_code not in course_prereqs:
                            course_prereqs[course_code] = set()
                        # Accept both list and comma-separated string
                        if isinstance(prereqs, list):
                            course_prereqs[course_code].update(prereqs)
                        elif isinstance(prereqs, str):
                            course_prereqs[course_code].update([p.strip() for p in prereqs.split(',') if p.strip()])
                    # Get extra attributes from plan if available
                    plan_info = plan_lookup.get(course_code, {})
                    weight = plan_info.get('weight', 1)
                    year = plan_info.get('year', 1)
                    available_in = plan_info.get('available_in', None)
                    # Initialize course if not present
                    if course_code not in all_courses:
                        all_courses[course_code] = {
                            'name': entry.get('courseTitle', course_code),
                            'credits': entry.get('creditHours') or 0,
                            'sections': {},
                            'labs': [],
                            'weight': weight,
                            'year': year,
                            'available_in': list(available_in) if available_in else None
                        }
                    # Extract only important fields for the section
                    section_info = {
                        'id': section_id,
                        'subject': entry.get('subject'),
                        'subjectDescription': entry.get('subjectDescription'),
                        'courseNumber': entry.get('courseNumber'),
                        'courseTitle': entry.get('courseTitle'),
                        'sequenceNumber': entry.get('sequenceNumber'),
                        'scheduleTypeDescription': entry.get('scheduleTypeDescription'),
                        'creditHours': entry.get('creditHours'),
                        'faculty': [f.get('displayName') for f in entry.get('faculty', []) if f.get('displayName')],
                        'enrollment': entry.get('enrollment'),
                        'maximumEnrollment': entry.get('maximumEnrollment'),
                        'seatsAvailable': entry.get('seatsAvailable'),
                        'meetingsFaculty': []
                    }
                    # Extract meeting info for each meeting
                    for meeting in entry.get('meetingsFaculty', []):
                        mt = meeting.get('meetingTime', {})
                        meeting_info = {
                            'beginTime': mt.get('beginTime'),
                            'endTime': mt.get('endTime'),
                            'days': [d for d in ['monday','tuesday','wednesday','thursday','friday','saturday','sunday'] if mt.get(d, False)],
                            'room': mt.get('room'),
                            'building': mt.get('buildingDescription'),
                        }
                        section_info['meetingsFaculty'].append(meeting_info)
                    # Place in labs or sections
                    if section_info['scheduleTypeDescription'] and section_info['scheduleTypeDescription'].lower() == 'lab':
                        all_courses[course_code]['labs'].append(str(section_id))
                    else:
                        all_courses[course_code]['sections'][str(section_id)] = section_info
    # Add prerequisites to each course
    for code, course in all_courses.items():
        course['prerequisites'] = list(course_prereqs.get(code, []))
    print(f"Loaded {sum(len(c['sections']) for c in all_courses.values())} sections from {total_files} files with {total_entries} total entries.")
    return all_courses

if __name__ == "__main__":
    data = load_fall25_courses()
    # Print the first course and its sections for inspection
    for course_code, course in list(data.items())[:1]:
        print(json.dumps({course_code: course}, indent=2, ensure_ascii=False)) 