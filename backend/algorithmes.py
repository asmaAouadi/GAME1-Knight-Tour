from backend.Population import Population
import time 

def genetic_algorithm(populationSize):
    start_time = time.time()
    population = Population(populationSize)

    while True:
        population.check_population()
        best_fitness,best_knight=population.evaluate()
        
        if best_fitness==64:
            end_time = time.time()
            execution_time = end_time - start_time
            return best_knight.path, execution_time
        else:
            population.create_new_generation()

        

path, exec_time = genetic_algorithm(50)

print("Solution path:", path)
print("the best fitness :", len(path))
print("Execution time:", exec_time, "seconds")