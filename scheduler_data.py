import os
import json

def parse_time(time_str):
    if not time_str or len(time_str) != 4 or not time_str.isdigit():
        return ''
    hour = int(time_str[:2])
    minute = int(time_str[2:])
    # Convert to 12-hour format if needed, but keep as H:MM
    return f"{hour}:{minute:02d}"

def extract_days(mt):
    days = ''
    if mt.get('monday'): days += 'M'
    if mt.get('tuesday'): days += 'T'
    if mt.get('wednesday'): days += 'W'
    if mt.get('thursday'): days += 'H'
    return days

def is_valid_meeting(mt):
    # Only consider meetings with at least one day and valid times
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
            name = entry.get('subjectDescription', '').strip()
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
# fall25_courses is now available for use


cs_courses = {
    'GENS101': {'name': 'Grand Challenges', 'credits': 4, 'prerequisites': [], 'weight': 1, 'year': 1, },
    'ENGL101': {'name': 'Academic English I', 'credits': 3, 'prerequisites': [], 'weight': 2, 'year': 1},
    'MATH111': {'name': 'Calculus I', 'credits': 4, 'prerequisites': [], 'weight': 2, 'year': 1},
    'CHEM115': {'name': 'General Chemistry I', 'credits': 4, 'prerequisites': [], 'weight': 2, 'year': 1},
    'GENS100': {'name': 'Academic Development & Success', 'credits': 1, 'prerequisites': [], 'weight': 1, 'year': 1},
    'ENGL102': {'name': 'Academic English II', 'credits': 3, 'prerequisites': ['ENGL101'], 'weight': 2, 'year': 1},
    'MATH112': {'name': 'Calculus II', 'credits': 4, 'prerequisites': ['MATH111'], 'weight': 3, 'year': 1},
    'PHYS121': {'name': 'University Physics I', 'credits': 4, 'prerequisites': ['MATH111'], 'weight': 2, 'year': 1},
    'COSC114': {'name': 'Intro to Computing Using Python', 'credits': 4, 'prerequisites': [], 'weight': 2, 'year': 1},   
    'COSC101': {'name': 'Foundations of Computer Science', 'credits': 3, 'prerequisites': ['COSC114'], 'weight': 3, 'year': 2,'available_in' :  {'fall', 'spring'}},
    'ECCE230': {'name': 'Object-Oriented Programming', 'credits': 4, 'prerequisites': ['COSC114'], 'weight': 3, 'year': 2,'available_in' :  {'fall', 'spring'}},
    'MATH204': {'name': 'Linear Algebra', 'credits': 3, 'prerequisites': ['MATH112'], 'weight': 2, 'year': 2},
    'MATH242': {'name': 'Intro to Probability and Statistics', 'credits': 3, 'prerequisites': ['MATH112'], 'weight': 2,'year': 2},
    'ENGR202': {'name': 'Data Science and AI', 'credits': 3, 'prerequisites': ['COSC114'], 'weight': 2, 'year': 2},
    'COSC201': {'name': 'Computer Systems Organization', 'credits': 3, 'prerequisites': ['COSC101'], 'weight': 3,'year': 2,'available_in' :  {'fall', 'spring'}},
    'ECCE342': {'name': 'Data Structures and Algorithms', 'credits': 3, 'prerequisites': ['ECCE230'], 'weight': 4, 'year': 2,'available_in' : {'fall', 'spring'}},
    'MATH232': {'name': 'Engineering Mathematics', 'credits': 3, 'prerequisites': ['ECCE230'], 'weight': 2, 'year': 2},
    'MATH214': {'name': 'Mathematical and Statistical Software', 'credits': 3, 'prerequisites': ['MATH242', 'MATH204'], 'weight': 2, 'year': 2},
    'MATH234': {'name': 'Discrete Mathematics', 'credits': 3, 'prerequisites': ['MATH112'], 'weight': 3,'year': 2},
    'BUSS322': {'name': 'Innovation and Entrepreneurship', 'credits': 3, 'prerequisites': [], 'weight': 4, 'year': 3, 'min_credits' : 60},
    'COSC301': {'name': 'Automata', 'credits': 3, 'prerequisites': ['COSC101', 'MATH234'], 'weight': 3, 'year': 3,'available_in' :  {'fall', 'spring'}},
    'ECCE336': {'name': 'Software Engineering', 'credits': 3, 'prerequisites': ['ECCE230'], 'weight': 3, 'year': 3,'available_in' :  {'fall', 'spring'}},
    'ECCE354': {'name': 'Operating Systems', 'credits': 3, 'prerequisites': ['COSC201'], 'weight': 3, 'year': 3,'available_in' : {'fall', 'spring'}},
    'COSC312': {'name': 'Algorithm Design and Analysis', 'credits': 3, 'prerequisites': ['COSC301', 'ECCE342'], 'weight': 3, 'year': 3,'available_in' :  {'fall', 'spring'}},
    'COSC320': {'name': 'Programming Languages', 'credits': 3, 'prerequisites': ['COSC301'], 'weight': 2,'year': 3,'available_in' :  {'fall', 'spring'}},
    'ECCE356': {'name': 'Computer Networks', 'credits': 4, 'prerequisites': ['COSC201'], 'weight': 3, 'year': 3,'available_in' :  {'fall', 'spring'}},
    'COSC330': {'name': 'Artificial Intelligence', 'credits': 3, 'prerequisites': ['ECCE230'], 'weight': 3, 'year': 3,'available_in' :  {'fall', 'spring'}},
    'COSC340': {'name': 'Computer Security', 'credits': 3, 'prerequisites': ['ECCE354'], 'weight': 3, 'year': 3,'available_in' :  {'fall', 'spring'}},
    'GENS300': {'name': 'Career Preparation', 'credits': 1, 'prerequisites': ['GENS100'], 'weight': 1,'year': 3},
    'ECCE434': {'name': 'Database Systems', 'credits': 3, 'prerequisites': ['ECCE336'], 'weight': 3, 'year': 3,'available_in' : {'spring'}},
    'COSC497': {'name': 'Senior Design Project I', 'credits': 3, 'prerequisites': ['COSC312'], 'weight': 4, 'sections': ['TT9-11'], 'min_credits' : 90, 'year': 4,'available_in' :  {'fall', 'spring'}},
    'COSC498': {'name': 'Senior Design Project II', 'credits': 3, 'prerequisites': ['COSC497'], 'weight': 4, 'sections': ['MW4-6'], 'year': 4,'available_in' : {'fall', 'spring'}},
    'TECH_ELECTIVE_1': {'name': 'Technical Elective 1', 'credits': 3, 'prerequisites': ['COSC330'], 'weight': 2, 'year': 4,'available_in' :  {'fall', 'spring'}},
    'TECH_ELECTIVE_2': {'name': 'Technical Elective 2', 'credits': 3, 'prerequisites': ['COSC320'], 'weight': 2, 'year': 4,'available_in' : {'fall', 'spring'}},
    'TECH_ELECTIVE_3': {'name': 'Technical Elective 3', 'credits': 3, 'prerequisites': ['COSC320','COSC330'], 'weight': 2, 'year': 4,'available_in' : {'fall', 'spring'}},
    'TECH_ELECTIVE_4': {'name': 'Technical Elective 4', 'credits': 3, 'prerequisites': ['COSC340'], 'weight': 2,'year': 4,'available_in' : {'spring'}},
    'TECH_ELECTIVE_5': {'name': 'Technical Elective 5', 'credits': 3, 'prerequisites': ['COSC312'], 'weight': 2, 'year': 4,'available_in' : {'fall'}},
    'GENS400': {'name': 'Enhancing Employability & Readiness', 'credits': 1, 'prerequisites': ['GENS300'], 'weight': 1, 'year': 4},
    'ENGR399' : {'name' : 'internship 1' , 'credits': 1, 'prerequisites': [], 'weight': 1, 'year': 3, 'min_credits': 60,'available_in' : {'summer'}},
    'ENGR399(2)' : {'name' : 'internship 2' , 'credits': 1, 'prerequisites': ['ENGR399'], 'weight': 1, 'year': 4, 'min_credits' : 90, 'available_in' : {'summer'}},
    'HUMAXXX' : {'name' : 'HUMA course' , 'credits': 3, 'prerequisites': [], 'weight': 2, 'year': 2},
    'BUXXX' : {'name' : 'BUSS course' , 'credits': 3, 'prerequisites': [], 'weight': 2, 'year': 2},
    'HUMA123' : {'name' : 'UAE studies' , 'credits': 3, 'prerequisites': [], 'weight': 2, 'year': 2},
}
ce_courses = {
    'GENS101': {'name': 'Grand Challenges', 'credits': 4, 'prerequisites': [], 'weight': 1, 'year': 1, },
    'ENGL101': {'name': 'Academic English I', 'credits': 3, 'prerequisites': [], 'weight': 2, 'year': 1},
    'MATH111': {'name': 'Calculus I', 'credits': 4, 'prerequisites': [], 'weight': 2, 'year': 1},
    'CHEM115': {'name': 'General Chemistry I', 'credits': 4, 'prerequisites': [], 'weight': 2, 'year': 1},
    'GENS100': {'name': 'Academic Development & Success', 'credits': 1, 'prerequisites': [], 'weight': 1, 'year': 1},
    'ENGL102': {'name': 'Academic English II', 'credits': 3, 'prerequisites': ['ENGL101'], 'weight': 2, 'year': 1},
    'MATH112': {'name': 'Calculus II', 'credits': 4, 'prerequisites': ['MATH111'], 'weight': 3, 'year': 1},
    'PHYS121': {'name': 'University Physics I', 'credits': 4, 'prerequisites': ['MATH111'], 'weight': 2, 'year': 1},
    'COSC114': {'name': 'Intro to Computing Using Python', 'credits': 4, 'prerequisites': [], 'weight': 2, 'year': 1},   
    'COSC101': {'name': 'Foundations of Computer Science', 'credits': 3, 'prerequisites': ['COSC114'], 'weight': 3, 'year': 2,'available_in' :  {'fall', 'spring'}},
    'ECCE230': {'name': 'Object-Oriented Programming', 'credits': 4, 'prerequisites': ['COSC114'], 'weight': 3, 'year': 2,'available_in' :  {'fall', 'spring'}},
    'MATH204': {'name': 'Linear Algebra', 'credits': 3, 'prerequisites': ['MATH112'], 'weight': 2, 'year': 2},
    'MATH242': {'name': 'Intro to Probability and Statistics', 'credits': 3, 'prerequisites': ['MATH112'], 'weight': 2,'year': 2},
    'ENGR202': {'name': 'Data Science and AI', 'credits': 3, 'prerequisites': ['COSC114'], 'weight': 2, 'year': 2},
    'COSC201': {'name': 'Computer Systems Organization', 'credits': 3, 'prerequisites': ['COSC101'], 'weight': 3,'year': 2,'available_in' :  {'fall', 'spring'}},
    'ECCE342': {'name': 'Data Structures and Algorithms', 'credits': 3, 'prerequisites': ['ECCE230'], 'weight': 4, 'year': 2,'available_in' : {'fall', 'spring'}},
    'MATH232': {'name': 'Engineering Mathematics', 'credits': 3, 'prerequisites': ['ECCE230'], 'weight': 2, 'year': 2},
    'MATH214': {'name': 'Mathematical and Statistical Software', 'credits': 3, 'prerequisites': ['MATH242', 'MATH204'], 'weight': 2, 'year': 2},
    'MATH234': {'name': 'Discrete Mathematics', 'credits': 3, 'prerequisites': ['MATH112'], 'weight': 3,'year': 2},
    'BUSS322': {'name': 'Innovation and Entrepreneurship', 'credits': 3, 'prerequisites': [], 'weight': 4, 'year': 3, 'min_credits' : 60},
    'COSC301': {'name': 'Automata', 'credits': 3, 'prerequisites': ['COSC101', 'MATH234'], 'weight': 3, 'year': 3,'available_in' :  {'fall', 'spring'}},
    'ECCE336': {'name': 'Software Engineering', 'credits': 3, 'prerequisites': ['ECCE230'], 'weight': 3, 'year': 3,'available_in' :  {'fall', 'spring'}},
    'ECCE354': {'name': 'Operating Systems', 'credits': 3, 'prerequisites': ['COSC201'], 'weight': 3, 'year': 3,'available_in' : {'fall', 'spring'}},
    'COSC312': {'name': 'Algorithm Design and Analysis', 'credits': 3, 'prerequisites': ['COSC301', 'ECCE342'], 'weight': 3, 'year': 3,'available_in' :  {'fall', 'spring'}},
    'COSC320': {'name': 'Programming Languages', 'credits': 3, 'prerequisites': ['COSC301'], 'weight': 2,'year': 3,'available_in' :  {'fall', 'spring'}},
    'ECCE356': {'name': 'Computer Networks', 'credits': 4, 'prerequisites': ['COSC201'], 'weight': 3, 'year': 3,'available_in' :  {'fall', 'spring'}},
    'COSC330': {'name': 'Artificial Intelligence', 'credits': 3, 'prerequisites': ['ECCE230'], 'weight': 3, 'year': 3,'available_in' :  {'fall', 'spring'}},
    'COSC340': {'name': 'Computer Security', 'credits': 3, 'prerequisites': ['ECCE354'], 'weight': 3, 'year': 3,'available_in' :  {'fall', 'spring'}},
    'GENS300': {'name': 'Career Preparation', 'credits': 1, 'prerequisites': ['GENS100'], 'weight': 1,'year': 3},
    'ECCE434': {'name': 'Database Systems', 'credits': 3, 'prerequisites': ['ECCE336'], 'weight': 3, 'year': 3,'available_in' : {'spring'}},
    'COSC497': {'name': 'Senior Design Project I', 'credits': 3, 'prerequisites': ['COSC312'], 'weight': 4, 'sections': ['TT9-11'], 'min_credits' : 90, 'year': 4,'available_in' :  {'fall', 'spring'}},
    'COSC498': {'name': 'Senior Design Project II', 'credits': 3, 'prerequisites': ['COSC497'], 'weight': 4, 'sections': ['MW4-6'], 'year': 4,'available_in' : {'fall', 'spring'}},
    'TECH_ELECTIVE_1': {'name': 'Feras elective', 'credits': 3, 'prerequisites': ['COSC330'], 'weight': 2, 'year': 4,'available_in' :  {'fall', 'spring'}},
    'TECH_ELECTIVE_2': {'name': 'Technical Elective 2', 'credits': 3, 'prerequisites': ['COSC320'], 'weight': 2, 'year': 4,'available_in' : {'fall', 'spring'}},
    'TECH_ELECTIVE_3': {'name': 'Technical Elective 3', 'credits': 3, 'prerequisites': ['COSC320','COSC330'], 'weight': 2, 'year': 4,'available_in' : {'fall', 'spring'}},
    'TECH_ELECTIVE_4': {'name': 'Technical Elective 4', 'credits': 3, 'prerequisites': ['COSC340'], 'weight': 2,'year': 4,'available_in' : {'spring'}},
    'TECH_ELECTIVE_5': {'name': 'Technical Elective 5', 'credits': 3, 'prerequisites': ['COSC312'], 'weight': 2, 'year': 4,'available_in' : {'fall'}},
    'GENS400': {'name': 'Enhancing Employability & Readiness', 'credits': 1, 'prerequisites': ['GENS300'], 'weight': 1, 'year': 4},
    'ENGR399' : {'name' : 'internship 1' , 'credits': 1, 'prerequisites': [], 'weight': 1, 'year': 3, 'min_credits': 60,'available_in' : {'summer'}},
    'ENGR399(2)' : {'name' : 'internship 2' , 'credits': 1, 'prerequisites': ['ENGR399'], 'weight': 1, 'year': 4, 'min_credits' : 90, 'available_in' : {'summer'}},
    'HUMAXXX' : {'name' : 'HUMA course' , 'credits': 3, 'prerequisites': [], 'weight': 2, 'year': 2},
    'BUXXX' : {'name' : 'BUSS course' , 'credits': 3, 'prerequisites': [], 'weight': 2, 'year': 2},
    'HUMA123' : {'name' : 'UAE studies' , 'credits': 3, 'prerequisites': [], 'weight': 2, 'year': 2},
}


