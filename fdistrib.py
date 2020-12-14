from __future__ import annotations
from typing import Optional, List, Dict, IO
import random
import math
from common import GET_FOOD_MULTIPLIER, DIGEST_FOOD_MULTIPLIER, Gender
import genetics
from common import Stage_of_age
from family import Family


class FoodDistribution:
    feeding_log: IO
    def __init__(self, soc):

        # сюда складываются излищки еды, образовавшиеся при первоначальном распределении, потом распределятся повторно
        self.food_waste: float = 0
        self.food_per_man: float = 0
        self.abundance: bool = False
        self.socium = soc
        self.report: str = ''

    @staticmethod
    def init_files():
        FoodDistribution.feeding_log = open("./global_food_distribution.log", "w", encoding="utf16")

    @staticmethod
    def close():
        FoodDistribution.feeding_log.close()

    def distribute(self):
        # флаг изобилия. Когда изобилие, люди не отбирают еду у других людей,
        # просто берут из природных резервов
        self.abundance = False
        self.food_per_man: float = self.count_food_per_man()
        # abundance - изобилие, при отором не должна происходить конкуренция между семьями за еду
        self.abundance: bool = self.check_abundabce()
        # первоначаальное распределение еды с учетом младенцев, детей, женщин с детьми и мужчин
        self.report = self.basic_food_distribution()


        self.feeding_log.write(self.report)
        # откладываем часть еды в семейный бюджет
        for fam in self.socium.families:
            fam.food.make_food_supplies()

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
        return food_per_man if food_per_man < optimal else optimal

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
            ff = (i.wife.genes.get_trait('strongness') * GET_FOOD_MULTIPLIER[i.wife.age.stage])**2 if i.wife else 0
            ff += (i.head.genes.get_trait('strongness') * GET_FOOD_MULTIPLIER[i.head.age.stage])**2
            family_strongness.append(math.sqrt(ff))

        delta = family_strongness[0] - family_strongness[1]
        if delta != 0:
            if delta > 0:
                res = second.resource
            else:
                res = first.resource
            # ОПАСНО, нет проверки на отрицательный общак у терпил
            food_reqisition = res / 15.5 * delta
            pref = "%d:%d|" % (first.head.socium.anno.year, first.head.socium.anno.month)
            s = ""
            # delta может быть положительной и оприцптельной, поэтому расределение вдет в правильную сторону без доп проверок
            for sign, fam in zip((1, -1), (first, second)):
                movement = sign * food_reqisition
                fam.resource += movement
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
            fam.food.food_display('После создания запасов')
            soc_food_budget += fam.food.budget
            sum_family_resourses += fam.resource
        self.feeding_log.write(f'{self.socium.anno.display()} еда после создания запасов: {soc_food_budget:7.1f} + \
                               {sum_family_resourses:7.1f} = {soc_food_budget + sum_family_resourses:7.1f}\n')
        # Семьи борятся за еду только если на всех не хватает
        if self.abundance is False:
            for i in range(len(group_1)):
                self.figth_for_food(self.socium.families[group_1[i]], self.socium.families[group_2[i]])
        soc_food_budget = 0
        for fam in self.socium.families:
            fam.food_dist()
            fam.food.food_display("FINAL")
            soc_food_budget += fam.food.budget
        self.feeding_log.write(f'{self.socium.anno.display()} Потребленная еда: {soc_food_budget:7.1f}\n')


class FoodControl:
    '''
    Класс содержащий информацию для вывода статистики по питанию. Важных для симуляции переменных не содержит
    '''

    pass


