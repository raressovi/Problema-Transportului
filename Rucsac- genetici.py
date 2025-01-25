import random
import numpy as np

# Definirea problemei
values = [60, 100, 120]  # Valorile obiectelor
weights = [10, 20, 30]  # Greutățile obiectelor
capacity = 50  # Capacitatea maximă a rucsacului
num_items = len(values)  # Numărul de obiecte

# Parametrii algoritmului genetic
population_size = 10
num_generations = 50
mutation_rate = 0.1

# Funcția de fitness
def fitness(individual):
    total_value = np.sum(np.array(individual) * np.array(values))
    total_weight = np.sum(np.array(individual) * np.array(weights))
    if total_weight > capacity:
        return 0  # Penalizare pentru depășirea capacității
    return total_value

# Inițializarea populației
def initialize_population():
    return [np.random.randint(2, size=num_items).tolist() for _ in range(population_size)]

# Selecția părinților (turneu)
def tournament_selection(population, fitnesses):
    tournament_size = 3
    selected = random.sample(list(zip(population, fitnesses)), tournament_size)
    return max(selected, key=lambda x: x[1])[0]

# Recombinarea (crossover)
def crossover(parent1, parent2):
    point = random.randint(1, num_items - 1)
    child1 = parent1[:point] + parent2[point:]
    child2 = parent2[:point] + parent1[point:]
    return child1, child2

# Mutarea (mutation)
def mutate(individual):
    for i in range(num_items):
        if random.random() < mutation_rate:
            individual[i] = 1 - individual[i]
    return individual

# Algoritmul genetic
def genetic_algorithm():
    population = initialize_population()

    for generation in range(num_generations):
        # Calculăm fitness-ul fiecărui individ
        fitnesses = [fitness(ind) for ind in population]

        # Creăm o nouă populație
        new_population = []
        while len(new_population) < population_size:
            # Selecția părinților
            parent1 = tournament_selection(population, fitnesses)
            parent2 = tournament_selection(population, fitnesses)

            # Recombinare
            child1, child2 = crossover(parent1, parent2)

            # Mutare
            child1 = mutate(child1)
            child2 = mutate(child2)

            new_population.extend([child1, child2])

        # Trunchiem populația la dimensiunea dorită
        population = new_population[:population_size]

    # Returnăm cea mai bună soluție
    fitnesses = [fitness(ind) for ind in population]
    best_index = np.argmax(fitnesses)
    return population[best_index], fitnesses[best_index]

# Rularea algoritmului
best_solution, best_value = genetic_algorithm()
print("Cea mai bună soluție:", best_solution)
print("Valoarea maximă:", best_value)
