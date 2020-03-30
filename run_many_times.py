import main
from soc_time import Date
counter = 0
while True:
    counter += 1
    print(f'Номер симуляции: {counter}')
    town = main.Simulation(4000, Date(1200))
    result, message = town.simulate()
    print(message)
    print(main.display_start_genotype())
    if result:
        break
    else:
        town.close()