import os
import json
import pprint

def parse_time(time_str):
    if not time_str or len(time_str) != 4 or not time_str.isdigit():
        return ''
    hour = int(time_str[:2])
    minute = int(time_str[2:])
    # Convert to 12-hour format
    hour_12 = hour % 12
    if hour_12 == 0:
        hour_12 = 12
    return f"{hour_12}:{minute:02d}"

def extract_days(mt):
    days = ''
    if mt.get('monday'): days += 'M'
    if mt.get('tuesday'): days += 'T'
    if mt.get('wednesday'): days += 'W'
    if mt.get('thursday'): days += 'H'
    return days

def is_valid_meeting(mt):
    return any([mt.get('monday'), mt.get('tuesday'), mt.get('wednesday'), mt.get('thursday')]) and mt.get('beginTime') and mt.get('endTime')

fall25_courses = {}

json_dir = os.path.join(os.path.dirname(__file__), 'courses_fall25')
for i in range(1, 25):
    fname = f'searchResults{i}.json'
    fpath = os.path.join(json_dir, fname)
    if not os.path.exists(fpath):
        continue
    with open(fpath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for entry in data.get('data', []):
            code = f"{entry.get('subject', '').strip()}{entry.get('courseNumber', '').strip()}"
            name = entry.get('courseTitle', '').strip()
            if not code:
                continue
            if code not in fall25_courses:
                fall25_courses[code] = {'name': name, 'sections': [], 'labs': []}
            meetings = entry.get('meetingsFaculty', [])
            for meet in meetings:
                mt = meet.get('meetingTime', {})
                if not is_valid_meeting(mt):
                    continue
                days = extract_days(mt)
                if not days:
                    continue
                start = parse_time(mt.get('beginTime'))
                end = parse_time(mt.get('endTime'))
                if not start or not end:
                    continue
                time_str = f"{days}{start}-{end}"
                if len(days) == 1:
                    if time_str not in fall25_courses[code]['labs']:
                        fall25_courses[code]['labs'].append(time_str)
                elif len(days) >= 2:
                    if time_str not in fall25_courses[code]['sections']:
                        fall25_courses[code]['sections'].append(time_str)

# Write the result to a file as a Python variable
with open('fall25_courses_data.py', 'w', encoding='utf-8') as out:
    out.write('fall25_courses = ')
    pprint.pprint(fall25_courses, stream=out) 