from __future__ import annotations
from typing import Optional, List, Dict, IO
import random
import genetics
from common import Stage_of_age
from family import Family

class FoodDistribution:
    feeding_log: IO
    def __init__(self, soc):
        self.socium =soc
        self.report: str = ''

    @staticmethod
    def init_files():
        FoodDistribution.feeding_log = open("./xoutput/global_food_distribution.log", "w", encoding="utf16")

    @staticmethod
    def close():
        FoodDistribution.feeding_log.close()


    def distribute(self):
        # флаг изобилия. Когда изобилие, люди не отбирают еду у других людей,
        # просто берут из природных резервов

        # сюда складываются излищки еды, образовавшиеся при первоначальном распределении, потом распределятся повторно
        self.food_waste = 0

        self.abundance = False
        self.food_per_man: float = self.count_food_per_man()
        # abundance - изобилие, при отором не должна происходить конкуренция между семьями за еду
        self.abundance: bool = self.check_abundabce()
        # первоначаальное распределение еды с учетом младенцев, детей, женщин с детьми и мужчин
        self.report = self.basic_food_distribution()
        self.report += self.recalculate_food_distribution()

        self.report += self.count_wasted_food()

        self.feeding_log.write(self.report)
        # откладываем часть еды в семейный бюджет
        for fam in self.socium.families:
            fam.make_food_supplies()

        self.family_food_redistibution()

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
            return (m, n)  # две группы семей, которые будут делить еду между собой

        sum_family_resourses = 0
        soc_food_budget = 0
        group_1, group_2 = shuffle_families(len(self.socium.families))
        for fam in self.socium.families:
            fam.food_display('После создания запасов')
            soc_food_budget += fam.budget
            sum_family_resourses += fam.resource
        self.feeding_log.write(f'{self.socium.anno.display()} еда после создания запасов: {soc_food_budget:7.1f} + \
                               {sum_family_resourses:7.1f} = {soc_food_budget + sum_family_resourses:7.1f}\n')
        for i in range(len(group_1)):
            Family.figth_for_food(self.socium.families[group_1[i]], self.socium.families[group_2[i]], self.abundance)
        soc_food_budget = 0
        for fam in self.socium.families:
            fam.food_dist()
            fam.food_display("FINAL")
            soc_food_budget += fam.budget
        self.feeding_log.write(f'{self.socium.anno.display()} Потребленная еда: {soc_food_budget:7.1f}\n')

    def count_wasted_food(self):
        # ================================
        # считаем пропавшую еду
        wasted_food = 0
        # еда пропавшая из-за детей
        wasted_food += self.socium.stat.children * self.food_per_man / 2
        s = "Еда пропавшая из-за %d детей: %8.2f\n" % (self.socium.stat.children, wasted_food)
        # еда пропавшая из-за женщин с иждивенцами
        dependents_sum = 0
        for fam in self.socium.families:
            dependents_sum += len(fam.dependents)
        dep_wast = dependents_sum * genetics.FOOD_COEF / 2
        s += "Еда пропавшая из-за %d иждивенцев: % 7.1f\n" % (dependents_sum, dep_wast)
        wasted_food += dep_wast
        s += "Пропавшая еда в целом: % 7.1f\n" % wasted_food
        soc_food_budget = 0
        for fam in self.socium.families:
            fam.food_display("первоначальное распределение")
            soc_food_budget += fam.budget
        s += "Сумма распределенного % 7.1f| и пропавшего % 7.1f|: % 7.1f\n" % (
            soc_food_budget, wasted_food, soc_food_budget + wasted_food)
        s += "%s первоначальное распределение еды : %7.1f\n" % (self.socium.anno.display(), soc_food_budget)
        return s

    def recalculate_food_distribution(self):
        # === строгий подсчет потребляемой пищи по людям ===
        men_food_sum = 0
        men_count = 0
        women_childless_food_sum = 0
        women_childless_count = 0
        women_with_children_food_sum = 0
        women_with_children_count = 0
        women_dependents = 0  # сумма иждивенцев в семьях
        children_food_sum = 0
        children_count = 0
        # считаем, сколько еды потребили все категории населения: мужчины, детные и бездетные женщины, дети
        for person in self.socium.people_alive:
            if person.is_big:
                # взрослые
                if person.gender:
                    # мужчины
                    men_count += 1
                    men_food_sum += person.health.have_food
                else:
                    if len(person.family.dependents) == 0:
                        # бездетные женщины
                        women_childless_count += 1
                        women_childless_food_sum += person.health.have_food
                    else:
                        # женщины с иждивенцами
                        women_dependents += len(person.family.dependents)
                        women_with_children_count += 1
                        women_with_children_food_sum += person.health.have_food
            else:
                # дети
                children_food_sum += person.health.have_food
                children_count += 1
        teor_men = men_count * self.food_per_man
        teor_women_childless = women_childless_count * self.food_per_man
        teor_women_with_children = women_with_children_count * self.food_per_man - women_dependents * genetics.FOOD_COEF / 2
        teor_children = children_count * self.food_per_man / 2
        s = "=======================================\n"
        s += "Мужчины %d| потребили фактически %8.2f| теоретически %8.2f|\n" % (men_count, men_food_sum, teor_men)
        s += "Бездетные женщины %d| потребили фактически %7.2f| теоретически %7.2f|\n" % (
            women_childless_count, women_childless_food_sum, teor_women_childless)
        s += "Детные женщины %d| потребили фактически %8.2f| теоретически %8.2f| из-за %d иждивенцев\n" % (
            women_with_children_count, women_with_children_food_sum, teor_women_with_children, women_dependents)
        s += "Дети %d| потребили фактически %8.2f| теоретически %8.2f|\n" % (children_count, children_food_sum, teor_children)
        real_f = men_food_sum + women_childless_food_sum + women_with_children_food_sum + children_food_sum
        teor_f = teor_men + teor_women_childless + teor_women_with_children + teor_children
        s += f'Остатки пищи: {self.food_waste}\n'
        s += "Итог фактич  %8.2f| теоретич  %8.2f|\n" % (real_f, teor_f)
        return s

    def count_food_per_man(self) -> float:
        food_per_man = self.socium.FOOD_RESOURCE / self.socium.stat.people_alive_number
        if food_per_man > genetics.RICH_CONSUME_RATE * genetics.FOOD_COEF:
            self.abundance = True
            food_per_man = genetics.RICH_CONSUME_RATE * genetics.FOOD_COEF  # это ограничение надо будет потом убрать
        return  food_per_man

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
            person.health.have_food_equal(self.food_per_man)
            # дети до трех лет пищу не добывают
            # дети добывают вдвое меньше еды
            if person.age_stage == Stage_of_age.BABY:
                person.health.have_food_equal(0)
                self.food_waste += self.food_per_man
            elif person.age_stage in  (Stage_of_age.CHILD, Stage_of_age.TEEN):
                half_food = person.health.have_food / 2
                person.health.have_food_equal(half_food)
                self.food_waste += self.food_per_man - half_food
            # женщины с детьми добывают меньше (минус за каждого иждивенца в семье)
            # по идее эту дельту надо передавать в детский бюджет, а не выкидывать в пустоту
            elif person.gender == 0:
                # штраф к еде за каждого ребенка
                woman_with_children_food_penalty = len(person.family.dependents) * genetics.FOOD_COEF / 2
                person.health.have_food_change(-woman_with_children_food_penalty)
                self.food_waste += woman_with_children_food_penalty
        return s

