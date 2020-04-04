import main
from soc_time import Date, ZERO_DATE
from genetics import Genes
def many_runs(crowd, period):
    counter = 0
    best_run = 0
    best_date = ZERO_DATE
    best_population = 0
    best_genome = Genes.gene_profile_0
    while True:
        counter += 1
        print(f'Номер симуляции: {counter}')
        print(f'Лучший прогон:{best_run:3d}. Дата: {best_date.display()}')
        town = main.Simulation(crowd, Date(period))
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


def many_sucsessful_runs(crowd, period):
    while True:
        town = main.Simulation(crowd, Date(period))
        result, final_date = town.simulate()
        if result:
            print(main.display_start_genotype(Genes.gene_profile_0))
        town.close()

if __name__ == '__main__':
    #many_runs(1000, 1200)
    many_sucsessful_runs(1000, 1200)