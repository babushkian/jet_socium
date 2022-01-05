import main
from soc_time import Date, ZERO_DATE
import datetime
from genetics import Genes
import random

EXPERIMENTS = 1
def many_runs(crowd, period):
    counter = 0
    best_run = 0
    best_date = ZERO_DATE
    best_population = 0
    best_genome = Genes.protogenome_profile
    while True:
        counter += 1
        print(f'Номер симуляции: {counter}')
        print(f'Лучший прогон:{best_run:3d}. Дата: {best_date.display()}')
        town = main.Simulation(crowd, Date(period))
        result, final_date = town.simulate()
        print(f'Последний год: {final_date.display()}')
        current_genome = Genes.protogenome_profile
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


def many_sucsessful_runs( period, estimated_people):
    global EXPERIMENTS
    while True:
        t = datetime.datetime.now()
        st = t.strftime("%H:%M:%S %d.%m.%Y")

        print(f'симуляция № {EXPERIMENTS} {st}')
        town = main.Simulation(Date(period), estimated_people)
        town.populate(main.FIRST_POPULATION)
        town.soc.roll_genome()
        result, final_date, _ = town.simulate()
        EXPERIMENTS += 1
        if result:
            print(main.display_start_genotype(Genes.protogenome_profile))
        town.close()

if __name__ == '__main__':
    #many_runs(1000, 1800)
    random.seed(0)
    many_sucsessful_runs( 1000, 400)