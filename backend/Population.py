from backend.Knight import Knight
from backend.Chromosome import Chromosome
import random

class Population:
    def __init__(self, population_size, generation=1, knights=None):
        self.population_size = population_size
        self.generation = generation
        self.knights = [] 
        for i in range (self.population_size):
            kn=Knight(None)
            self.knights.append(kn)
            self.generation=1


    def check_population(self):
        for kn in self.knights:
            kn.check_moves()

    def evaluate(self):
        best_knight=None
        best_fitness=-1
        for kn in self.knights:
            current_fitness=kn.evaluate_fitness()
            if current_fitness>best_fitness:
                best_fitness=current_fitness
                best_knight=kn

        return best_fitness,best_knight 
           

    def tournament_selection(self):
        random_knights=random.choices(self.knights,k=3)
        random_knights.sort(key=lambda k: k.evaluate_fitness(), reverse=True)
        return random_knights[0], random_knights[1]



    def create_new_generation(self):
        new_knights=[]
        for _ in range(self.population_size//2):
            parent1,parent2=self.tournament_selection()
            offspring1,offspring2=parent1.chromosome.crossover(parent2.chromosome)
            offspring1.mutation()
            offspring2.mutation()
            child_knight1=Knight(offspring1)
            child_knight2=Knight(offspring2)
            new_knights.append(child_knight2)
            new_knights.append(child_knight1)
        self.knights=new_knights
        self.generation+=1
    
            