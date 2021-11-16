from __future__ import annotations
from typing import Optional, List, Dict, IO
import csv
import random
import common
from soc_time import Date, Anno
#import family
from family import Family
from human import Human
from fdistrib import FoodDistribution
import statistics
import genetics


TIME_TO_EXCLUDE_DEAD_ANCESTORS = Date(40)

class Socium:
    ESTIMAED_NUMBER_OF_PEOPLE = None
    FOOD_RESOURCE = None

    def __init__(self, anno=1000, estimate_people=100):
        # список всех людей в социуме, на данный момент включая мертвых (проверить)
        genetics.Genes.init_protogenome()
        Socium.class_var_init(estimate_people)
        Human.init_files()
        Family.init_files()
        FoodDistribution.init_files()
        self.soc_list: List[Human] = list()
        self.families: List[Family] = list()

        self.stat = statistics.Soc_stat(self)
        self.food = FoodDistribution(self)

        self.person_stat_file = open('./person_features_table.csv', 'w', encoding="UTF16")
        self.person_stat = csv.writer(self.person_stat_file, delimiter='\t', lineterminator='\n')
        pers_stat_header = list()
        for i in genetics.GN:
            pers_stat_header.append(i)
        hextend = ['макс. возр. отца', 'возр. отца при рождении', 'макс. возр. матери', 'возр. матери при рождении', 'каким по счету родился', 'кол-во супругов', 'кол-во детей', 'возраст смерти']
        pers_stat_header.extend(hextend)
        self.person_stat.writerow(pers_stat_header)
        # текущий год
        self.anno: Anno = Anno(anno)
        # локальный счетчик смертей, после появления чужака обнуляется
        self.short_death_count: int = 0
        # общий счетчик смертей
        self.global_death_count: int = 0
        # давно умершие родственники (чтобы зря не крутить большие циклы)
        self.forgotten: List = []
        self.people_alive: List = []

    @staticmethod
    def class_var_init(estimate_people):
        Socium.ESTIMAED_NUMBER_OF_PEOPLE = estimate_people # предполагаемое количество людей
        # общее количество пищи за ход, которое люди делят между собой
        Socium.FOOD_RESOURCE = genetics.FOOD_COEF * genetics.NORMAL_CONSUME_RATE * Socium.ESTIMAED_NUMBER_OF_PEOPLE


    def close(self, estimate_people):
        self.__class__.class_var_init(estimate_people)
        FoodDistribution.close()
        Human.close()
        Family.close()

    def add_human(self, human):
        self.soc_list.append(human)

    def remove_human(self, human):
        self.soc_list.remove(human)

    def clear_people_alive(self):
        self.people_alive = [] #живые люди

    def people_alive_add(self, person):
        self.people_alive.append(person)

    def forgot_ancestors(self):
        temp = []
        self.forgotten = []
        for person in self.soc_list:
            if not person.is_alive and self.anno - person.death_date > TIME_TO_EXCLUDE_DEAD_ANCESTORS:
                self.forgotten.append(person)
            else:
                temp.append(person)
        self.soc_list = temp
        self.hall_of_fame(self.forgotten)


    def tictac(self):
        def families_list_update():
            temp = []
            for fam in self.families:
                if not fam.obsolete:
                    temp.append(fam)
            self.families = temp

        self.anno.increase()
        # уменьшаем количество пищи
        if self.anno.year_starts() and self.anno.year % 4 == 0:
            pass
        #self.reduce_food_resource()

        # чистим социум от давно умерших людей
        if self.anno.year_starts() and self.anno.year % 40 == 0: # раз в 40 лет
            self.forgot_ancestors()

        #  Распределение еды.Общий ресурс веды делится на всех жителей.
        #  Потом еда распределяется внутри семьи, а потом каждый употребляет еду индивидуально
        #self.food_distribution()
        self.food.distribute()

        # женим холостых людей
        self.search_spouce()
        # проверяем семьи # в результате свадеб часть семей могла устареть
        families_list_update()

        # каждый человек делает свои индивидуальные дела: ест, рожает детей, умирает
        for person  in self.people_alive:
            person.live()

        #----------------------------------------------
        # вот он метод, из-за которого у меня основные проблемы. Он енправильно обрабатывает семьи
        # семьи трудный, постоянно меняющийся объект, в отличии от людей. Когда перебираешь людей,
        #  социум рзвивается стабильно. Когда обрабатываешь семьи - все вымирают
        #---------------------------------------------
        '''
        for fam in self.families:
            fam.live()
        # проверяем семьи # в результате смерти главы семьи, часть семей могла устареть
        '''
        families_list_update()

        # добавляем странника именно в это место, потому что список живых людей еще не модифицирован
        # и участвовать в общественной жизни страннику нельзя
        if self.anno.year_starts():
            if self.anno.year < 1200:
                self.stranger_comes_to_socium()

        self.families[0].print_something("\n==============================\n"+ self.anno.display())
        self.families[0].print_something("Количество семей: %d" % len(self.families))
        for fam in self.families:
            fam.del_grown_up_children()
            fam.print_family()
        # подсчет статистики социума
        self.stat.count_soc_state()
        self.stat.get_families_in_socium()


        # считается, как изменяются средние значения генов (каждый год считать не обязательно)
        if self.anno.year_starts() and self.anno.year % 4 ==0:
            self.stat.count_genes_average()


    def	search_spouce(self):
        def success_marry_chanse(person1, person2):
            attraction = (genetics.lust_coef(person1.age.year) *
                          genetics.lust_coef(person2.age.year))
            return attraction >= random.random()
        # если есть возможность создать хоть одну пару
        if min(self.stat.unmarried_adult_men_number, self.stat.unmarried_adult_women_number) > 0:
            s = f'Холостых мужчин: {self.stat.unmarried_adult_men_number}\nХолостых женщин: {self.stat.unmarried_adult_women_number}'
            Human.write_chronicle(s)
            if self.stat.unmarried_adult_men_number < self.stat.unmarried_adult_women_number:
                a = self.stat.unmarried_adult_men
                b = self.stat.unmarried_adult_women
            else:
                b = self.stat.unmarried_adult_men
                a = self.stat.unmarried_adult_women
            random.shuffle(b)
            # за один раз можно попытать счастья только с одним избранниким
            # цикл идет по представителям пола, который сейчас в меньшинстве
            for person in a:
                if person.close_ancestors.isdisjoint(b[-1].close_ancestors): # ксли не являются близкими родственниками
                    if success_marry_chanse(person, b[-1]):
                        tup = (person.id, b[-1].id, person.name.display(), person.age.year, b[-1].name.display(), b[-1].age.year)
                        Human.write_chronicle(Human.chronicle_marriage.format(*tup))
                        person.get_marry(b[-1])
                        b[-1].get_marry(person)
                        person.score.update(person.score.MARRY_SCORE)
                        b[-1].score.update(b[-1].score.MARRY_SCORE)
                        if person.gender is common.Gender.MALE:
                            person.family.unite_families(b[-1].family)
                        else:
                            b[-1].family.unite_families(person.family)
                    b.pop() # человек удаляется из списка кандидатов в супруги независтмо от того, заключил он брак или нет


    def stranger_comes_to_socium(self):
        '''
        процедура для пополнения социума свежей кровью.
        в среднем после пяти умерших персонажей в социум приходит взрослый чужак,
        который никому не является родственником и может завести семью
        '''
        if self.short_death_count > random.randrange(9):
            # пока будет случайный пол, но пол незнакомцев должен выравнивать демографическую обстановку в социуме
            self.add_human(Human(self, (None, None), gender=None, age_int=random.randrange(18, 35)))
            self.short_death_count = 0


    def display_tribes(self):
        '''
        Краткая сводка по племенам, когда выводятся их айдишники, количество членов и средние значения генов в племени
        '''
        st = ''
        for tribe in self.stat.tribes_in_socium:
            elder_of_tribe = self.stat.tribes_in_socium[tribe][0]
            tribe_family_name = elder_of_tribe.name.family_name[1]
            st += '%d:%d| '% (self.anno.year, self.anno.month)
            st += '%12s| %7s: %4d | ' % (tribe_family_name, tribe, self.stat.families_in_tribe_count[tribe])
            st += '%4d | %s\n' %(self.stat.tribes_in_socium_count[tribe], self.stat.count_tribe_genes_average(tribe))
        return st


    def display_tribes_verbose(self):
        '''
        Подробная информация о племенах. С перечислением каждого члена племени, к какой семье он нотнсится, какую роль
        в семье занимает. Ну и указание ФИО и идентификатора. В общем выводятся все живые люди.
        '''
        st = ''
        for tri in self.stat.tribes_in_socium:
            elder_of_tribe = self.stat.tribes_in_socium[tri][0]
            for fam in self.stat.families_in_tribe[tri]:
                st += ("-------------\n")
                date_fam = "%d:%d| %s| %s| " % (self.anno.year, self.anno.month, tri, fam.id)
                for member in fam.all:
                    if member is fam.head:
                        role = 'глав'
                    elif member is fam.wife:
                        role = 'жена'
                    else:
                        role = 'чадо'
                    st =  st + date_fam + role
                    st +=" | %s| %s\n" % (member.id, member.name.display())
        return st


    def hall_of_fame(self, list_of_dead):
        hall= open("./hall_of_fame.txt", "a", encoding = "UTF16")
        list_of_dead.sort(key=lambda x: x.id)
        for person in list_of_dead:
            # записи про каждого мертвого человека с подробностями его жизни
            hall.write("\n====================================\n")
            hall.write(person.necrolog())
            self.person_stat.writerow(person.magareport())
        hall.close()

