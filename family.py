from __future__ import annotations
import random
from typing import Optional, List
from enum  import Enum
from common import GET_FOOD_MULTIPLIER, DIGEST_FOOD_MULTIPLIER
import genetics

import human
class FE(Enum):
    MOTHER = 0
    FATHER = 1



'''
вот бы еще сжделать классы Parents и Childern
class Parents
social_parents = Parents(pers1, pers2)
biological_parents = Parents(pers1, pers2)
'''


class Family:
    family_log_file = None
    family_food_file = None
    family_feeding = None

    def __init__(self, head: 'human.Human', depend: Optional[List[human.Human]]=None):  # (человек; список иждивенцев)
        self.obsolete: bool = False
        self.id: str = self.generate_family_id()
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
        self.food = FamilySupplies(self)
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

    @staticmethod
    def generate_family_id() -> str:
        ALFABET = ('BBCCDDFFGHJKLKLMMNPQRSTPQRRSSTVWXZ', 'AEIAEEIOOUY')
        id = ''
        while len(id) < 7:
            for l in range(2):
                for sec in range(round(random.random() * .75) + 1):
                    id += ALFABET[l][random.randrange(len(ALFABET[l]))]
        return id[:7]

    def add_parents(self):
        for i in [self.head.father, self.head.mother]:
            if i is not None:
                if i.is_alive:
                    self.parents.append(i)

    def add_child(self, person: human.Human):
        self.dependents.append(person)
        self.all.append(person)
        person.family = self
        return len(self.dependents)


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


    def get_family_role_sting(self, person:human.Human) -> str:
        if person is self.head:
            s = ' глав'
        elif person is self.wife:
            s = ' жена'
        elif person in self.dependents:
            s = ' чадо'
        else:
            raise Exception('Определение роли человека в семье: неизвестная роль.')
        return s



