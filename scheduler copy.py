import pulp
import collections

class CourseScheduler:
    """
    CourseScheduler is responsible for generating optimal or feasible course plans for a university degree.
    It supports both greedy (semester-by-semester) and full-program optimization using Gurobi, respecting prerequisites, credit limits, course availability, and special constraints.
    """
    def __init__(self, courses, completed, required, max=18, min=12, semesters=15, starting=1, semester_type=None):
        """
        Initialize the CourseScheduler with course data, completed and required courses, and scheduling parameters.
        """
        self.courses= courses
        self.completed_courses= completed
        self.required_courses= required
        self.min_credits = min if min is not None else 0
        self.max_credits = max if max is not None else 18
        self.remaining_courses=  set(self.required_courses) -set(self.completed_courses)
        self.model= None
        self.model2=None
        self.model3=None
        self.total_semesters_remaining = semesters
        self.x= {} # for model 1
        self.x2= {} # for model 2
        self.y={}# for model 3
        self.starting_semester = starting 
        self.semester_type = semester_type  # NEW: store current semester type
        self.assign_importance()  # Always assign importance on initialization

        
  

   
    
    def build_model(self,alpha=3, beta=0.5, credit_target=15, penalty_weight=1.0, topo_penalty_weight=1.5):
        """
        Build and return a Gurobi model for scheduling courses in a single semester (next semester).
        This model selects a feasible set of courses for the next semester, respecting prerequisites, credit limits, and other constraints.
        Used in the greedy, semester-by-semester plan.
        """
        # Initialize Gurobi model
        self.model = pulp.LpProblem("NextSemesterScheduler", pulp.LpMaximize)
        self.x= {} 
        # Add binary variables for each course-section pair
        for course in self.remaining_courses:
            for section in self.courses[course]['sections']:
                self.x[(course, section)] = pulp.LpVariable(f"x_{course}_{section}", cat='Binary')

        # Add prerequisite constraints
        for i in self.remaining_courses:
            prerequistes=self.courses[i]['prerequisites']
            for j in prerequistes:
                if j in self.completed_courses:
                    continue 
                for section in self.courses[i]['sections']:
                    self.model += self.x[(i, section)] <= 0

        # Only one section per course can be taken
        for course in self.remaining_courses:
            self.model += pulp.lpSum(self.x[course,section] for section in self.courses[course]['sections']) <=1
            
        # Credit constraints for the semester
        total_credits_pre_sem= pulp.lpSum(self.courses[x]['credits']* self.x[x,y] for x in self.remaining_courses for y in self.courses[x]['sections']) 
        self.model += total_credits_pre_sem<= self.max_credits
        min_credits = self.min_credits if self.min_credits is not None else 0
        self.model += total_credits_pre_sem >= min_credits

        # Special cases: courses with min_credits requirements
        total_credits = pulp.lpSum(self.courses[course]['credits'] for course in self.completed_courses)
        special_cases = [i for i, j in self.courses.items() if 'min_credits' in j and i in self.remaining_courses]
        for course in  special_cases:
            min_credits = self.courses[course]['min_credits']
            if min_credits is not None and total_credits < min_credits:
                self.model += pulp.lpSum(self.x[course, section] for section in self.courses[course]['sections']) == 0
        
        # Soft credit target penalty
        deviation = pulp.LpVariable("deviation", lb=0)
        self.model += deviation >= total_credits_pre_sem - credit_target
        self.model += deviation >= credit_target - total_credits_pre_sem
        
        # Topological order penalty (soft constraint)
        topo_order = self.topological_sort_courses(list(self.remaining_courses), list(self.completed_courses))
        topo_index = {course: idx for idx, course in enumerate(topo_order)}
        # Penalize not picking lower-index (prerequisite) courses
        soft_penalty = pulp.lpSum(
            (1 - pulp.lpSum(self.x[(course, section)] for section in self.courses[course]['sections'])) * (topo_index[course] + 1)
            for course in self.remaining_courses
        )
        # Objective: maximize importance, minimize workload, penalize deviation and late prerequisites
        objective_expr = pulp.lpSum(self.x[(c,s)] * (alpha * self.courses[c]['importance'] - beta * self.courses[c].get('weight', 1)) for c in self.remaining_courses for s in self.courses[c]['sections'])
        self.model += objective_expr - penalty_weight * deviation - topo_penalty_weight * soft_penalty

        # Enforce semester availability constraint
        if self.semester_type is not None:
            for course in self.remaining_courses:
                available_in = self.courses[course].get('available_in', ['fall', 'spring', 'summer'])
                if self.semester_type.lower() not in [s.lower() for s in available_in]:
                    for section in self.courses[course]['sections']:
                        self.model += self.x[(course, section)] == 0

        # Strict internship constraint: if ENGR399 or ENGR399(2) is scheduled, no other courses can be scheduled
        for internship in ['ENGR399', 'ENGR399(2)']:
            if internship in self.remaining_courses:
                for int_sec in self.courses[internship]['sections']:
                    for course in self.remaining_courses:
                        if course == internship:
                            continue
                        for sec in self.courses[course]['sections']:
                            self.model += self.x[(course, sec)] <= 1 - self.x[(internship, int_sec)]
        return self.model


    
    def build_model2(self, desired_courses):
        """
        Build and return a Gurobi model for scheduling sections and labs for a given set of courses in a single semester.
        This model resolves time conflicts between sections/labs and ensures one section/lab per course is chosen.
        Used for detailed time/section scheduling after course selection.
        """
        self.model2 = pulp.LpProblem("Time Scheduler", pulp.LpMaximize)
        
        self.x2 = {}
        
       
        for course in desired_courses:
            sections = self.courses[course]['sections']
            labs = self.courses[course].get('labs', [])
        
            # add  sections
            for section in sections:
                self.x2[(course, section)] = pulp.LpVariable(f"x_{course}_sec_{section}", cat='Binary')
        
            # add lanbs
            for lab in labs:
                self.x2[(course, lab)] = pulp.LpVariable(f"x_{course}_lab_{lab}", cat='Binary')
    
            # one section consterain
            self.model2 += pulp.lpSum(self.x2[(course, sec)] for sec in sections) == 1
    
            # lab constrain 
            if labs:
                self.model2 += pulp.lpSum(self.x2[(course, lab)] for lab in labs) == 1
        
        # time conflict 
        all_vars = list(self.x2.keys())
        for i in range(len(all_vars)):
            c1, t1 = all_vars[i]
            for j in range(i + 1, len(all_vars)):
                c2, t2 = all_vars[j]
                if self.does_conflict(t1, t2):
                    self.model2 += self.x2[(c1, t1)] + self.x2[(c2, t2)] <= 1
        return self.model2
    


    
                
    def build_model3(self, alpha=2, beta=0.5, gamma=1.0, topo_penalty_weight=1.0):
        """
        Build and return a Gurobi model for scheduling all courses over all semesters (full degree plan).
        This model assigns each course to a semester, respecting prerequisites, credit limits, course availability, and special constraints (e.g., internships).
        Used for generating a complete multi-semester plan in one optimization.
        """
        # Prerequisite integrity check
        for course in self.remaining_courses:
            for prereq in self.courses[course]['prerequisites']:
                if prereq not in self.completed_courses and prereq not in self.remaining_courses:
                    print(f"WARNING: Prerequisite {prereq} for course {course} is neither completed nor scheduled. This may cause prerequisite logic errors.")
        self.model3 = pulp.LpProblem("FullPlanScheduler", pulp.LpMinimize)
    
        semesters = list(range(self.starting_semester, self.total_semesters_remaining + 1))  
        self.y = {}
    
        for course in self.remaining_courses:
            for sem in semesters:
                self.y[(course, sem)] = pulp.LpVariable(f"y_{course}_sem{sem}", cat='Binary')
        # must take all cources once 
        for course in self.remaining_courses:
            self.model3 += pulp.lpSum(self.y[course, s] for s in semesters) == 1

        # ENFORCE INTERNSHIP SEMESTER RESTRICTIONS
        internship_courses = {'ENGR399', 'ENGR399(2)'}
        for course in self.remaining_courses:
            for s in semesters:
                if s in [9, 12]:
                    # Only allow internship courses in semesters 9 and 12
                    if course not in internship_courses:
                        self.model3 += self.y[(course, s)] == 0
                else:
                    # Only allow non-internship courses in other semesters
                    if course in internship_courses:
                        self.model3 += self.y[(course, s)] == 0

        # FORCE INTERNSHIPS IF ELIGIBLE
        # ENGR399 in 9, ENGR399(2) in 12
        if 'ENGR399' in self.remaining_courses:
            # Check if prerequisites and min_credits are met for ENGR399 in 9
            prereqs = self.courses['ENGR399']['prerequisites']
            min_credits = self.courses['ENGR399'].get('min_credits')
            prereq_met = True
            for pr in prereqs:
                if pr in self.remaining_courses:
                    prereq_met = False
            if min_credits is not None:
                # Credits up to semester 9
                credits_up_to_9 = pulp.lpSum(self.courses[c]['credits'] * self.y[c, t] for c in self.remaining_courses for t in semesters if t < 9)
                self.model3 += self.y['ENGR399', 9] * min_credits <= credits_up_to_9
            if prereq_met:
                self.model3 += self.y['ENGR399', 9] == 1
        if 'ENGR399(2)' in self.remaining_courses:
            # Check if prerequisites and min_credits are met for ENGR399(2) in 12
            prereqs = self.courses['ENGR399(2)']['prerequisites']
            min_credits = self.courses['ENGR399(2)'].get('min_credits')
            prereq_met = True
            for pr in prereqs:
                if pr in self.remaining_courses:
                    prereq_met = False
            if min_credits is not None:
                credits_up_to_12 = pulp.lpSum(self.courses[c]['credits'] * self.y[c, t] for c in self.remaining_courses for t in semesters if t < 12)
                self.model3 += self.y['ENGR399(2)', 12] * min_credits <= credits_up_to_12
            if prereq_met:
                self.model3 += self.y['ENGR399(2)', 12] == 1

        # prerequsite constrain 
        for course in self.remaining_courses:
            prereqs = self.courses[course]['prerequisites']
            for prereq in prereqs:
                if prereq in self.remaining_courses:
                    self.model3 += pulp.lpSum(s * self.y[(course, s)] for s in semesters) >= pulp.lpSum(s * self.y[(prereq, s)] for s in semesters)+1
        #credits per sem constrain

        for s in semesters:
            total_credits = pulp.lpSum(self.y[(course, s)] * self.courses[course]['credits']for course in self.remaining_courses)
            if s%3==0:# so if summer....
                 self.model3 += total_credits <= 6
            elif s>12:# for the fifth year, max is 18 but min is 0 
                 self.model3 += total_credits <= self.max_credits
            else:  
                self.model3 += total_credits <= self.max_credits
                self.model3 += total_credits >= self.min_credits

        # restricted cources constrain e.g sdp
        
        credits_up_to_semester = {s: pulp.lpSum(self.courses[c]['credits'] * self.y[c, t] for c in self.remaining_courses for t in semesters if t < s) for s in semesters }

        special_cases = [i for i, j in self.courses.items() if 'min_credits' in j]
        for course in special_cases:
            required_credits = self.courses[course]['min_credits']
            if required_credits is None:
                continue
            for s in semesters:
                if (course, s) in self.y:
                    self.model3 += self.y[course, s] * required_credits <= credits_up_to_semester[s]
                        
        # u cant take courses with internships 
        if 'ENGR399' in self.remaining_courses:
            self.model3 += pulp.lpSum(self.y[c, s] for c in self.remaining_courses if c != 'ENGR399') <= 100 * (1 - self.y['ENGR399', s])
        if 'ENGR399(2)' in self.remaining_courses:
            self.model3 += pulp.lpSum(self.y[c, s] for c in self.remaining_courses if c != 'ENGR399(2)') <= 100 * (1 - self.y['ENGR399(2)', s])


        # availabilty constrain 
        offered_sems= {'fall', 'spring' , 'summer'}
        for course in self.remaining_courses:
            if 'available_in' not in self.courses[course]:
                continue
            not_available_in = offered_sems - set(self.courses[course]['available_in'])
            for s in semesters:
                if s % 3 == 1 and 'fall' in not_available_in:
                    self.model3 += self.y[course, s] == 0
                elif s % 3 == 2 and 'spring' in not_available_in:
                    self.model3 += self.y[course, s] == 0
                elif s % 3 == 0 and 'summer' in not_available_in:
                    self.model3 += self.y[course, s] == 0
            

       
       
        # IMPORTANCE 
        #so since its multiplied by s (semester), to get the lowest score pssible it takes high importance courses sooner 
        importance_term = pulp.lpSum(
            self.y[(course, s)] *self.courses[course].get('importance', 1) * s
            for course in self.remaining_courses
            for s in semesters
        )

        # PENALTY 
        # to minimize this, it would rather make the (taken semester - prefered semster) = 0 or as close to 0 as possible 
        penalties = {    (c, s): abs(self.year_of_semester(s) - self.courses[c].get('year', self.year_of_semester(s)))  for c in self.remaining_courses
                for s in semesters  }
        penalty_term = pulp.lpSum(
            self.y[(course, s)] *  penalties[(course, s)]
            for course in self.remaining_courses
            for s in semesters if s<13
        )

        # TOPOLOGICAL SORT SOFT CONSTRAINT
        topo_order = self.topological_sort_courses(list(self.remaining_courses), list(self.completed_courses))
        topo_index = {course: idx for idx, course in enumerate(topo_order)}
        topological_penalty = pulp.lpSum(
            self.y[(course, s)] * s * (topo_index[course] + 1)
            for course in self.remaining_courses
            for s in semesters
        )

        # BALANCE WORKLOAD 
        taken_sems = [s for s in semesters if s % 3 != 0]
        avg_weight = pulp.lpSum(self.y[(c, s)] * self.courses[c]['weight'] for s in taken_sems for c in self.remaining_courses) / len(taken_sems)
        # Absolute deviation penalty for workload balance
        deviation_vars = {}
        for s in taken_sems:
            workload_s = pulp.lpSum(self.y[c, s] * self.courses[c]['weight'] for c in self.remaining_courses)
            deviation = pulp.LpVariable(f"workload_dev_sem_{s}", lowBound=0)
            self.model3 += deviation >= workload_s - avg_weight
            self.model3 += deviation >= avg_weight - workload_s
            deviation_vars[s] = deviation
        workload_balance_term = pulp.lpSum(deviation_vars[s] for s in taken_sems)

        objective_expr = alpha*importance_term + beta*workload_balance_term + gamma* penalty_term + topo_penalty_weight * topological_penalty
        self.model3 += objective_expr

        # REQUIRE AT LEAST 130 CREDITS FOR GRADUATION
        # total_credits_all = pulp.lpSum(self.y[(course, s)] * self.courses[course]['credits'] for course in self.remaining_courses for s in semesters)
        # self.model3 += total_credits_all >= 130
        return self.model3
        
        
    '''
        objective_expr = pulp.lpSum(
        (self.y[(course, s)] * s * (beta * self.courses[course].get('weight', 1) - alpha * self.courses[course].get('importance', 1) )- gamma * penalties[(course, s)])
        for course in self.remaining_courses 
        for s in semesters
    )'''

    def assign_importance(self):
        """
        Assigns an 'importance' score to each course based on how many other courses depend on it (directly or indirectly).
        A higher importance means the course is a prerequisite for more courses, so it should be prioritized earlier in the schedule.
        """
        def count_dependents(target_course):
            visited = set()
            stack = [target_course]
            count = 0
            while stack:
                current = stack.pop()
                for course, info in self.courses.items():
                    if current in info.get('prerequisites', []) and course not in visited:
                        visited.add(course)
                        count += 1
                        stack.append(course)
            return count
        for course in self.courses:
            self.courses[course]['importance'] = count_dependents(course) + 1


    # --- Utility Functions ---
    @staticmethod
    def parse_time(string):
        """
        Parse a time string (e.g., 'MW10-11:15') into days, start, and end times.
        """
        i=0
        while i<len(string) and not string[i].isdigit():
            i+=1
        days=list(string[:i])
    
        temp= string[i:]
        start, end = temp.split('-')
        return days, start, end

    @staticmethod
    def convert_to_set(str):
        """
        Convert a time string to a set of 15-minute time slots for conflict checking.
        """
        def to_minutes(t):
            mins_diff=0
            if ':' in t:
                hour, minute = map(int, t.split(':'))
            else:
                hour, minute = int(t), 0
            if hour >= 9:
                mins_diff+= (hour-9)  * 60 
            else:
                mins_diff+= 180+ hour*60
            mins_diff+= minute
            return mins_diff
        days, start, end = CourseScheduler.parse_time(str)
        start_min = to_minutes(start)
        end_min = to_minutes(end)
    
        start_point= start_min//15
        end_point= end_min//15
        
        time_set= set()
        dic=  {'M': 0, 'T': 48, 'W': 96, 'H': 144} 
        for i in days:
            for j in  range(start_point, end_point):
                time_set.add(dic[i] + j)
        return time_set

    @staticmethod    
    def does_conflict(t1, t2):
        """
        Return True if two time strings conflict (overlap in time slots).
        """
        return not CourseScheduler.convert_to_set(t1).isdisjoint(CourseScheduler.convert_to_set(t2))

    @staticmethod
    def year_of_semester(s):
        """
        Return the academic year (1-based) for a given semester number.
        """
        return int((s-1) // 3 + 1 )

    # --- Debug and Output Functions ---
    def debug_unscheduled_course(self, course_code, completed_courses, all_semesters=None):
        """
        Print eligibility reasons for an unscheduled course in each semester, simulating credit accumulation.
        """
        print(f"\nDebugging course: {course_code} - {self.courses[course_code]['name']}")
        running_completed = set(completed_courses)
        for sem in range(2, self.total_semesters_remaining + 1):
            sem_type = self.get_semester_type(sem)
            prereqs = self.courses[course_code]['prerequisites']
            available_in = self.courses[course_code].get('available_in', ["fall", "spring", "summer"])
            min_credits = self.courses[course_code].get('min_credits')
            reasons = []
            if not all(pr in running_completed for pr in prereqs):
                reasons.append(f"missing prerequisites: {', '.join([pr for pr in prereqs if pr not in running_completed])}")
            if sem_type.lower() not in [s.lower() for s in available_in]:
                reasons.append(f"not offered in {sem_type}")
            if min_credits is not None:
                total_credits = sum(self.courses[cc]['credits'] for cc in running_completed)
                if total_credits < min_credits:
                    reasons.append(f"requires {min_credits} credits, has {total_credits}")
            if reasons:
                print(f"  Semester {sem} ({sem_type}): NOT ELIGIBLE ({'; '.join(reasons)})")
            else:
                print(f"  Semester {sem} ({sem_type}): ELIGIBLE")
            # Simulate taking courses in this semester
            if all_semesters and sem-1 < len(all_semesters):
                running_completed.update(all_semesters[sem-1])

    def get_full_solution(self):
        """
        Print the full solution for the multi-semester plan (model3), including course assignments and objective terms.
        Output format matches semester_by_semester_plan.
        """
        if not hasattr(self, 'model3') or pulp.LpStatus[self.model3.status] != "Optimal":
            print("Model3 is not solved or not optimal.")
            return
        semester_courses = {s: [] for s in range(1, self.total_semesters_remaining + 1)}
        semester_credits = {s: 0 for s in range(1, self.total_semesters_remaining + 1)}
        cumulative_credits = 0
        course_semester = {}
        for (course, s), var in self.y.items():
            if var.varValue > 0.5:
                semester_courses[s].append(course)
                semester_credits[s] += self.courses[course]['credits']
                course_semester[course] = s
        print("==============================")
        print("     Full Degree Plan Output    ")
        print("==============================\n")
        total_credits_all = 0
        for s in range(2, self.total_semesters_remaining + 1):
            courses = semester_courses[s]
            sem_type = self.get_semester_type(s)
            if not courses:
                print(f"Semester {s} ({sem_type}): No courses scheduled.\n")
                continue
            course_lines = []
            for c in courses:
                course = self.courses.get(c)
                if course:
                    course_lines.append(f"  - {c}: {course['name']} ({course['credits']} credits)")
            sem_credits = semester_credits[s]
            total_credits_all += sem_credits
            print(f"Semester {s} ({sem_type}):")
            for line in course_lines:
                print(line)
            print(f"  Total credits: {sem_credits}\n")
        print("==============================")
        print(f"Total credits earned: {total_credits_all}")
        print(f"Number of semesters used: {len([s for s in semester_courses.values() if s])}")
        print("==============================\n")
        # Prerequisite debug print
        print("Prerequisite schedule check:")
        for course, s in course_semester.items():
            prereqs = self.courses[course]['prerequisites']
            if prereqs:
                for pr in prereqs:
                    pr_sem = course_semester.get(pr, None)
                    if pr_sem is not None:
                        print(f"  {course} (semester {s}) <- {pr} (semester {pr_sem})")
                    else:
                        print(f"  {course} (semester {s}) <- {pr} (NOT SCHEDULED)")
        # If there are still remaining courses, print them
        all_scheduled = set()
        for course_list in semester_courses.values():
            all_scheduled.update(course_list)
        remaining = self.remaining_courses - all_scheduled
        if remaining:
            print("The following courses could not be scheduled due to constraints:")
            for c in remaining:
                print(f"  - {c}: {self.courses[c]['name']}")
            # Debug each unscheduled course
            for c in remaining:
                self.debug_unscheduled_course(c, all_scheduled)

    def topological_sort_courses(self, remaining, completed):
        """
        Return a list of courses in topological order (prerequisites before dependents) for the given remaining and completed courses.
        """
        # Build graph
        graph = collections.defaultdict(list)
        in_degree = collections.defaultdict(int)
        for c in remaining:
            for prereq in self.courses[c]['prerequisites']:
                if prereq in remaining or prereq in completed:
                    graph[prereq].append(c)
                    in_degree[c] += 1
        # Courses with no prerequisites (or all prereqs completed)
        queue = [c for c in remaining if in_degree[c] == 0 and all(pr in completed for pr in self.courses[c]['prerequisites'])]
        sorted_courses = []
        while queue:
            node = queue.pop(0)
            sorted_courses.append(node)
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0 and all(pr in completed for pr in self.courses[neighbor]['prerequisites']):
                    queue.append(neighbor)
        # If there are cycles or unsatisfiable prereqs, append the rest
        for c in remaining:
            if c not in sorted_courses:
                sorted_courses.append(c)
        return sorted_courses

    def get_semester_type(self, sem_num):
        if sem_num % 3 == 1:
            return 'Fall'
        elif sem_num % 3 == 2:
            return 'Spring'
        else:
            return 'Summer'

    def semester_by_semester_plan(self, credit_target=15, penalty_weight=1.0):
        """
        Greedy scheduler: plans courses semester by semester, printing the plan and eligibility at each step.
        """
        fixed_first_semester = ["GENS101", "ENGL101", "MATH111", "GENS100", "CHEM115"]
        completed = set(fixed_first_semester)
        all_semesters = [fixed_first_semester]
        print("\n==============================")
        print("  KU CS Degree Plan Scheduler  ")
        print("==============================\n")
        print("First Semester (fixed by registration office):")
        for code in fixed_first_semester:
            c = self.courses.get(code)
            if c:
                print(f"  - {code}: {c['name']} ({c['credits']} credits)")
        total_credits = sum(self.courses[code]['credits'] for code in fixed_first_semester if code in self.courses)
        print(f"  Total credits: {total_credits}\n")
        sem = 2
        while sem <= 12:
            remaining = set(self.courses.keys()) - completed
            sem_type = self.get_semester_type(sem)
            max_credits = 6 if sem_type == 'Summer' else self.max_credits
            min_credits = 0 if sem_type == 'Summer' else self.min_credits
            print(f"\n--- Semester {sem} ({sem_type}) ---")
            # Topological sort: strictly prioritize prerequisites
            sorted_remaining = self.topological_sort_courses(remaining, completed)
            # Only allow eligible courses (prereqs met, available, min_credits met)
            eligible_courses = []
            for c in sorted_remaining:
                course = self.courses[c]
                prereqs = course['prerequisites']
                available_in = course.get('available_in', ["fall", "spring", "summer"])
                min_credits = course.get('min_credits')
                reasons = []
                if not all(pr in completed for pr in prereqs):
                    reasons.append(f"missing prerequisites: {', '.join([pr for pr in prereqs if pr not in completed])}")
                if sem_type.lower() not in [s.lower() for s in available_in]:
                    reasons.append(f"not offered in {sem_type}")
                if min_credits is not None:
                    total_credits = sum(self.courses[cc]['credits'] for cc in completed)
                    if total_credits < min_credits:
                        reasons.append(f"requires {min_credits} credits, has {total_credits}")
                if not reasons:
                    eligible_courses.append(c)
            # Only pass eligible courses to the scheduler
            semester_courses = []
            if eligible_courses:
                scheduler = CourseScheduler(self.courses, completed, set(eligible_courses), max_credits, min_credits, self.total_semesters_remaining, self.starting_semester, semester_type=sem_type)
                scheduler.remaining_courses = set(eligible_courses)
                scheduler.build_model(credit_target=credit_target, penalty_weight=penalty_weight)
                scheduler.model.solve()
                if pulp.LpStatus[scheduler.model.status] == "Optimal":
                    semester_courses = [c for c in eligible_courses if any(scheduler.x[(c, s)].varValue > 0.5 for s in self.courses[c]['sections'])]
                    completed.update(semester_courses)
            all_semesters.append(semester_courses)
            sem += 1
        # Print the full plan
        print("==============================")
        print("     Full Degree Plan Output    ")
        print("==============================\n")
        total_credits_all = 0
        for i, sem_courses in enumerate(all_semesters, 1):
            sem_type = self.get_semester_type(i)
            if not sem_courses:
                print(f"Semester {i} ({sem_type}): No courses scheduled.\n")
                continue
            course_lines = []
            for c in sem_courses:
                course = self.courses.get(c)
                if course:
                    course_lines.append(f"  - {c}: {course['name']} ({course['credits']} credits)")
            sem_credits = sum(self.courses[c]['credits'] for c in sem_courses if c in self.courses)
            total_credits_all += sem_credits
            print(f"Semester {i} ({sem_type}):")
            for line in course_lines:
                print(line)
            print(f"  Total credits: {sem_credits}\n")
        print("==============================")
        print(f"Total credits earned: {total_credits_all}")
        print(f"Number of semesters used: {len([s for s in all_semesters if s])}")
        print("==============================\n")
        # If there are still remaining courses, print them
        remaining = set(self.courses.keys()) - completed
        if remaining:
            print("The following courses could not be scheduled due to constraints:")
            for c in remaining:
                print(f"  - {c}: {self.courses[c]['name']}")
            # Debug each unscheduled course
            for c in remaining:
                self.debug_unscheduled_course(c, completed, all_semesters)

    def print_courses(self):
        """
        Print all course codes and names in the scheduler.
        """
        print("Courses in scheduler:")
        for code, info in self.courses.items():
            print(f"  {code}: {info['name']}")

def load_courses_dict_from_json(json_path: str) -> dict:
    """Load courses from a JSON file and return a dict-of-dicts for legacy CourseScheduler."""
    import json
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    courses = {}
    for code, info in data.items():
        # Default to one section 'A' if not present
        sections = info.get('sections', ['A'])
        # Default year to 1 if null
        year = info.get('year', 1)
        if year is None:
            year = 1
        courses[code] = {
            'name': info['name'],
            'credits': info['credits'],
            'prerequisites': info['prerequisites'],
            'weight': info.get('weight', 1),
            'year': year,
            'sections': sections,
            'importance': info.get('importance', 1),
            'min_credits': info.get('min_credits'),
            'available_in': info.get('available_in'),
        }
    return courses

# Usage example
if __name__ == "__main__":
    fixed_first_semester = ["GENS101", "ENGL101", "MATH111", "GENS100", "CHEM115"]
    courses = load_courses_dict_from_json("courses.json")
    completed = set(fixed_first_semester)
    required = set(courses.keys())
    scheduler = CourseScheduler(courses, completed, required)
    print("Courses passed to model3 (remaining courses):", scheduler.remaining_courses)
    model3 = scheduler.build_model3()
    result_status = model3.solve()
    print("Solver status:", pulp.LpStatus[model3.status])
    # Print fixed first semester
    print("\n==============================")
    print("  KU CS Degree Plan Scheduler  ")
    print("==============================\n")
    print("First Semester (fixed by registration office):")
    for code in fixed_first_semester:
        c = courses.get(code)
        if c:
            print(f"  - {code}: {c['name']} ({c['credits']} credits)")
    total_credits = sum(courses[code]['credits'] for code in fixed_first_semester if code in courses)
    print(f"  Total credits: {total_credits}\n")
    scheduler.get_full_solution()
    # Uncomment below to test greedy semester-by-semester plan
    # scheduler.semester_by_semester_plan(credit_target=15, penalty_weight=1.0)