import gurobipy as gp
from gurobipy import GRB
from unittest.mock import MagicMock

class CourseScheduler:
    def __init__(self, courses, completed, required, max=18,min=12, semesters=15, starting=1):
        self.courses= courses
        self.completed_courses= set(completed)
        self.required_courses= set(required)
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

        
  

   
    
    def build_model(self,alpha=1.5, beta=0.5):
        self.model = gp.Model("NextSemesterScheduler")
        self.model.setParam('OutputFlag', 1) 
        # here we add the varibles into the model, in this case they r the  remaing courses 
        self.x= {} 
        for course in self.remaining_courses:
            for section in self.courses[course].get('sections', ['default']):
                self.x[(course, section)] = self.model.addVar(vtype= GRB.BINARY, name= f"x_{course}_{section}")

        

        # now we add the constrains. we will do prerequsites and max credits hours for now and the others later (like time conflicts) 
        #prereusite constrain:
        
        for i in self.remaining_courses:
            prerequistes=self.courses[i]['prerequisites']
            for j in prerequistes:
                if j in self.completed_courses:
                    continue 
                for section in self.courses[i].get('sections', ['default']):
                    self.model.addConstr(self.x[(i, section)] <= 0)

        #section constrain 
        for course in self.remaining_courses:
            self.model.addConstr(gp.quicksum(self.x[course,section] for section in self.courses[course].get('sections', ['default'])) <=1)
            
        #credit constrain                          
        total_credits_pre_sem= gp.quicksum(self.courses[x]['credits']* self.x[x,y] for x in self.remaining_courses for y in self.courses[x].get('sections', ['default'])) 
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
        total_credits = sum(self.courses[course]['credits'] for course in self.completed_courses)
        special_cases = [i for i, j in self.courses.items() if 'min_credits' in j and i in self.remaining_courses]
        for course in  special_cases:
            if total_credits < self.courses[course]['min_credits']:
                self.model.addConstr(gp.quicksum(self.x[course, section] for section in self.courses[course].get('sections', ['default'])) == 0)
        

        objective_expr = gp.quicksum(self.x[(c,s)] * (alpha * self.courses[c].get('importance', 1) - beta * self.courses[c].get('weight', 1)) for c in self.remaining_courses for s in self.courses[c].get('sections', ['default']))


        #m making the model to give the max amount of credits for now. I will discuess this with u guys
                                   
        #self.model.setObjective(total_credits,GRB.MAXIMIZE)
        self.model.setObjective(objective_expr, GRB.MAXIMIZE)
        return self.model


    
    def build_model2(self, desired_courses,fixed_sections,fixed_labs):
        self.model2 = gp.Model("Time Scheduler")
        self.model2.setParam("OutputFlag", 1)
        print('fixed_sections:', fixed_sections)
        print('fixed_labs:', fixed_labs)
        
        self.x2 = {}
        
       
        for course in desired_courses:
            sections = self.courses[course].get('sections', ['default'])
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
        for course, section in fixed_sections.items():
            self.model2.addConstr(
                self.x2[(course,section)] == 1)

        for course, section in fixed_labs.items():
            self.model2.addConstr(
                self.x2[(course,section)] == 1)
    

    
        
    


    
                
    def build_model3(self, beta=1.5, alpha=0.5, gamma=0.25,delta=1):
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
        
        credits_up_to_semester = {
        s: gp.quicksum(
            self.courses[c]['credits'] * self.y[c, t]
            for c in self.remaining_courses
            for t in semesters if t < s
        ) + sum(self.courses[c]['credits'] for c in self.completed_courses if c in self.courses)
        for s in semesters
    }


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
            if self.is_depndent(course, target_course, self.courses):
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



    def get_full_solution(self):
        if not hasattr(self, 'model3') or self.model3 is None or self.model3.Status != GRB.OPTIMAL:
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
            self.y.get((course, s), MagicMock(X=0)).X * self.courses.get(course, {}).get('importance', 1) * s
            for course in self.remaining_courses
            for s in semesters
        )
        
       
        penalty_term = sum(
            self.y.get((course, s), MagicMock(X=0)).X * abs(self.year_of_semester(s) - self.courses.get(course, {}).get('year', self.year_of_semester(s)))
            for course in self.remaining_courses
            for s in semesters
        )
        
        taken_sems = { s for s in semesters if s % 3 != 0 }
        
        avg_weight = sum(self.y.get((c, s), MagicMock(X=0)).X * self.courses.get(c, {}).get('weight', 1) for s in taken_sems for c in self.remaining_courses) / len(taken_sems)
        
        workload_term = sum((sum(self.y.get((c, s), MagicMock(X=0)).X * self.courses.get(c, {}).get('weight', 1) for c in self.remaining_courses) - avg_weight) ** 2 for s in taken_sems)

        value = sum(
            self.y.get((course, s), MagicMock(X=0)).X * s
            for course in self.remaining_courses
            for s in semesters if s > 12
        )

        
      
        print(f"Importance Term Value: {importance_term}")
        print(f"Penalty Term Value: {penalty_term}")
        print(f"Workload Variance Term Value: {workload_term}")
        print(f"avg load : {avg_weight}")
        print(f"Fifth year pen Value: {value}")