class FamilySupplies:
    '''
    Формирует и распределяет семейный бюждет
    '''
    def __init__(self, family:Family):
        self.family = family
        self._supplies = 0
        self.budget = 0

    def make(self, food):
        '''полняем семейный бюджет'''
        # возможность переносить запасы на следующий ход пока не делаю
        self._supplies = 0
        for member in self.family.all:
            give = member.health.have_food * genetics.ALTRUISM_COEF * member.genes.get_trait(genetics.GN.ALTRUISM)
            member.health.have_food_change(-give)
            self._supplies += give


    def make_food_supplies(self):

        def form_text_body() ->str:
            s = f'{self.family.get_family_role_sting(member):6s}| {member.id}|'
            s += f' alt={self.family.head.genes.get_trait(genetics.GN.ALTRUISM):2d}| имеет {member.health.have_food_prev:5.1f}| ' \
                 f'вкладывает {give:5.1f}| остается {member.health.have_food:5.1f}\n'
            return s

        pref = f'{self.family.head.socium.anno.year}:{self.family.head.socium.anno.month}| {self.family.id}|'
        s = pref +"-------------\n"
        self._supplies = 0
        for member in self.family.all:
            give = member.health.have_food * genetics.ALTRUISM_COEF * member.genes.get_trait(genetics.GN.ALTRUISM)
            member.health.have_food_change(-give)
            self._supplies += give
            s+= pref + form_text_body()
        s = s + pref + " Всего запас: %6.1f\n" %  self._supplies
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
            egoism_proportion = member.genes.get_trait(genetics.GN.EGOISM) / genetics.Gene.MAX_VALUE
            #part = age_proportion + egoism_proportion
            part = egoism_proportion # отключу слагаемое, отвечающее за возраст, пусть дети получают столько же, сколько и взрослые
            portions[member] = part
            denominator += part
        for member in fam_list:
            portions[member] = portions[member] / denominator
        return portions


    def distribute(self):
        # Новая концепция, попробовать кормить детей так, чтобы у всех детей сытость была на одном уровне примерно
        # а потом о родителях думать
        '''
        Расрелеоение пищи между членами семьи
        Если для одного еды слишком много, оставшаяся от него еда перераспределяется между оставшимися членами семьи
        Если посое всех членов семьи остается еда ...
        '''
        pref = f'{self.family.head.socium.anno.year}:{self.family.head.socium.anno.month}| {self.family.id}|'
        s ='\n'+ pref +"---- питание ---------\n"
        s = s+ pref +"Запасы: %6.1f\n" % self._supplies

        members_list = self.family.all.copy()
        portions = self._calculate_portions(members_list)
        s +=  pref + f'Первонаяальное распределение:\n'
        for member in self.family.all:
            s = s + pref + f'\t{self.family.get_family_role_sting(member):6s}({member.age.year:3d})| {member.id}| {portions[member] * 100:4.1f}% - {self._supplies * portions[member]:5.1f} еды \n'

        # пища, уже отданная из общих запасов кому-то из семьи
        aside = 0
        distributed_food = dict()
        while len(members_list)>0:
            member = members_list.pop()
            s = s + pref + f'{self.family.get_family_role_sting(member):6s}| {member.id}|'
            supplies_share = self._supplies * portions[member] # доля человека из общих запасов
            temp_food = member.health.have_food + supplies_share
            ideal_food = member.health.ideal_food_amount()
            get_food  = min(supplies_share, ideal_food - member.health.have_food)
            member.health.have_food_change(get_food)
            distributed_food[member] = get_food
            aside += get_food
            s += f' доля: {temp_food:5.1f}| идеально: {ideal_food:5.1f}'
            s += f' взято из запасов: {get_food:5.1f}| остаток: {self._supplies-aside:6.1f}|\n'
            if temp_food > ideal_food and len(members_list) > 0:
                # если кто-то не съел свою порцию, обновляем значение запасов и считаем ноаве пропорции исходя из изменившихся запасов
                self._supplies -= aside
                aside = 0
                portions = self._calculate_portions(members_list)
                s = s + pref +  f'\tПЕРЕРАССЧЕТ ({len(members_list)} членов семьи):\n'
                for mem in members_list:
                    s = s + pref + f'\t{self.family.get_family_role_sting(mem)} {portions[mem]:5.3f}\n'
                s += '\n'

        self._supplies -= aside
        # если после распределения еды что-то осталось
        s += f'{self.family.id}| осталось запасов:{self._supplies}\n'
        if self._supplies > 0.01:
            # если есть живые старики, кормим стариков
            if len(self.family.parents) > 0:
                food_per_parent = self._supplies / len(self.family.parents)
                s = s + pref + f'КОРМИМ СТАРИКОВ: {len(self.family.parents)} человека, каждлому по {food_per_parent:5.1f} еды\n'
                for i in self.family.parents:
                    i.health.have_food_change(food_per_parent)
                self._supplies = 0
            else:
                s = s + pref + f'\tРАСПРЕДЕЛЯЕМ ОСТАТКИ: \n'
                # если нет, перераспределяем остатки между членами семьи, не пропадать же еде
                portions = self._calculate_portions(self.family.all)
                for member in self.family.all:
                    s = s + pref + f'\t{self.family.get_family_role_sting(member):6s}| {member.id}| {portions[member]*100:4.1f}% - {self._supplies * portions[member]} еды \n'
                    member.health.have_food_change(self._supplies * portions[member])
                    distributed_food[member] += self._supplies * portions[member]
                self._supplies = 0

        s +=  pref + f'окончательное распределение:\n'
        sum_dist_food = 0
        for member in self.family.all:
            sum_dist_food += distributed_food[member]
        for member in self.family.all:
            persent = distributed_food[member]/sum_dist_food * 100 if sum_dist_food > 0 else 999
            s = s + pref + f'\t{self.family.get_family_role_sting(member):6s}({member.age.year:3d})| {member.id}| {persent:4.1f}% - {distributed_food[member]:5.1f} еды \n'

        self.family.family_feeding.write(s)


    @property
    def suppplies(self):
        return self._supplies

    def change_supplies(self, amount):
        self._supplies += amount

    def family_food_display(self, message: str=''):
        fam_pref = f'{self.family.id}|'
        pref = f'{fam_pref}================={message}\n'
        Family.family_food_file.write(pref)

        pref = f'{self.family.head.socium.anno.year}:{self.family.head.socium.anno.month}| {fam_pref}'
        self.budget = 0
        budget_prev = 0
        for i in self.family.all:
            self.budget += i.health.have_food
            budget_prev += i.health.have_food_prev
            role = self.family.get_family_role_sting(i)
            s = pref + f'{role}| {i.health.have_food:5.1f}| {i.health.have_food_prev:5.1f}| непонятная фигня {int(i.health.have_food/genetics.FOOD_COEF):2d}\n'

            Family.family_food_file.write(s)
        b = "Бюждет до %6.1f  после %6.1f \n" % (budget_prev, self.budget)
        Family.family_food_file.write(pref + b)

