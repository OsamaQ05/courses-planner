import gurobipy as gp
from gurobipy import GRB
import collections

class CourseScheduler:
    def __init__(self, courses, completed, required, max=18,min=12, semesters=15, starting=1, semester_type=None):
        self.courses= courses
        self.completed_courses= completed
        self.required_courses= required
        self.max_credits= max
        self.min_credits= min
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

        
  

   
    
    def build_model(self,alpha=3, beta=0.5, credit_target=15, penalty_weight=1.0, topo_penalty_weight=1.0):
        self.model = gp.Model("NextSemesterScheduler")
        self.model.setParam('OutputFlag', 1) 
        # here we add the varibles into the model, in this case they r the  remaing courses 
        self.x= {} 
        for course in self.remaining_courses:
            for section in self.courses[course]['sections']:
                self.x[(course, section)] = self.model.addVar(vtype= GRB.BINARY, name= f"x_{course}_{section}")

        

        # now we add the constrains. we will do prerequsites and max credits hours for now and the others later (like time conflicts) 
        #prereusite constrain:
        
        for i in self.remaining_courses:
            prerequistes=self.courses[i]['prerequisites']
            for j in prerequistes:
                if j in self.completed_courses:
                    continue 
                for section in self.courses[i]['sections']:
                    self.model.addConstr(self.x[(i, section)] <= 0)

        #section constrain 
        for course in self.remaining_courses:
            self.model.addConstr(gp.quicksum(self.x[course,section] for section in self.courses[course]['sections']) <=1)
            
        #credit constrain                          
        total_credits_pre_sem= gp.quicksum(self.courses[x]['credits']* self.x[x,y] for x in self.remaining_courses for y in self.courses[x]['sections']) 
        self.model.addConstr(total_credits_pre_sem<= self.max_credits)
        self.model.addConstr(total_credits_pre_sem >= self.min_credits)
        
        # time conflics 
        '''
        r=list(self.remaining_courses)
        length= len(self.remaining_courses)
        for i in range(length):
            course=r[i]
            for j in range(i+1, length):
                course2=r[j]
                for section in self.courses[course]['sections']:
                    for section2 in self.courses[course2]['sections']:
                        if self.does_conflict(section,section2):
                            self.model.addConstr(self.x[(course,section)]+self.x[(course2,section2)]<=1)
        '''
        # special cases constrain 
        total_credits =__builtins__.sum(self.courses[course]['credits'] for course in self.completed_courses)
        special_cases = [i for i, j in self.courses.items() if 'min_credits' in j and i in self.remaining_courses]
        for course in  special_cases:
            min_credits = self.courses[course]['min_credits']
            if min_credits is not None and total_credits < min_credits:
                self.model.addConstr(gp.quicksum(self.x[course, section] for section in self.courses[course]['sections']) == 0)
        
        # Soft credit target penalty
        deviation = self.model.addVar(lb=0, name="deviation")
        self.model.addConstr(deviation >= total_credits_pre_sem - credit_target, name="dev_pos")
        self.model.addConstr(deviation >= credit_target - total_credits_pre_sem, name="dev_neg")
        
        # Topological order penalty (soft constraint)
        topo_order = self.topological_sort_courses(list(self.remaining_courses), list(self.completed_courses))
        topo_index = {course: idx for idx, course in enumerate(topo_order)}
        # For each course, penalize scheduling it later than its topo index (relative to the semester number)
        # We'll use the first section as a proxy for when the course is scheduled (since only one section can be chosen)
        soft_penalty = gp.quicksum(
            self.x[(course, self.courses[course]['sections'][0])] * max(0, (1) - (topo_index[course] + 1))
            for course in self.remaining_courses
        )  # This is a placeholder; see below for a better approach
        # Since we don't have semester numbers in this model, we can only encourage lower-index courses to be picked
        # So, penalize not picking lower-index courses
        soft_penalty = gp.quicksum(
            (1 - gp.quicksum(self.x[(course, section)] for section in self.courses[course]['sections'])) * (topo_index[course] + 1)
            for course in self.remaining_courses
        )
        # Objective
        objective_expr = gp.quicksum(self.x[(c,s)] * (alpha * self.courses[c]['importance'] - beta * self.courses[c].get('weight', 1)) for c in self.remaining_courses for s in self.courses[c]['sections'])
        self.model.setObjective(objective_expr - penalty_weight * deviation - topo_penalty_weight * soft_penalty, GRB.MAXIMIZE)

        # Enforce semester availability constraint
        if self.semester_type is not None:
            for course in self.remaining_courses:
                available_in = self.courses[course].get('available_in', ['fall', 'spring', 'summer'])
                if self.semester_type.lower() not in [s.lower() for s in available_in]:
                    for section in self.courses[course]['sections']:
                        self.model.addConstr(self.x[(course, section)] == 0)

        # Strict internship constraint: if ENGR399 or ENGR399(2) is scheduled, no other courses can be scheduled
        for internship in ['ENGR399', 'ENGR399(2)']:
            if internship in self.remaining_courses:
                for int_sec in self.courses[internship]['sections']:
                    for course in self.remaining_courses:
                        if course == internship:
                            continue
                        for sec in self.courses[course]['sections']:
                            self.model.addConstr(self.x[(course, sec)] <= 1 - self.x[(internship, int_sec)])

        return self.model


    
    def build_model2(self, desired_courses):
        self.model2 = gp.Model("Time Scheduler")
        self.model2.setParam("OutputFlag", 1)
        
        self.x2 = {}
        
       
        for course in desired_courses:
            sections = self.courses[course]['sections']
            labs = self.courses[course].get('labs', [])
        
            # add  sections
            for section in sections:
                self.x2[(course, section)] = self.model2.addVar(
                    vtype=GRB.BINARY, name=f"x_{course}_sec_{section}"
                )
        
            # add lanbs
            for lab in labs:
                self.x2[(course, lab)] = self.model2.addVar(
                    vtype=GRB.BINARY, name=f"x_{course}_lab_{lab}"
                )
    
            # one section consterain
            self.model2.addConstr(
                gp.quicksum(self.x2[(course, sec)] for sec in sections) == 1,
                name=f"choose_one_section_{course}"
            )
    
            # lab constrain 
            if labs:
                self.model2.addConstr(
                    gp.quicksum(self.x2[(course, lab)] for lab in labs) == 1,
                    name=f"choose_one_lab_{course}"
                )
        
        # time conflict 
        all_vars = list(self.x2.keys())
        for i in range(len(all_vars)):
            c1, t1 = all_vars[i]
            for j in range(i + 1, len(all_vars)):
                c2, t2 = all_vars[j]
                if self.does_conflict(t1, t2):
                    self.model2.addConstr(
                        self.x2[(c1, t1)] + self.x2[(c2, t2)] <= 1,
                        name=f"time_conflict_{c1}_{t1}_vs_{c2}_{t2}"
                    )
        return self.model2
    


    
                
    def build_model3(self, beta=2, alpha=0.5, gamma=0.25,delta=1):
        self.model3 = gp.Model("FullPlanScheduler")
        self.model3.setParam('OutputFlag', 1)
    
        semesters = list(range(self.starting_semester, self.total_semesters_remaining + 1))  
        self.y = {}  
    
        for course in self.remaining_courses:
            for sem in semesters:
                self.y[(course, sem)] = self.model3.addVar(vtype=GRB.BINARY, name=f"y_{course}_sem{sem}")
        # must take all cources once 
        for course in self.remaining_courses:
            self.model3.addConstr(gp.quicksum(self.y[course, s] for s in semesters) == 1, name=f"take {course} once")

        # ENFORCE INTERNSHIP SEMESTER RESTRICTIONS
        internship_courses = {'ENGR399', 'ENGR399(2)'}
        for course in self.remaining_courses:
            for s in semesters:
                if s in [9, 12]:
                    # Only allow internship courses in semesters 9 and 12
                    if course not in internship_courses:
                        self.model3.addConstr(self.y[(course, s)] == 0, name=f"no_{course}_in_sem{s}")
                else:
                    # Only allow non-internship courses in other semesters
                    if course in internship_courses:
                        self.model3.addConstr(self.y[(course, s)] == 0, name=f"no_internship_{course}_in_sem{s}")

        # prerequsite constrain 
        for course in self.remaining_courses:
            prereqs = self.courses[course]['prerequisites']
            for prereq in prereqs:
                if prereq in self.remaining_courses:
                    self.model3.addConstr(gp.quicksum(s * self.y[(course, s)] for s in semesters) >= gp.quicksum(s * self.y[(prereq, s)] for s in semesters)+1, name="prereqsite")
        #credits per sem constrain

        for s in semesters:
            total_credits = gp.quicksum(self.y[(course, s)] * self.courses[course]['credits']for course in self.remaining_courses)
            if s%3==0:# so if summer....
                 self.model3.addConstr(total_credits <= 6, name=f"max credits for sem {s}") 
            elif s>12:# for the fifth year, max is 18 but min is 0 
                 self.model3.addConstr(total_credits <= self.max_credits, name=f"max credits for sem {s}")
            else:  
                self.model3.addConstr(total_credits <= self.max_credits, name=f"max credits for sem {s}")
                self.model3.addConstr(total_credits >= self.min_credits, name=f"min credits for sem {s}")# 2+2=4

        # restricted cources constrain e.g sdp
        
        credits_up_to_semester = {s: gp.quicksum(self.courses[c]['credits'] * self.y[c, t] for c in self.remaining_courses for t in semesters if t < s) for s in semesters }

        special_cases = [i for i, j in self.courses.items() if 'min_credits' in j]
        for course in special_cases:
            required_credits = self.courses[course]['min_credits']
            for s in semesters:
                if (course, s) in self.y:
                    self.model3.addConstr(
                        self.y[course, s] * required_credits <= credits_up_to_semester[s],
                        name=f"restricted course {course} in sem {s}")
                        
        # u cant take courses with internships 
        if 'ENGR399' in self.remaining_courses:
            self.model3.addConstrs((gp.quicksum(self.y[c, s] for c in self.remaining_courses if c != 'ENGR399') <= 100 * (1 - self.y['ENGR399', s])for s in semesters))
        if 'ENGR399(2)' in self.remaining_courses:
            self.model3.addConstrs((gp.quicksum(self.y[c, s] for c in self.remaining_courses if c != 'ENGR399(2)') <= 100 * (1 - self.y['ENGR399(2)', s])for s in semesters))


        # availabilty constrain 
        offered_sems= {'fall', 'spring' , 'summer'}
        for course in self.remaining_courses:
            if 'available_in' not in self.courses[course]:
                continue
            not_available_in= offered_sems- self.courses[course]['available_in']
            for s in semesters:
                if s % 3 == 1 and 'fall' in not_available_in:
                    self.model3.addConstr(self.y[course, s] == 0)
                elif s % 3 == 2 and 'spring' in not_available_in:
                    self.model3.addConstr(self.y[course, s] == 0)
                elif s % 3 == 0 and 'summer' in not_available_in:
                    self.model3.addConstr(self.y[course, s] == 0)
            

       
       
        # IMPORTANCE 
        #so since its multiplied by s (semester), to get the lowest score pssible it takes high importance courses sooner 
        importance_term = gp.quicksum(
            self.y[(course, s)] *self.courses[course].get('importance', 1) * s
            for course in self.remaining_courses
            for s in semesters
        )

        # PENALTY 
        # to minimize this, it would rather make the (taken semester - prefered semster) = 0 or as close to 0 as possible 
        penalties = {    (c, s): abs(self.year_of_semester(s) - self.courses[c].get('year', self.year_of_semester(s)))  for c in self.remaining_courses
                for s in semesters  }
        penalty_term = gp.quicksum(
            self.y[(course, s)] *  penalties[(course, s)]
            for course in self.remaining_courses
            for s in semesters if s<13
        )
        fifth_year_penalty = gp.quicksum(
            self.y[(course, s) ]*s
            for course in self.remaining_courses
            for s in semesters if s > 12
        )


        # BALANCE WORKLOAD 
        # here since we r looking for balacning the overload over all semesters, we will want to make the load similar, so we calcute the 'variance' and try to minimze that 
        taken_sems = [s for s in semesters if s % 3 != 0]

    
        avg_weight = gp.quicksum(  self.y[(c, s)] * self.courses[c]['weight']  for s in taken_sems for c in self.remaining_courses) / len(taken_sems)
         
        workload_term = gp.quicksum((gp.quicksum(self.y[c, s] * self.courses[c]['weight'] for c in self.remaining_courses) - avg_weight) ** 2 for s in taken_sems)
        

        mean_weight = gp.quicksum(self.y[(c,s)] * self.courses[c]['weight'] for c in self.remaining_courses for s in semesters if s%3!=0)/ (len(semesters)- len(semesters)//3)
        workload_balance_term = gp.quicksum(
            (gp.quicksum(self.y[c, s] * self.courses[c].get('weight', 1) for c in self.remaining_courses) - mean_weight) ** 2
            for s in semesters if s%3!=0
        )

        objective_expr = alpha*importance_term + beta*workload_balance_term +   gamma* penalty_term + delta*fifth_year_penalty 
        self.model3.setObjective(objective_expr, GRB.MINIMIZE)
        return self.model3
        



    '''
        objective_expr = gp.quicksum(
        (self.y[(course, s)] * s * (beta * self.courses[course].get('weight', 1) - alpha * self.courses[course].get('importance', 1) )- gamma * penalties[(course, s)])
        for course in self.remaining_courses 
        for s in semesters
    )'''


        
        


    
    @staticmethod
    def is_depndent(start_course, target_course, courses):
        visited = set()
        stack = [start_course]
    
        while stack:
            current_course = stack.pop()
    
            if current_course in visited:
                continue
            visited.add(current_course)
            prerequisites = courses.get(current_course, {}).get('prerequisites', [])
    
            for prereq in prerequisites:
                if prereq == target_course:
                    return True
                stack.append(prereq)
    
        return False

    def get_all_dependents(self, target_course):
        dependents= set()
        
        for course in self.courses:
            if self.is_depndent(course, target_course, courses):
                dependents.add(course)
            
        return dependents
    def assign_importance(self):

        for course in self.courses:
            dependents = self.get_all_dependents(course)
            self.courses[course]['importance'] = len(dependents)+1


    @staticmethod
    def parse_time(string):
        i=0
        while i<len(string) and not string[i].isdigit():
            i+=1
        days=list(string[:i])
    
        temp= string[i:]
        start, end = temp.split('-')
        return days, start, end

    
    @staticmethod
    def convert_to_set(str):
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
        return not CourseScheduler.convert_to_set(t1).isdisjoint(CourseScheduler.convert_to_set(t2))

    @staticmethod
    def year_of_semester(s):
        return int((s-1) // 3 + 1 )



    def get_full_solution(self):
        if not hasattr(self, 'model3') or self.model3.Status != GRB.OPTIMAL:
            print("Model3 is not solved or not optimal.")
            return
    
        semester_courses = {s: [] for s in range(1, self.total_semesters_remaining + 1)}
        semester_credits = {s: 0 for s in range(1, self.total_semesters_remaining + 1)}
        cumulative_credits = 0
    
        # Gather results
        for (course, s), var in self.y.items():
            if var.X > 0.5:  # course is taken in semester s
                semester_courses[s].append(course)
                semester_credits[s] += self.courses[course]['credits']
    
        # Print results
        for s in range(1, self.total_semesters_remaining + 1):
            courses = semester_courses[s]
            if not courses:
                continue
            course_names = [self.courses[c]['name'] for c in courses]
            sem_credits = semester_credits[s]
            cumulative_credits += sem_credits
            print(f"Semester {s}: {', '.join(course_names)} | Credits = {sem_credits} \n\n")
        semesters = list(range(self.starting_semester, self.total_semesters_remaining + 1))  

        
        importance_term = sum(
            self.y[(course, s)].X * self.courses[course].get('importance', 1) * s
            for course in self.remaining_courses
            for s in semesters
        )
        
       
        penalty_term = sum(
            self.y[(course, s)].X * abs(self.year_of_semester(s) - self.courses[course].get('year', self.year_of_semester(s)))
            for course in self.remaining_courses
            for s in semesters
        )
        
        taken_sems = { s for s in semesters if s % 3 != 0 }
        
        avg_weight = sum(self.y[(c, s)].X * self.courses[c]['weight'] for s in taken_sems for c in self.remaining_courses) / len(taken_sems)
        
        workload_term = sum((sum(self.y[c, s].X * self.courses[c].get('weight', 1) for c in self.remaining_courses) - avg_weight) ** 2 for s in taken_sems)

        value = sum(
            self.y[(course, s)].X * s
            for course in self.remaining_courses
            for s in semesters if s > 12
        )

        
      
        print(f"Importance Term Value: {importance_term}")
        print(f"Penalty Term Value: {penalty_term}")
        print(f"Workload Variance Term Value: {workload_term}")
        print(f"avg load : {avg_weight}")
        print(f"Fifth year pen Value: {value}")

    def topological_sort_courses(self, remaining, completed):
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

    def debug_unscheduled_course(self, course_code, completed_courses):
        print(f"\nDebugging course: {course_code} - {self.courses[course_code]['name']}")
        for sem in range(2, self.total_semesters_remaining + 1):
            sem_type = self.get_semester_type(sem)
            prereqs = self.courses[course_code]['prerequisites']
            available_in = self.courses[course_code].get('available_in', ["fall", "spring", "summer"])
            min_cred = self.courses[course_code].get('min_credits')
            reasons = []
            if not all(pr in completed_courses for pr in prereqs):
                reasons.append(f"missing prerequisites: {', '.join([pr for pr in prereqs if pr not in completed_courses])}")
            if sem_type.lower() not in [s.lower() for s in available_in]:
                reasons.append(f"not offered in {sem_type}")
            if min_cred is not None:
                total_cred = sum(self.courses[cc]['credits'] for cc in completed_courses)
                if total_cred < min_cred:
                    reasons.append(f"requires {min_cred} credits, has {total_cred}")
            if reasons:
                print(f"  Semester {sem} ({sem_type}): NOT ELIGIBLE ({'; '.join(reasons)})")
            else:
                print(f"  Semester {sem} ({sem_type}): ELIGIBLE")

    def semester_by_semester_plan(self, credit_target=15, penalty_weight=1.0):
        def get_semester_type(sem_num):
            if sem_num % 3 == 1:
                return 'Fall'
            elif sem_num % 3 == 2:
                return 'Spring'
            else:
                return 'Summer'

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
            sem_type = get_semester_type(sem)
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
                min_cred = course.get('min_credits')
                reasons = []
                if not all(pr in completed for pr in prereqs):
                    reasons.append(f"missing prerequisites: {', '.join([pr for pr in prereqs if pr not in completed])}")
                if sem_type.lower() not in [s.lower() for s in available_in]:
                    reasons.append(f"not offered in {sem_type}")
                if min_cred is not None:
                    total_cred = sum(self.courses[cc]['credits'] for cc in completed)
                    if total_cred < min_cred:
                        reasons.append(f"requires {min_cred} credits, has {total_cred}")
                if not reasons:
                    eligible_courses.append(c)
            # Only pass eligible courses to the scheduler
            semester_courses = []
            if eligible_courses:
                scheduler = CourseScheduler(self.courses, completed, set(eligible_courses), max_credits, min_credits, self.total_semesters_remaining, self.starting_semester, semester_type=sem_type)
                scheduler.remaining_courses = set(eligible_courses)
                scheduler.build_model(credit_target=credit_target, penalty_weight=penalty_weight)
                scheduler.model.optimize()
                if scheduler.model.Status == GRB.OPTIMAL:
                    semester_courses = [c for c in eligible_courses if any(scheduler.x[(c, s)].X > 0.5 for s in self.courses[c]['sections'])]
                    completed.update(semester_courses)
            all_semesters.append(semester_courses)
            sem += 1
        # Print the full plan
        print("==============================")
        print("     Full Degree Plan Output    ")
        print("==============================\n")
        total_credits_all = 0
        for i, sem_courses in enumerate(all_semesters, 1):
            sem_type = get_semester_type(i)
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
                self.debug_unscheduled_course(c, completed)

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
    courses = load_courses_dict_from_json("courses.json")
    scheduler = CourseScheduler(courses, set(), set(courses.keys()))
    scheduler.semester_by_semester_plan(credit_target=15, penalty_weight=1.0)