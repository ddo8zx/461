# Dylan Orpin
# Assignment 2 (prob distribution)

# imports

import random # used for generating random selections
import math # used for the calculations in softmax
from collections import defaultdict, Counter # used for counting and grouping

# data definitions

FACILITATORS = [ # list of given available facilitators
    "Lock", "Glen", "Banks", "Richards", "Shaw",
    "Singer", "Uther", "Tyler", "Numen", "Zeldin"
]

TIME_SLOTS = ["10 AM", "11 AM", "12 PM", "1 PM", "2 PM", "3 PM"] # list of given available time slots

ROOMS = { # dictionary of given rooms and capacities
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

ACTIVITIES = [ # list of activities with expected enrollment and facilitator preferences
    {"name": "SLA100A", "expected": 50, "preferred": ["Glen", "Lock", "Banks", "Zeldin"], "other": ["Numen", "Richards"]},
    {"name": "SLA100B", "expected": 50, "preferred": ["Glen", "Lock", "Banks", "Zeldin"], "other": ["Numen", "Richards"]},
    {"name": "SLA191A", "expected": 50, "preferred": ["Glen", "Lock", "Banks", "Zeldin"], "other": ["Numen", "Richards"]},
    {"name": "SLA191B", "expected": 50, "preferred": ["Glen", "Lock", "Banks", "Zeldin"], "other": ["Numen", "Richards"]},
    {"name": "SLA201",  "expected": 50, "preferred": ["Glen", "Banks", "Zeldin", "Shaw"], "other": ["Numen", "Richards", "Singer"]},
    {"name": "SLA291",  "expected": 50, "preferred": ["Lock", "Banks", "Zeldin", "Singer"], "other": ["Numen", "Richards", "Shaw", "Tyler"]},
    {"name": "SLA303",  "expected": 60, "preferred": ["Glen", "Zeldin", "Banks"], "other": ["Numen", "Singer", "Shaw"]},
    {"name": "SLA304",  "expected": 25, "preferred": ["Glen", "Banks", "Tyler"], "other": ["Numen", "Singer", "Shaw", "Richards", "Uther", "Zeldin"]},
    {"name": "SLA394",  "expected": 20, "preferred": ["Tyler", "Singer"], "other": ["Richards", "Zeldin"]},
    {"name": "SLA449",  "expected": 60, "preferred": ["Tyler", "Singer", "Shaw"], "other": ["Zeldin", "Uther"]},
    {"name": "SLA451",  "expected": 100, "preferred": ["Tyler", "Singer", "Shaw"], "other": ["Zeldin", "Uther", "Richards", "Banks"]}
]

# random schedule generation

def generate_random_schedule(): # generates random schedule for all activities
    schedule = [] # list to hold schedule entries
    for activity in ACTIVITIES: # loop through each activity
        entry = { 
            "activity": activity["name"],
            "room": random.choice(list(ROOMS.keys())), # random room choice
            "time": random.choice(TIME_SLOTS), # random time slot
            "facilitator": random.choice(FACILITATORS) # random facilitator
        }
        schedule.append(entry) # adds entry to schedule
    return schedule

def generate_initial_population(n): # generates initial population of random schedules
    return [generate_random_schedule() for _ in range(n)] # list of n schedules

# fitness function

def compute_fitness(schedule): # evaluates fitness score of given schedule
    score = 0.0 # initializes score to 0
    room_time_usage = defaultdict(list) # tracks room usage by time slot
    facilitator_times = defaultdict(list) # tracks facilitator's scheduled time
    facilitator_total = Counter() # tracks total activities per facilitator

    act_lookup = {a["name"]: a for a in ACTIVITIES} # maps activity name to its data

    for entry in schedule: # first pass to build tracking maps/get context
        act = entry["activity"] # extracts name
        room = entry["room"] # extracts room
        time = entry["time"] # extracts time
        facilitator = entry["facilitator"] # extracts facilitator

        room_time_usage[(room, time)].append(act) # record room + time
        facilitator_times[facilitator].append(time) # record facilitator + time
        facilitator_total[facilitator] += 1 # increment facilitator total activity

    for entry in schedule: # repeat to evaluate fitness score using earlier data
        act = entry["activity"]
        room = entry["room"]
        time = entry["time"]
        facilitator = entry["facilitator"]

        activity_data = act_lookup[act] # gets expected enrollment and facilitator preference for activity
        expected = activity_data["expected"] # get expected enrollment to evaluate room size fitness

        # conflict if multiple activities in same room at same time
        if len(room_time_usage[(room, time)]) > 1:
            score -= 0.5 # decrease score if overlap

        # evaluate room size related to expected enrollment
        capacity = ROOMS[room]
        if capacity < expected:
            score -= 0.5 # decrease if room too small
        elif capacity > 6 * expected:
            score -= 0.4 # decrease if room way oversized
        elif capacity > 3 * expected:
            score -= 0.2 # decrease score if room oversized
        else:
            score += 0.3 # increase score for correct size

        # evaluate facilitator match
        if facilitator in activity_data["preferred"]:
            score += 0.5 # increase score if facilitator is preferred
        elif facilitator in activity_data["other"]:
            score += 0.2 # increase score if facilitator is acceptable
        else:
            score -= 0.1 # decrease score if facilitator is not ideal

        # evaluate if facilitator available
        if facilitator_times[facilitator].count(time) == 1:
            score += 0.2 # increase score if free
        else:
            score -= 0.2 # decrease score if not free

    # evaluate facilitator activity load
    for facilitator, count in facilitator_total.items():
        if count > 4:
            score -= 0.5 # decrease score if greater than 4
        elif count in [1, 2]:
            if facilitator != "Tyler":
                score -= 0.4 # decrease score if too low and not Tyler

    # activity-specific rules
    time_map = {entry["activity"]: entry["time"] for entry in schedule} # get time for each activity
    room_map = {entry["activity"]: entry["room"] for entry in schedule} # get room for each activity

    def time_diff(t1, t2):
        return abs(TIME_SLOTS.index(t1) - TIME_SLOTS.index(t2)) # returns how many slots apart two times are

    def in_diff_buildings(r1, r2):
        roman_beach = ["Roman", "Beach"]
        b1 = any(x in r1 for x in roman_beach)
        b2 = any(x in r2 for x in roman_beach)
        return b1 != b2 # return true if only one room is in Roman or Beach

    # SLA100 (SLA100A/B) + SLA191 (SLA191A/B) rules
    for a1, a2 in [("SLA100A", "SLA100B"), ("SLA191A", "SLA191B")]:
        t1 = time_map[a1]
        t2 = time_map[a2]
        if t1 == t2:
            score -= 0.5 # decrease score if same time
        elif time_diff(t1, t2) >= 4:
            score += 0.5 # increase score if far enough apart

    for a1 in ["SLA100A", "SLA100B"]:
        for a2 in ["SLA191A", "SLA191B"]:
            t1 = time_map[a1]
            t2 = time_map[a2]
            if time_diff(t1, t2) == 1:
                score += 0.5 # increase score if back to back
                if in_diff_buildings(room_map[a1], room_map[a2]):
                    score -= 0.4 # decrease score if far away and back to back
            elif time_diff(t1, t2) == 2:
                score += 0.25 # increase score if there is gap between 101 & 191
            elif t1 == t2:
                score -= 0.25 # decrease score if they are in same time slot

    return score

# softmax selection

def softmax(fitness_scores): # applies softmax to scores
    max_score = max(fitness_scores) # used for stability
    exps = [math.exp(f - max_score) for f in fitness_scores]
    total = sum(exps)
    return [e / total for e in exps] # returns probability distribution

# genetic operators

def select_parents(population, fitness_scores): # selects 2 parents based on softmax probabilities
    probabilities = softmax(fitness_scores)
    parents = random.choices(population, weights=probabilities, k=2)
    return parents

def crossover(parent1, parent2): # single-point crossover for two schedules
    point = random.randint(1, len(parent1) - 1)
    child1 = parent1[:point] + parent2[point:]
    child2 = parent2[:point] + parent1[point:]
    return child1, child2

def mutate(schedule, mutation_rate=0.01): # applies random mutations to a schedule
    for entry in schedule:
        if random.random() < mutation_rate:
            entry["room"] = random.choice(list(ROOMS.keys()))
        if random.random() < mutation_rate:
            entry["time"] = random.choice(TIME_SLOTS)
        if random.random() < mutation_rate:
            entry["facilitator"] = random.choice(FACILITATORS)
    return schedule

# main genetic algorithm loop

def run_genetic_algorithm(generations=200, population_size=500): # creates the loop
    population = generate_initial_population(population_size) # initial population
    fitness_history = [] # list to track average fitness
    mutation_rate = 0.01 # starting mutation rate

    for gen in range(generations): # loop over generations
        fitness_scores = [compute_fitness(schedule) for schedule in population] # scores each schedule
        avg_fitness = sum(fitness_scores) / len(fitness_scores) # averages score
        fitness_history.append(avg_fitness) # update list

        print(f"Generation {gen + 1}: Avg Fitness = {avg_fitness:.4f}") # displays current generation's fitness

        if gen > 100:  # checks for early stopping condition
            if fitness_history[100] != 0:
                improvement = (fitness_history[gen] - fitness_history[100]) / fitness_history[100]  # calculate % improvement
                if improvement < 0.01:
                    print("Stopping early: <1% improvement since generation 100")
                    break  # stop early if improvement is less than 1%
            else:
                print("Stopping early: fitness at generation 100 is zero (can't compare improvement)")
                break


        if gen > 0 and fitness_history[gen] > fitness_history[gen - 1]: 
            mutation_rate = max(0.0001, mutation_rate / 2) # cut mutation rate in half if improved last generation

        new_population = [] # create list for new population
        while len(new_population) < population_size:
            parent1, parent2 = select_parents(population, fitness_scores) # selects 2 parents using softmax
            child1, child2 = crossover(parent1, parent2) # generates children using crossover
            new_population.extend([
                mutate(child1, mutation_rate), # mutate and add child 1
                mutate(child2, mutation_rate) # mutate and add child 2
            ])
        population = new_population[:population_size] # replace population

    final_scores = [compute_fitness(s) for s in population] # recompute fitness scores
    best_index = final_scores.index(max(final_scores)) # find the index of the best schedule
    best_schedule = population[best_index] # retrieve best schedule
    
    print("\nBest Schedule (Fitness = {:.2f}):".format(final_scores[best_index]))
    for entry in best_schedule:
        print(entry) # prints best schedule

    with open("final_schedule.txt", "w") as f: # opens file
        for entry in best_schedule:
            f.write(str(entry) + "\n") # writes to file

# entry point

if __name__ == "__main__":
    run_genetic_algorithm() # runs program
