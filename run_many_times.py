import main
from soc_time import Date
counter = 0
while True:
    counter += 1
    print(f'Номер симуляции: {counter}')
    town = main.Simulation(4000, Date(1200))
    result = town.simulate()
    if result:
        break
    else:
        town.close()