from __future__ import annotations
from typing import Optional, List, Dict, IO
import random
import genetics
from family import Family

class FoodDistribution:
    feeding_log: IO
    def __init__(self, soc):
        self.socium =soc

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
        food_waste = 0
        # abundance - изобилие, при отором не должна происходить конкуренция между семьями за еду
        abundance = False
        # первоначальное распределение еды
        food_per_man = self.socium.FOOD_RESOURCE / self.socium.stat.people_alive_number
        if food_per_man > genetics.RICH_CONSUME_RATE * genetics.FOOD_COEF:
            abundance = True
            food_per_man_corrected = genetics.RICH_CONSUME_RATE * genetics.FOOD_COEF  # это ограничение надо будет потом убрать
        else:
            food_per_man_corrected = food_per_man
        s = f'\n==================\n{self.socium.anno.year}:{self.socium.anno.month}\n'
        s += f'Общее количество еды: {self.socium.FOOD_RESOURCE:10.2f}\n'
        s += f'Количество людей: {self.socium.stat.people_alive_number}\n'
        s += f'Изначальное количество еды на человека: {food_per_man:7.2f}\n'
        s += f'Скорректированое количество еды на человека: {food_per_man_corrected:7.2f}\n'
        for person in self.socium.people_alive:
            # присваивает каждому человеку первоначальное количество пищи
            person.health.have_food_equal(food_per_man_corrected)
            # дети до трех лет пищу не добывают
            # дети добывают вдвое меньше еды
            if person.is_baby:
                person.health.have_food_equal(0)
                food_waste += food_per_man_corrected
            elif not person.is_big:
                half_food = person.health.have_food / 2
                person.health.have_food_equal(half_food)
                food_waste += food_per_man_corrected - half_food
            # женщины с детьми добывают меньше (минус за каждого иждивенца в семье)
            # по идее эту дельту надо передавать в детский бюджет, а не выкидывать в ппустоту
            elif person.gender == 0:
                woman_food_delta = -len(
                    person.family.dependents) * genetics.FOOD_COEF / 2  # штраф к еде за каждого ребенка
                person.health.have_food_change(woman_food_delta)
                food_waste -= woman_food_delta  # штраф отрицательный, поэтому не прибавляем, а отнимаем
            # тут должен быть else. но его случай обрабатывается в самом начале без условий : это взрослые мужчины
            # print(f'человек: {person.id}  пол: {person.gender} возраст:{person.age.display()}')
        # === строгий подсчет потребляемой пищи по людям ===
        men = 0
        men_count = 0
        women_childless = 0
        women_childless_count = 0
        women_with_children = 0
        women_with_children_count = 0
        women_dep = 0  # сумма иждивенцев в семьях
        children = 0
        children_count = 0
        # считаем, сколько еды потребили все категории населения: мужчины, детные и бездетные женщины, дети
        for person in self.socium.people_alive:
            if person.is_big:
                if person.gender:
                    men_count += 1
                    men += person.health.have_food
                else:
                    if len(person.family.dependents) == 0:
                        women_childless_count += 1
                        women_childless += person.health.have_food
                    else:
                        women_dep += len(person.family.dependents)
                        women_with_children_count += 1
                        women_with_children += person.health.have_food
            else:
                children += person.health.have_food
                children_count += 1
        teor_men = men_count * food_per_man_corrected
        teor_women_childless = women_childless_count * food_per_man_corrected
        teor_women_with_children = women_with_children_count * food_per_man_corrected - women_dep * genetics.FOOD_COEF / 2
        teor_children = children_count * food_per_man_corrected / 2
        s += "=======================================\n"
        s += "Мужчины %d| потребили фактически %8.2f| теоретически %8.2f|\n" % (men_count, men, teor_men)
        s += "Бездетные женщины %d| потребили фактически %7.2f| теоретически %7.2f|\n" % (
        women_childless_count, women_childless, teor_women_childless)
        s += "Детные женщины %d| потребили фактически %8.2f| теоретически %8.2f| из-за %d иждивенцев\n" % (
        women_with_children_count, women_with_children, teor_women_with_children, women_dep)
        s += "Дети %d| потребили фактически %8.2f| теоретически %8.2f|\n" % (children_count, children, teor_children)
        real_f = men + women_childless + women_with_children + children
        teor_f = teor_men + teor_women_childless + teor_women_with_children + teor_children
        s += f'Остатки пищи: {food_waste}\n'
        s += "Итог фактич  %8.2f| теоретич  %8.2f|\n" % (real_f, teor_f)

        # ================================
        # считаем пропавшую еду
        wasted_food = 0
        # еда пропавшая из-за детей
        wasted_food += self.socium.stat.children * food_per_man / 2
        s += "Еда пропавшая из-за %d детей: %8.2f\n" % (self.socium.stat.children, wasted_food)
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

        # откладываем часть еды в семейный бюджет
        self.feeding_log.write(s)
        for fam in self.socium.families:
            fam.make_food_supplies()

        def shuffle_families(number):
            diap = number // 3  # треть семей
            seq = [x for x in range(number)]
            random.shuffle(seq)
            m = seq[:diap]
            n = seq[diap:2 * diap]
            return (m, n)  # две группы семей, которые будут делить еду между собой

        sum_family_resourses = 0
        soc_food_budget = 0
        group_1, group_2 = shuffle_families(len(self.socium.families))
        for fam in self.socium.families:
            fam.food_display("После создания запасов")
            soc_food_budget += fam.budget
            sum_family_resourses += fam.resource
        self.feeding_log.write("%s еда после создания запасов : %7.1f + %7.1f = %7.1f\n" % (
        self.socium.anno.display(), soc_food_budget, sum_family_resourses, soc_food_budget + sum_family_resourses))

        for i in range(len(group_1)):
            Family.figth_for_food(self.socium.families[group_1[i]], self.socium.families[group_2[i]], abundance)
        soc_food_budget = 0
        for fam in self.socium.families:
            fam.food_dist()
            fam.food_display("FINAL")
            soc_food_budget += fam.budget
        self.feeding_log.write("%s Потребленная еда: %7.1f\n" % (self.socium.anno.display(), soc_food_budget))


