import random


class Chromosome:
    def __init__(self, genes=None):
        # If no genes are provided, generate random ones
        if genes is None:
            self.genes = self.randomGene()
        else:
            self.genes = genes

    @staticmethod
    def randomGene():
        # Generate 63 random moves between 1 and 8
        gene = []
        for _ in range(63):
            gene.append(random.randint(1,8))
        return gene

    def crossover(self, partner):
        # Single-point crossover
        point = random.randint(1, 62)  # crossover point between 1 and 62
        child1_genes = self.genes[:point] + partner.genes[point:]
        child2_genes = partner.genes[:point] + self.genes[point:]
        return Chromosome(child1_genes), Chromosome(child2_genes)

    def mutation(self, mutation_rate=0.01):
        for i in range(len(self.genes)):
            if random.random() < mutation_rate:
                self.genes[i] = random.randint(1,8)  # mutate to a new random move
        return self