plans= [cs_courses, ce_courses]

time_data = {
    'MATH242': {
        'name': 'Intro to Probability and Statistics',
        'credits': 3,
        'prerequisites': [],
        'weight': 2,
        'sections': [
            'MW9-10:30', 'MW11-12:30', 'MW1-2:30',
            'TH9-10:30', 'TH11-12:30', 'TH2-3:30'
        ]
        # No lab
    },
    'ENGR202': {
        'name': 'Data Science and AI',
        'credits': 3,
        'prerequisites': [],
        'weight': 2,
        'sections': [
            'MW2-3:30', 'MW4-5:30', 'TH12-1:30',
            'TH2-3:30', 'TH4-5:30'
        ],
        'labs': [
            'M9-11', 'T2-4', 'W4-6', 'H5-7', 'H2-4'
        ]
    },
    'COSC114': {
        'name': 'Intro to Computing Using Python',
        'credits': 4,
        'prerequisites': [],
        'weight': 2,
        'sections': [
            'MW1-2:30', 'MW3-4:30', 'MW5-6:30',
            'TH3-4:30', 'TH5-6:30'
        ],
        'labs': [
            'M4-6', 'W9-11', 'T12-2', 'H10-12', 'W1-3'
        ]
    },
    'PHYS121': {
        'name': 'University Physics I',
        'credits': 4,
        'prerequisites': [],
        'weight': 2,
        'sections': [
            'TH2-3:30', 'MW3-4:30', 'MW6-7:30',
            'TH4-5:30', 'MW10-11:30'
        ],
        'labs': [
            'T5-7', 'W4-6', 'T11-1', 'M2-4', 'H1-3'
        ]
    },
    'ENGL101': {
        'name': 'Academic English I',
        'credits': 3,
        'prerequisites': [],
        'weight': 1,
        'sections': [
            'MW9-10:30', 'MW11-12:30', 'TH10-11:30',
            'TH9-10:30', 'MW2-3:30'
        ]
        # No lab
    },
    'CHEM110': {
        'name': 'General Chemistry',
        'credits': 4,
        'prerequisites': [],
        'weight': 2,
        'sections': [
            'MW10-11:30', 'MW12-1:30', 'TH1-2:30',
            'TH3-4:30'
        ],
        'labs': [
            'M1-3', 'T3-5', 'W10-12', 'H9-11'
        ]
    },
    'CSCI200': {
        'name': 'Object-Oriented Programming',
        'credits': 4,
        'prerequisites': [],
        'weight': 2,
        'sections': [
            'MW8-9:30', 'MW2-3:30', 'TH11-12:30', 'TH1-2:30'
        ],
        'labs': [
            'M3-5', 'T9-11', 'W2-4', 'H4-6'
        ]
    }
}




