# Dylan Orpin
# Assignment 2 (minheap)

# imports

import random # used for randomly selcting
import heapq # used for the minheap
from itertools import count # used for the counter

# data definitions

MUTATION_RATE = 0.01 # given to us

FACILITATORS = ["Lock", "Glen", "Banks", "Richards", "Shaw",  # list of available facilitators
                "Singer", "Uther", "Tyler", "Numen", "Zeldin"]

TIME_SLOTS = ["10 AM", "11 AM", "12 PM", "1 PM", "2 PM", "3 PM"] # list of available time slots

ROOMS = {
    "Slater 003": 45,
    "Roman 216": 30,
    "Loft 206": 75,
    "Roman 201": 50,
    "Loft 310": 108,
    "Beach 201": 60,
    "Beach 301": 75,
    "Logos 325": 450,
    "Frank 119": 60
}

ACTIVITIES = {  # dictionary of rooms and their capacities
    "SLA100A": {"enrollment": 50, "preferred": ["Glen", "Lock", "Banks", "Zeldin"], "others": ["Numen", "Richards"]},
    "SLA100B": {"enrollment": 50, "preferred": ["Glen", "Lock", "Banks", "Zeldin"], "others": ["Numen", "Richards"]},
    "SLA191A": {"enrollment": 50, "preferred": ["Glen", "Lock", "Banks", "Zeldin"], "others": ["Numen", "Richards"]},
    "SLA191B": {"enrollment": 50, "preferred": ["Glen", "Lock", "Banks", "Zeldin"], "others": ["Numen", "Richards"]},
    "SLA201":  {"enrollment": 50, "preferred": ["Glen", "Banks", "Zeldin", "Shaw"], "others": ["Numen", "Richards", "Singer"]},
    "SLA291":  {"enrollment": 50, "preferred": ["Lock", "Banks", "Zeldin", "Singer"], "others": ["Numen", "Richards", "Shaw", "Tyler"]},
    "SLA303":  {"enrollment": 60, "preferred": ["Glen", "Zeldin", "Banks"], "others": ["Numen", "Singer", "Shaw"]},
    "SLA304":  {"enrollment": 25, "preferred": ["Glen", "Banks", "Tyler"], "others": ["Numen", "Singer", "Shaw", "Richards", "Uther", "Zeldin"]},
    "SLA394":  {"enrollment": 20, "preferred": ["Tyler", "Singer"], "others": ["Richards", "Zeldin"]},
    "SLA449":  {"enrollment": 60, "preferred": ["Tyler", "Singer", "Shaw"], "others": ["Zeldin", "Uther"]},
    "SLA451":  {"enrollment": 100, "preferred": ["Tyler", "Singer", "Shaw"], "others": ["Zeldin", "Uther", "Richards", "Banks"]}
}

# classes

class ActivityAssignment:
    def __init__(self, room, time, facilitator): # constructor for activity assignments, initializes
        self.room = room
        self.time = time
        self.facilitator = facilitator

    def __repr__(self): # used for printing
        return f"{self.room} @ {self.time} with {self.facilitator}"

class Schedule:
    def __init__(self):
        self.assignments = {} # maps names to assignments
        self.fitness = 0.0 # fitness score of schedule

    def randomize(self): # fills with random assignments
        for activity in ACTIVITIES:
            room = random.choice(list(ROOMS.keys()))
            time = random.choice(TIME_SLOTS)
            facilitator = random.choice(FACILITATORS)
            self.assignments[activity] = ActivityAssignment(room, time, facilitator) # stores them

# fitness functions

def time_to_int(time_str): # converts time to int
    return int(time_str.split()[0])  

def score_special_cases(schedule): # calculates bonuses for SLA100/191
    bonus = 0.0
    time_map = {}
    room_map = {}

    for activity in ["SLA100A", "SLA100B", "SLA191A", "SLA191B"]: # converts and stores room
        if activity in schedule.assignments:
            assignment = schedule.assignments[activity]
            time_map[activity] = time_to_int(assignment.time)
            room_map[activity] = assignment.room

    # SLA100
    if abs(time_map["SLA100A"] - time_map["SLA100B"]) > 4:
        bonus += 0.5 # bonus if > 4
    if time_map["SLA100A"] == time_map["SLA100B"]:
        bonus -= 0.5 # penalty if equal

    # SLA191
    if abs(time_map["SLA191A"] - time_map["SLA191B"]) > 4:
        bonus += 0.5 # bonus if > 4
    if time_map["SLA191A"] == time_map["SLA191B"]:
        bonus -= 0.5 # penalty if equal

    # SLA100/191 combos
    for a in ["SLA100A", "SLA100B"]:
        for b in ["SLA191A", "SLA191B"]:
            t1, t2 = time_map[a], time_map[b] # gets times
            r1, r2 = room_map[a], room_map[b] # gets rooms
            if abs(t1 - t2) == 1:
                bonus += 0.5 # bonus if consecutive
                in_opposite = (
                    ("Roman" in r1 or "Beach" in r1) ^
                    ("Roman" in r2 or "Beach" in r2)
                )
                if in_opposite:
                    bonus -= 0.4 # penalty if opposite buildings
            elif abs(t1 - t2) == 2:
                bonus += 0.25 # bonus if hour gap
            elif t1 == t2:
                bonus -= 0.25 # penalty if same time slot

    return bonus