class FamilySupplies:
    '''
    Формирует и распределяет семейный бюждет
    '''
    def __init__(self, family:Family):
        self.family = family
        self._supplies = 0
        '''
        # сумма личной пищи людей в семье
        self.budget = 0
        '''

    def make(self, food):
        '''полняем семейный бюджет'''
        # возможность переносить запасы на следующий ход пока не делаю
        self._supplies = 0
        for member in self.family.all:
            give = member.health.have_food * genetics.ALTRUISM_COEF * member.genes.get_trait('altruism')
            member.health.have_food_change(-give)
            self._supplies += give



    def make_food_supplies(self):
        """
        Каждый член семьи откладывает часть добытой еды в общий семейный запас self.resource.
        Доля пищи, переданной из личного в семейный бюджет, зависит от  альтруизма человека.
        """
        def get_family_role_sting(person) -> str:
            if person is self.family.head:
                s = ' Глава'
            elif person is self.family.wife:
                s = ' Жена'
            elif person in self.family.dependents:
                s = ' ребенок'
            else:
                raise Exception('Определение роли человека в семье: неизвестная роль.')
            return s

        def form_text_body() ->str:
            s = f'{get_family_role_sting(member):6s}| {member.id}|'
            s += f' alt={self.family.head.genes.get_trait("altruism"):2d}| имеет {member.health.have_food_prev:5.1f}| ' \
                 f'вкладывает {give:5.1f}| остается {member.health.have_food:5.1f}\n'
            return s

        pref = f'{self.family.head.socium.anno.year}:{self.family.head.socium.anno.month}| {self.family.id}|'
        s = pref +"-------------\n"
        self.resource = 0
        for member in self.family.all:
            give = member.health.have_food * genetics.ALTRUISM_COEF * member.genes.get_trait('altruism')
            member.health.have_food_change(-give)
            self.resource += give
            s+= pref + form_text_body()
        s = s + pref + " Всего запас: %6.1f\n" %  self.resource
        Family.family_feeding.write(s)


    def _calculate_portions(self, fam_list):
        '''
        Считаем расределение еды на всех членов семьи (пропорции)
        '''
        portions = dict()
        denominator = 0
        for member in fam_list:
            # здесь не учитываем, что старики плохо уствивают пищу и для насыщения им нужно больше, они будут получать, как взрослые
            age_proportion = min(DIGEST_FOOD_MULTIPLIER[member.age.stage], 1)
            egoism_proportion = member.genes.get_trait('harshness') / genetics.Gene.MAX_VALUE
            part = age_proportion + egoism_proportion
            portions[member] = part
            denominator += part
        for member in fam_list:
            portions[member] = portions[member] / denominator
        return portions


    def distribute(self):
        '''
        Расрелеоение пищи между членами семьи
        Если для одного еды слишком много, оставшаяся от него еда перераспределяется между оставшимися членами семьи
        Если посое всех членов семьи остается еда ...
        '''
        members_list = self.family.all.copy()
        portions = self._calculate_portions()
        # пища, уже отданная из общих запасов кому-то из семьи
        aside = 0
        food = dict()
        while len(members_list)>0:
            member = members_list.pop()
            temp_food = member.health.have_food + self._supplies * portions[member]
            ideal_food = member.health.ideal_food_amount()
            sufficient_food = min(temp_food, ideal_food)
            member.health.have_food_change(sufficient_food)
            aside +=sufficient_food
            if temp_food > ideal_food and members_list > 0:
                # если кто-то не съел своб порцию, обновляем значение запасов и считаем ноаве пропорции исходя из изменившихся запасов
                self._supplies -= aside
                aside = 0
                portions = self._calculate_portions(members_list)
        # если после распределения еды что-то осталось
        if self._supplies>0:
            # если есть живые старики, кормим стариков
            if len(self.family.parents) > 0:
                food_per_parent = self._supplies / len(self.family.parents)
                for i in self.family.parents:
                    i.health.have_food_change(food_per_parent)
                self._supplies = 0
            else:
                # если нет, перераспределяем остатки между членами семьи, не пропадать же еде
                portions = self._calculate_portions(self.family.all)
                for member in self.family.all:
                    member.health.have_food_change(self._supplies * portions[member])


    @property
    def suppplies(self):
        return self._supplies


    def family_food_display(self, message: str=''):
        pref = "%s|=================%s\n" % (self.family.id, message)
        Family.family_food_file.write(pref)
        pref = "%d:%d| %s|" % (self.family.head.socium.anno.year, self.family.head.socium.anno.month, self.family.id)
        self.budget = 0
        budget_prev = 0
        for i in self.family.all:
            self.budget += i.health.have_food
            budget_prev += i.health.have_food_prev
            if i is self.family.head:
                role = "гла"
            elif i is self.family.wife:
                role = "жен"
            else:
                role = "реб"
            s = pref + " %s| %5.1f| %5.1f| %2d\n" % (role, i.health.have_food, i.health.have_food_prev,
                                                     int(i.health.have_food/genetics.FOOD_COEF) )
            Family.family_food_file.write(s)
        b = "Бюждет до %6.1f  после %6.1f \n" % (budget_prev, self.budget)
        Family.family_food_file.write(pref + b)

