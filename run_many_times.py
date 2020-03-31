import main
from soc_time import Date, ZERO_DATE
from genetics import Genes
counter = 0
best_run = 0
best_date = ZERO_DATE
best_population = 0
best_genome = Genes.gene_profile_0
while True:
    counter += 1
    print(f'Номер симуляции: {counter}')
    print(f'Лучший прогон:{best_run:3d}. Дата: {best_date.display()}')
    town = main.Simulation(1000, Date(1200))
    result, final_date = town.simulate()
    print(f'Последний год: {final_date.display()}')
    current_genome = Genes.gene_profile_0
    print(f'{"Теущ. геном":13s} :{main.display_start_genotype(current_genome)}')
    if best_date < final_date:
        best_date =  final_date
        best_run = counter
        best_genome = current_genome
    print(f'{"Лучший геном":13s} :{main.display_start_genotype(best_genome)}')
    if result:
        break
    else:
        town.close()