from __future__ import annotations
from typing import Optional, List, Dict, IO
import random
import math
from common import GET_FOOD_MULTIPLIER, DIGEST_FOOD_MULTIPLIER, Gender
import genetics
from family import Family
from common import Stage_of_age

class FoodDistribution:
    feeding_log: IO
    def __init__(self, soc):

        # сюда складываются излищки еды, образовавшиеся при первоначальном распределении, потом распределятся повторно
        self.food_waste: float = 0
        self.food_per_man: float = 0
        self.abundance: bool = False
        self.socium = soc
        self.report: str = ''

    @classmethod
    def init_files(cls):
        cls.feeding_log = open("./global_food_distribution.log", "w", encoding="utf16")

    @classmethod
    def close(cls):
        cls.feeding_log.close()

    def distribute(self):
        # флаг изобилия. Когда изобилие, люди не отбирают еду у других людей,
        # просто берут из природных резервов
        self.abundance = False
        self.food_per_man: float = self.count_food_per_man()
        # abundance - изобилие, при отором не должна происходить конкуренция между семьями за еду
        self.abundance: bool = self.check_abundabce()
        # первоначальное распределение еды с учетом младенцев, детей, женщин с детьми и мужчин
        self.report = self.basic_food_distribution()


        self.feeding_log.write(self.report)
        # откладываем часть еды в семейный бюджет
        for fam in self.socium.families:
            fam.food.make()

        self.family_food_redistibution()

    def count_food_per_man(self) -> float:
        '''
        Сколько еды приходится на взрослого мужчину за один ход.
        Другие возрастные и половые группы пляшут от этого значения
        '''
        # Добавляем нераспределенную еду с проршлого хода
        # food_per_man = (self.socium.FOOD_RESOURCE + self.food_waste)/ self.socium.stat.people_alive_number
        # вариант без передачи остатков с прошлого хода - он более предсказуемый
        food_per_man = self.socium.FOOD_RESOURCE  / self.socium.stat.people_alive_number
        self.food_waste = 0
        optimal = genetics.RICH_CONSUME_RATE * genetics.FOOD_COEF
        return min(food_per_man,optimal)

    def check_abundabce(self):
        return self.food_per_man < self.socium.FOOD_RESOURCE / self.socium.stat.people_alive_number

    def basic_food_distribution(self):
        # первоначальное распределение еды
        s = f'\n==================\n{self.socium.anno.year}:{self.socium.anno.month}\n'
        s += f'Общее количество еды: {self.socium.FOOD_RESOURCE:10.2f}\n'
        s += f'Количество людей: {self.socium.stat.people_alive_number}\n'
        s += f'Изобилие: {self.abundance}\n'
        s += f'Количество еды на человека: {self.food_per_man:7.2f}\n'
        for person in self.socium.people_alive:
            # присваивает каждому человеку первоначальное количество пищи
            mult = GET_FOOD_MULTIPLIER[person.age.stage]
            food = mult * self.food_per_man
            self.food_waste += self.food_per_man - food
            person.health.have_food_equal(food)
            # женщины с детьми добывают меньше (минус за каждого иждивенца в семье)
            # по идее эту дельту надо передавать в детский бюджет, а не выкидывать в пустоту
            if person.gender is Gender.FEMALE and len(person.family.dependents) > 0:
                # первый ребенок уменьшает добываемый матерью паек на четверть
                # каждый последующий ребенок уменьшает траф к добываемой матерью пище в два раза
                # после шестого ребенка штраф не рассчитывается, потому что его вклад ничтожен
                # 1/4 + 1/8 + 1/16 + 1/32...
                dep_sum = 64 - 2**(6 - min(len(person.family.dependents), 6))
                woman_with_children_food_penalty = person.health.have_food * dep_sum / 128.0 # 128 это знаменатель, до которого рассчитывается ряд
                person.health.have_food_change(-woman_with_children_food_penalty)
                self.food_waste += woman_with_children_food_penalty
        return s

    @staticmethod
    def figth_for_food(first: Family, second: Family):
        family_strongness = []
        for i in (first, second):
            # нельзя чтобы у семейной пары было слишком большое приемущество над одиночками, поэтому берем среднеквадратичную силу
            ff = (i.wife.genes.get_trait(genetics.GN.STRONGNESS) * GET_FOOD_MULTIPLIER[i.wife.age.stage])**2 if i.wife else 0
            ff += (i.head.genes.get_trait(genetics.GN.STRONGNESS) * GET_FOOD_MULTIPLIER[i.head.age.stage])**2
            family_strongness.append(math.sqrt(ff))

        delta = family_strongness[0] - family_strongness[1]
        if delta != 0:
            if delta > 0:
                res = second.food.supplies
            else:
                res = first.food.supplies
            # ОПАСНО, нет проверки на отрицательный общак у терпил
            food_reqisition = res / 15.5 * delta
            pref = "%d:%d|" % (first.head.socium.anno.year, first.head.socium.anno.month)
            s = ""
            # delta может быть положительной и оприцптельной, поэтому расределение вдет в правильную сторону без доп проверок
            for sign, fam in zip((1, -1), (first, second)):
                movement = sign * food_reqisition
                fam.food.change_supplies(movement)
                direct = "семья нашла " if movement > 0 else "семья потеряла "
                s = s + pref + " %s|" % fam.id + direct + "%5.1f\n" % movement
            Family.family_feeding.write(s)

    def family_food_redistibution(self):
        def shuffle_families(number):
            # создаем и перемешиваем индексы, по которым потом будем обращаться к семьям
            seq = [x for x in range(number)]
            random.shuffle(seq)
            # выбираем из перемешанных индексов две трети
            diap = number // 3  # треть семей
            # делим индексы пополам ,чтобы потом сталкивать семьи в конкурентной борьбе
            m = seq[:diap]
            n = seq[diap:2 * diap]
            return m, n  # две группы семей, которые будут делить еду между собой

        sum_family_resourses = 0
        soc_food_budget = 0
        group_1, group_2 = shuffle_families(len(self.socium.families))
        for fam in self.socium.families:
            fam.food.family_food_display('После создания запасов')
            soc_food_budget += fam.food.budget
            sum_family_resourses += fam.food.supplies
        self.feeding_log.write(f'{self.socium.anno.display()} еда после создания запасов: {soc_food_budget:7.1f} + {sum_family_resourses:7.1f} = {soc_food_budget + sum_family_resourses:7.1f}\n')
        # Семьи борятся за еду только если на всех не хватает
        if self.abundance is False:
            for i in range(len(group_1)):
                self.figth_for_food(self.socium.families[group_1[i]], self.socium.families[group_2[i]])
        soc_food_budget = 0
        for fam in self.socium.families:
            fam.food.distribute()
            #fam.food.distribute_disp()
            fam.food.family_food_display("FINAL")
            soc_food_budget += fam.food.budget
        self.feeding_log.write(f'{self.socium.anno.display()} Потребленная еда: {soc_food_budget:7.1f}\n')


class FoodControl:
    '''
    Класс содержащий информацию для вывода статистики по питанию. Важных для симуляции переменных не содержит
    '''

    pass