def compute_fitness(schedule): # calculates fitness for full schedule
    fitness = 0.0
    activity_list = list(schedule.assignments.items()) # converts to list
    facilitator_times = {f: [] for f in FACILITATORS} # tracks facilitator usage by time
    room_times = {}
    facilitator_total_load = {f: 0 for f in FACILITATORS} # facilitator total assingments

    for activity, assignment in activity_list: # gets data
        data = ACTIVITIES[activity]
        enrollment = data["enrollment"]
        preferred = data["preferred"]
        others = data["others"]
        room_capacity = ROOMS[assignment.room]

        if room_capacity < enrollment:
            fitness -= 0.5 #penalty if too small
        elif room_capacity > 6 * enrollment:
            fitness -= 0.4  # penalty if too small
        elif room_capacity > 3 * enrollment:
            fitness -= 0.2 # penalty if wasting space
        else:
            fitness += 0.3 # bonus if good size

        if assignment.facilitator in preferred:
            fitness += 0.5 # bonus if preferred
        elif assignment.facilitator in others:
            fitness += 0.2 # bonus if okay with it
        else:
            fitness -= 0.1 # penalty if not

        facilitator_times[assignment.facilitator].append(assignment.time) # tracks facilitator time
        facilitator_total_load[assignment.facilitator] += 1

        if (assignment.room, assignment.time) in room_times: # check for room/time conflicts
            fitness -= 0.5 # penalty if conflict
        else:
            room_times[(assignment.room, assignment.time)] = activity

    for facilitator, times in facilitator_times.items(): # counts how many times facilitator booked
        time_counts = {t: times.count(t) for t in times}
        for count in time_counts.values():
            if count > 1:
                fitness -= 0.2 # penalty if double booked
            elif count == 1:
                fitness += 0.2 # bonus if not

        total = facilitator_total_load[facilitator]
        if total > 4: 
            fitness -= 0.5 # penalty if greater than 4 for load
        elif total in [1, 2] and facilitator != "Tyler":
            fitness -= 0.4 # penalty if not enough and not Tyler

    fitness += score_special_cases(schedule)
    return fitness

def crossover(parent1, parent2): # creates child from 2 parents
    child = Schedule()
    for activity in ACTIVITIES:
        if random.random() < 0.5: # randomly selects them
            child.assignments[activity] = parent1.assignments[activity]
        else:
            child.assignments[activity] = parent2.assignments[activity]
    return child

def mutate(schedule): # randomly mutates schedule
    for activity in schedule.assignments:
        if random.random() < MUTATION_RATE:
            assignment = schedule.assignments[activity]
            assignment.room = random.choice(list(ROOMS.keys()))
        if random.random() < MUTATION_RATE:
            assignment = schedule.assignments[activity]
            assignment.time = random.choice(TIME_SLOTS)
        if random.random() < MUTATION_RATE:
            assignment = schedule.assignments[activity]
            assignment.facilitator = random.choice(FACILITATORS)

def run_generation(population): # runs a generation
    for _ in range(POPULATION_SIZE):
        heapq.heappop(population) # remove least fit
        parents = random.sample(population, 2) # pick 2 random parents
        parent1 = parents[0][2]
        parent2 = parents[1][2]
        child = crossover(parent1, parent2) # crossover to produce kid
        mutate(child) # mutate
        child.fitness = compute_fitness(child) # score the kid
        heapq.heappush(population, (child.fitness, next(counter), child)) # insert into heap

# population generation

POPULATION_SIZE = 500
counter = count()  # global counter to ensure unique heap items

def generate_initial_population(): # creates initial population
    population = []
    for _ in range(POPULATION_SIZE):
        sched = Schedule()
        sched.randomize()
        sched.fitness = compute_fitness(sched)
        heapq.heappush(population, (sched.fitness, next(counter), sched))
    return population

# main genetic algorithm

def run_genetic_algorithm():
    population = generate_initial_population()
    fitness_history = []

    for gen in range(300):  # runs up to 300 generations
        run_generation(population)

        best_fitness = population[-1][0]  # max fitness (heapq = minheap, so last is best)
        fitness_history.append(best_fitness)

        print(f"Generation {gen + 1}: Best Fitness = {best_fitness:.3f}") # prints best fitness

        if gen > 100: # early stopping condition (after gen 100)
            if fitness_history[100] != 0: # make sure not dividing by 0
                improvement = (fitness_history[gen] - fitness_history[100]) / abs(fitness_history[100])
                if improvement < 0.01:
                    print("Stopping early: <1% improvement since generation 100")
                    break
            else:
                print("Stopping early: fitness at generation 100 is zero (can't compare improvement)")
                break

    best_schedule = population[-1][2]  # save the best schedule
    print("\nBest Schedule:\n")
    for activity, assignment in best_schedule.assignments.items():
        print(f"{activity}: {assignment}")

    with open("best_schedule.txt", "w") as f: # saves best schedule to file
        f.write("Best Schedule:\n\n")
        for activity, assignment in best_schedule.assignments.items():
            f.write(f"{activity}: {assignment}\n")

if __name__ == "__main__": # runs program
    run_genetic_algorithm()