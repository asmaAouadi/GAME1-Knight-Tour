
import random
from backend.Chromosome import Chromosome



class Knight:
    def __init__(self,chromosome):
        self.position =tuple((0,0))
        if chromosome is None:
            self.chromosome = Chromosome()
        else:
            self.chromosome = chromosome
        self.path =[self.position]
        self.fitness = 0
    
    def move_forward(self,direction):
        x,y=self.position
        moves = {
            1: (x+1, y+2),   # DOWN-right 
            2: (x+2, y+1),   # RIGHT-down  
            3: (x+2, y-1),   # RIGHT-up
            4: (x+1, y-2),   # UP-right
            5: (x-1, y-2),   # UP-left
            6: (x-2, y-1),   # LEFT-up
            7: (x-2, y+1),   # LEFT-down
            8: (x-1, y+2)    # DOWN-left
        }
        new_pos = moves[direction]
        self.position = new_pos
        return new_pos
    def move_backward(self,direction):
        x,y=self.position
        moves = {
            1: (x-1, y-2),   # DOWN-right 
            2: (x-2, y-1),   # RIGHT-down  
            3: (x-2, y+1),   # RIGHT-up
            4: (x-1, y+2),   # UP-right
            5: (x+1, y+2),   # UP-left
            6: (x+2, y+1),   # LEFT-up
            7: (x+2, y-1),   # LEFT-down
            8: (x+1, y-2)    # DOWN-left
        }
        self.position = moves[direction]
        return self.position
        


    def check_moves(self):
        cycle_forward =random.choice([True, False])
        
        for i in range(len(self.chromosome.genes)):
            gene = self.chromosome.genes[i]
            
            
            # Try the original move
            new_position = self.move_forward(gene)
            
            # Check if valid
            if (0 <= new_position[0] < 8 and 
                0 <= new_position[1] < 8 and 
                new_position not in self.path):
                # Valid move - ADD TO PATH
                self.path.append(new_position)
            else:
                # Invalid move - cancel it using move_backward
                self.move_backward(gene)
                
                # Try cycling through alternatives
                found_valid = False
                alternatives = []
                
                if cycle_forward:
                    # Cycle forward: gene+1, gene+2, ..., wrapping around
                    for j in range(1, 8):
                        alt_gene = (gene + j - 1) % 8 + 1
                        alternatives.append(alt_gene)
                else:
                    # Cycle backward: gene-1, gene-2, ..., wrapping around
                    for j in range(1, 8):
                        alt_gene = (gene - j - 1) % 8 + 1
                        alternatives.append(alt_gene)
                
                # Try each alternative
                for alt_gene in alternatives:
                    alt_position = self.move_forward(alt_gene)
                    
                    if (0 <= alt_position[0] < 8 and 
                        0 <= alt_position[1] < 8 and 
                        alt_position not in self.path):
                        # Valid alternative found
                        self.chromosome.genes[i] = alt_gene  # Update chromosome
                        self.path.append(alt_position)  # ADD TO PATH
                        found_valid = True
                        break
                    else:
                        # This alternative didn't work either, cancel it
                        self.move_backward(alt_gene)
                



    def evaluate_fitness(self):
    
        self.fitness = 1 
        for i in range(1, len(self.path)):
            current_pos = self.path[i]
            if (0 <= current_pos[0] < 8 and 
                0 <= current_pos[1] < 8 and 
                current_pos not in self.path[:i]):  # Not visited before this point
                self.fitness += 1
            else:
                
                break
        return self.fitness


