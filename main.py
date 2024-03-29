﻿import random
import os

from soc_time import Date
from human import Human
from socium import Socium
import family
import causes

import soc_time
import common
import genetics


# хочется повторяемости картины, фиксируем сид
random.seed(664)
# количество людей в начальной популяции
FIRST_POPULATION = 20
TIMELINE = Date(200)  # количество лет симуляции
HOME_DIR = os.getcwd()

class Simulation:
    def __init__(self, timeline, estimate_people):
        self.estimate_people = estimate_people
        self.init_logs()
        self.soc = Socium(1000, self.estimate_people)  # создется социум
        self.timeline = timeline

    def init_logs(self):
        common.init_sim_dir()
        self.lohfile = open("./population.txt", "w", encoding="utf-8-sig")
        self.every_man_state_log = open("./human_state.txt", "w", encoding="utf-8-sig")
        self.tribes_verbose = open("./tribes_verbose.txt", "w", encoding="utf-8-sig")

    def close(self):
        self.lohfile.close()
        self.every_man_state_log.close()
        self.tribes_verbose.close()
        all_time_lived = Human.GLOBAL_HUMAN_NUMBER
        self.soc.close(self.estimate_people)
        os.chdir(HOME_DIR)
        return all_time_lived

    def populate(self, popul):
        for p in range(popul):
            age = random.randint(9, 20)
            # почему он сразу не  добавляется в социум по праву создания, зачем отдельно добавлять
            none_parents = causes.BiolParents(None)
            self.soc.add_human(Human(self.soc, none_parents,  gender=None,  age_int=age))

    def simulate(self):
        self.soc.stat.count_soc_state()
        extinct = False
        for year in range(self.timeline.len()):
            if self.soc.stat.people_alive_number < 6:
                extinct = True
                break
            self.write_chronicle_title()
            self.soc.tictac()
            Human.write_chronicle(f'население: {self.soc.stat.people_alive_number}')
            self.write_to_logs()
        self.last_record_to_annals()
        all_time_lived = self.close()
        return not extinct, self.soc.anno, all_time_lived

    def write_chronicle_title(self):
        s = f'\n {"="*40}\n{self.soc.anno.display()}\nнаселение: {self.soc.stat.people_alive_number}'
        Human.write_chronicle(s)

    def write_to_logs(self):
        def write_lohfile(town):
            town.lohfile.write("================================================\n")
            town.lohfile.write("%s\n" % town.soc.anno.display())
            town.lohfile.write("количество племен: %d\n" % len(town.soc.stat.tribes_in_socium))
            town.lohfile.write("количество семей: %d\n" % len(town.soc.families))
            town.lohfile.write("население: %d\n" % town.soc.stat.people_alive_number)
            town.lohfile.write(town.soc.display_tribes())

        def write_human_state(town):
            town.every_man_state_log.write("================================================\n")
            town.every_man_state_log.write(f'{town.soc.anno.display()}\n')
            town.every_man_state_log.write(f'население: {town.soc.stat.people_alive_number}\n')
            for i in town.soc.people_alive:
                anno_date = f'{town.soc.anno.year}:{ town.soc.anno.month}'
                famil = f' {i.family.id}'
                a = i.id
                satge_name = i.age.stage.name

                sex = "М" if i.gender is common.Gender.MALE else "Ж"
                b = i.genes.get_trait(genetics.GN.STRONGNESS)
                c = i.genes.get_trait(genetics.GN.ABSTINENCE)
                d = i.health.satiety
                e = Date(0, 0, round(i.health.health / genetics.HEALTH_PER_DAY)).display(False)
                fb = - i.health.food_sum
                hf = i.health.have_food
                z = anno_date + famil
                z += f' {a}| {sex}|{i.age.display():14s}| {satge_name:7s}| str= {b:2d}| abs= {c:2d}| sat= {d:2d}| ' \
                     f'food= {hf:5.1f}| hbonus= {fb:6.1f}| healt={i.health.health:6.1f}| lifetim={e}\n'
                town.every_man_state_log.write(z)

        write_lohfile(self)
        write_human_state(self)
        self.tribes_verbose.write(self.soc.display_tribes_verbose())



    def last_record_to_annals(self):
        dead = []
        for person in self.soc.soc_list:
            if not person.is_alive:
                dead.append(person)
        self.soc.hall_of_fame(dead)

def display_start_genotype(genome) -> str:
    s = ''
    for name in genetics.GN:
        s += f'| {genetics.Genes.GEN_PSEUDONYM[name]:4s}:{genome[name]:3d} '
    return s

if __name__ == '__main__':
    print('Start.')

    town = Simulation(TIMELINE, estimate_people=200)

    for i in range(1):
        town.populate(FIRST_POPULATION)
        town.soc.roll_genome()

    result, final_date, atl = town.simulate()

    print(display_start_genotype(genetics.Genes.protogenome_profile))
    print(f'население за всю историю: {atl}' )
    print(f'Последний год: {final_date.display()}')

