﻿from __future__ import annotations
import random
from typing import Optional, List
from enum  import Enum
import math
from common import GET_FOOD_MULTIPLIER
import genetics
import human
class FE(Enum):
    MOTHER = 0
    FATHER = 1


# при максимальном альтруизме вкадывает в семейный бюждет всю  еду. При минимальном - нисколько.
ALTRUISM_COEF = 1/genetics.Gene.MAX_VALUE

class Family:
    family_log_file = None
    family_food_file = None
    family_feeding = None

    def __init__(self, head: 'human.Human', depend: Optional[List[human.Human]]=None):  # (человек; список иждивенцев)
        self.obsolete: bool = False
        self.id: str = generate_family_id()
        self.head: human.Human = head
        self.head.socium.families.append(self) # добавляет семью в список семей
        self.husband: Optional[human.Human] = None
        self.wife: Optional[human.Human] = None
        self.parents: List[human.Human] = list()
        self.add_parents()
        self.all: List[human.Human] = [self.head] # все члены семьи кроме стариков, которые и так не члены семьи
        # список детей (не обязательно родных)
        self.dependents: List[Optional[human.Human]] = list()
        if depend:
            for i in depend:
                self.add_child(i)
        # пищевой ресурс семьи
        self.resource = 0
        s = f'Новая семья: {self.id}| {self.head.name.display()}| {self.head.id}| возраст - {self.head.age.year} лет.\n'
        self.family_log_file.write(s)


    @staticmethod
    def init_files():
        Family.family_log_file = open("./families.log", "w", encoding="utf16")
        Family.family_food_file = open("./family_food_distrib.log", "w", encoding="utf16")
        Family.family_feeding = open("./family_feeding.log", "w", encoding="utf16")

    @staticmethod
    def close():
        Family.family_log_file.close()
        Family.family_food_file.close()
        Family.family_feeding.close()

    def add_parents(self):
        for i in [self.head.father, self.head.mother]:
            if i is not None:
                if i.is_alive:
                    self.parents.append(i)

    def add_child(self, person: human.Human):
        self.dependents.append(person)
        self.all.append(person)
        person.family = self


    def add_dependents(self, family: Family):
        for i in family.dependents:
            if not i.age.is_big:
                i.tribe_name = self.head.tribe_name
                # меняем имя и фамилию
                i.name.change_father(self.head)
                i.name.change_family_name(self.head)
                self.add_child(i)


    def unite_families(self, other: Family):
        # добавляем жену в семью мужа. Семья жены уничтожается
        # объединяем родителей жены и мужа
        # объединяем иждивенцев жены и мужа
        # у жены удаляются родители прежнего мужа
        s = "Объединились семьи:\n"
        s += "\t %s| %s| %s\n" % (self.id, self.head.id, self.head.name.display())
        s += "\t %s| %s| %s\n" % (other.id, other.head.id, other.head.name.display())
        self.family_log_file.write(s)
        self.wife: human.Human  = other.head
        self.husband: human.Human  = self.head
        self.wife.tribe_name = self.head.tribe_name
        self.all.append(self.wife)
        self.parents.extend(other.parents)
        self.add_dependents(other)
        self.family_disband(other)
        self.wife.family = self


    def divide_families(self):
        # это разводик
        # у жены генерится новая семья, дети к совоему отцу перестают иметь отношение
        s = "=======Семья | %s | распалась\n" % self.id
        s += "\t %s| %s\n" % (self.head.id, self.head.name.display())
        s += "\t %s| %s\n" % (self.wife.id, self.wife.name.display())
        self.family_log_file.write(s)
        children = self.wife.family.dependents[:] # передаем содержимое, а не объект
        self.wife.family = Family(self.wife, children)
        # мужчина бросает всех иждивенцев на жену
        self.dependents = []
        # родители разделяются на линии жены и мужа
        self.parents = []
        self.add_parents()
        # никто ничей муж и не жена, только главы семьи
        self.husband = None
        self.wife = None
        self.all = [self.head]

    def family_disband(self, family: Family):
        '''
        Уничтожение семьи происходит в двух случаях:
        1) при свадьбе семья жены уничтожается - жена с иждивенцами переходит в семью мужа
        2) при смерти холостого гоавы семьи. Иждивенцы не наслебуют его семью, а создаютс собственные
        '''
        family.obsolete = True
        family.head = None
        family.husband = None
        family.wife = None
        family.all = []
        family.dependents = []

    def dead_in_family(self, person: human.Human):
        if person not in self.dependents:
            if self.wife: # нельзя применять person.married(), так как в person.die супруг уже убран
                self.spouse_dies(person)
            else: # одинок или одинеока
                self.orphane_family()
        else:
            self.child_dies(person)

    def spouse_dies(self, person: human.Human):
        # когда супруг умирает, семья сохраняеися
        # списки родителей и иждивенцев остаются без изменения
        # если умирает супруг, жена становится главой семьи
        if person == self.head:
            s ="\nВ семье |%s|  умер супруг |%s| %s\n"% (self.id, self.head.id, self.head.name.display())
            self.all.remove(self.head)
            self.head = self.wife
            self.husband = None
            self.wife = None
            s += "Теперь |%s| %s глава семьи.\n" % (self.head.id, self.head.name.display())
        else:
            s = "\nВ семье |%s|  умерла супруга |%s| %s\n" % (self.id, self.wife.id, self.wife.name.display())
            self.all.remove(self.wife)
            self.husband = None
            self.wife = None
        self.family_log_file.write(s)


    def orphane_family(self):
        # если у детей умирают оба родителя, они становятся главами своих собственных семей
        if len(self.dependents) > 0:
            s = "%s| %s из семьи |%s| умер, оставив несовершеннолетних детей.\n" % (self.head.id, self.head.name.display(), self.id)
            for i in self.dependents:
                i.family = Family(i)
        else:
            s = "%s| %s из семьи |%s| умер в одиночестве.\n" % (self.head.id, self.head.name.display(), self.id)
        self.family_log_file.write(s)
        self.family_disband(self)


    def child_dies(self, person: human.Human):
        self.dependents.remove(person)
        self.all.remove(person)

    def make_food_supplies(self):
        """
        Каждый член семьи откладывает часть добытой еды в общий семейный запас self.resource.
        Доля пищи, переданнойи из личного в семейный бюджет, зависит от  альтруизма человека.
        """
        def get_family_role_sting(person: human.Human) -> str:
            if person is self.head:
                s = ' Глава'
            elif person is self.wife:
                s = ' Жена'
            elif person in self.dependents:
                s = ' ребенок'
            else:
                raise Exception('Определение роли человека в семье: неизвестная роль.')
            return s

        def form_text_body() ->str:
            s = f'{get_family_role_sting(member):6s}| {member.id}|'
            s += f' alt={self.head.genes.get_trait("altruism"):2d}| имеет {member.health.have_food_prev:5.1f}| ' \
                 f'вкладывает {give:5.1f}| остается {member.health.have_food:5.1f}\n'
            return s

        pref = f'{self.head.socium.anno.year}:{self.head.socium.anno.month}| {self.id}|'
        s = pref +"-------------\n"
        self.resource = 0
        for member in self.all:
            give = member.health.have_food * ALTRUISM_COEF * member.genes.get_trait('altruism')
            member.health.have_food_change(-give)
            self.resource += give
            s+= pref + form_text_body()
        s = s + pref + " Всего запас: %6.1f\n" %  self.resource
        self.family_feeding.write(s)


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

    def food_dist(self):
        # префикс для описания описания питания семей, создающийся каждый цикл
        pref = f'{self.head.socium.anno.year}:{self.head.socium.anno.month}| {self.id}|'
        s = pref +"---- питание ---------\n"
        s = s+ pref +"Запасы: %6.1f\n" % self.resource
        # кормим детей
        if len(self.dependents) > 0:
            dependents_budget = self.resource / 2
            self.resource /= 2

            # кормим иждивенцев поровну
            food_addon_per_child = dependents_budget / len(self.dependents)
            s = s + pref + "Кромим %d детей\n" % len(self.dependents)
            s = s + pref + "Каждому выдаем по %5.1f еды\n" % food_addon_per_child
            for child in self.dependents:
                temp = child.health.have_food + food_addon_per_child
                ideal_food = child.health.ideal_food_amount()
                fd = temp - ideal_food
                if fd > 0: # если для ребенка слишком много еды, излишки возвращаются в запас
                    child.health.have_food_equal(ideal_food)
                    self.resource += fd
                    s = s + pref + f'ребенок не голоден и возвращает {fd:5.1f} еды в общий котел\n'
                else:
                    child.health.have_food_equal(temp)
                s = s + pref + "ребенок %s| съедает %5.1f\n" % (child.id, child.health.have_food)

            s = s + pref + "Запасы: %6.1f\n" % self.resource
        food_for_old_ones = 0
        # откладываем часть еды для стариков
        if len(self.parents) > 0:
            if self.wife:
                alt_to_old = 1.5 * (self.head.genes.get_trait('altruism') + self.wife.genes.get_trait('altruism'))
            else:
                alt_to_old = 2* self.head.genes.get_trait('altruism')
            food_for_old_ones = self.resource * (alt_to_old - 4)/100
            food_for_old_ones = food_for_old_ones if food_for_old_ones > 0 else 0
            self.resource -= food_for_old_ones
            s = s + pref + "Для стариков откладываем : %5.1f\n" % food_for_old_ones
        # кормим жену
        if self.wife:
            fitness_addon = 0.02 * self.wife.genes.get_trait('strongness')
            altruism_addon = 0.02 * (1.1 * self.wife.genes.get_trait('altruism') - self.husband.genes.get_trait('altruism'))
            wife_food_addon = self.resource * (0.5 + fitness_addon + altruism_addon)
            self.resource -= wife_food_addon
            ideal_food = genetics.FOOD_COEF * genetics.HEDONIC_CONSUME_RATE
            temp = self.wife.health.have_food + wife_food_addon
            fd = temp - ideal_food
            if fd > 0:  # чтобы жена не переедала
                self.wife.health.have_food_equal(ideal_food)
                self.resource += fd
            else:
                self.wife.health.have_food_equal(temp)
            s = s + pref + "Жена берет %5.1f| съедает %5.1f\n" % (wife_food_addon, self.wife.health.have_food)
            s = s + pref + "Запасы: %5.1f\n" % self.resource
        #кормим главу семьи
        ideal_food = genetics.FOOD_COEF * genetics.HEDONIC_CONSUME_RATE
        tf = self.resource
        self.resource = 0
        temp = self.head.health.have_food + tf
        fd = temp - ideal_food
        if fd > 0:  # чтобы жена не переедала
            self.head.health.have_food_equal(ideal_food)
            self.resource = fd
        else:
            self.head.health.have_food_equal(temp)
        s = s + pref + "Глава берет %5.1f| съедает %5.1f\n" % (tf, self.head.health.have_food)
        s = s + pref + "Запасы: %6.1f\n" % self.resource

        #кормим стариков
        if len(self.parents) > 0:
            self.resource = food_for_old_ones
            if self.resource > 0 and  len(self.parents) > 0:
                food_per_parent = self.resource / len(self.parents)
                for i in self.parents:
                    i.health.have_food_change(food_per_parent)
                self.resource = 0

                s = s + pref + "Остатками еды кормим родителей по %5.1f\n" % food_per_parent
        self.family_feeding.write(s)

    def food_display(self, message: str=''):
        pref = "%s|=================%s\n" % (self.id, message)
        self.family_food_file.write(pref)
        pref = "%d:%d| %s|" % (self.head.socium.anno.year, self.head.socium.anno.month, self.id)
        self.budget = 0
        budget_prev = 0
        for i in self.all:
            self.budget += i.health.have_food
            budget_prev += i.health.have_food_prev
            if i is self.head:
                role = "гла"
            elif i is self.wife:
                role = "жен"
            else:
                role = "реб"
            s = pref + " %s| %5.1f| %5.1f| %2d\n" % (role, i.health.have_food, i.health.have_food_prev,
                                                     int(i.health.have_food/genetics.FOOD_COEF) )
            self.family_food_file.write(s)
        b = "Бюждет до %6.1f  после %6.1f \n" % (budget_prev, self.budget)
        self.family_food_file.write(pref + b)


    def del_grown_up_children(self): # проверить, работает ли она вообще
        # убираем повзрослевших иждивенцев
        too_old =[]
        for i in self.dependents:
            if i.age.is_big:
                too_old.append(i)
        if len(too_old) > 0:
            for i in too_old:
                self.dependents.remove(i)
                self.all.remove(i)
                i.family = Family(i)


    def live(self):
        for i in self.all:
            i.live()


    def print_something(self, some):
        some += "\n"
        self.family_log_file.write(some)


    def print_family(self) -> None:
        self.family_log_file.write(self.family_info())


    def family_info(self) -> str:
        strok = f'===========\nСемья: {self.id}\n'
        strok += f'\tГлава:  {self.head.id}| {self.head.name.display()}\n'
        if self.wife:
            strok += f'\tЖена:   {self.wife.id}| {self.wife.name.display()}\n'
        if len(self.dependents)>0:
            strok += f'\tДети:  \n'
            for i in self.dependents:
                strok += f'\t\t{i.id}| {i.name.display()}\n'
        return strok + '\n'





def generate_family_id() -> str:
    ALFABET =('BBCCDDFFGHJKLKLMMNPQRSTPQRRSSTVWXZ', 'AEIAEEIOOUY')
    id = ''
    while  len(id) < 7:
        for l in range(2):
            for sec in range(round(random.random() * .75) + 1):
                id += ALFABET[l][random.randrange(len(ALFABET[l]))]
    return id[:7]
