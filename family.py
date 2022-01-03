from __future__ import annotations
import random
from typing import Optional, List, Dict
from dataclasses import dataclass

from abc import ABC, abstractmethod
from common import ( DIGEST_FOOD_MULTIPLIER,
                    Gender,
                    opposite_gender)
from soc_time import Date, FAR_FUTURE
import human

import genetics


@dataclass
class HumanRec:
    person: human.Human
    start: Date
    finish: Optional[Date] = None


class BiolParents:
    '''
    Биологические родители ребенка. Присваиваются при рождении. Впоследствии не меняются.
    У новоприбывших людей семьи нет, биологические родители это NoneHuman
    Биологические родители не могут быть равны None. Кто-то человека зачинал.
    '''
    def __init__(self, family:Optional[Family]):
        self._parents: Dict[Gender, Optional[human.Human]] = dict()
        if family:
            for parent in [family.wife, family.husband]:
                self._parents[parent.gender] = parent
        else:
            for g in Gender:
                self._parents[g] = human.NoneHuman(g)

    @property
    def mother(self) -> Optional[human.Human]:
        return self._parents[Gender.FEMALE]

    @property
    def father(self) -> Optional[human.Human]:
        return self._parents[Gender.MALE]

    @property
    def lst(self):
        '''
        Возвращает итерируемый объект (список), состоящий из родителей.
        '''
        return [self.mother, self.father]

    def same_gender_parent(self, person:human.Human)-> human.Human:
        return self._parents[person.gender]

    def opposite_gender_parent(self, person:human.Human)-> human.Human:
        return self._parents[opposite_gender(person.gender)]


class SocParents:
    '''
    Социальные родители. У ребенка может смениться множество родителей. Все сони записаны в структуру
    данных. Словарь, в котором лежат два списка родителей: отцов и матерей.
    Если параметр family=None, социальными родителями назначаются два NoneHuman. Но почему не делать
    их равными None, непонятно. Ведь есть же параметр none_soc, который именно так и делает

    '''
    def __init__(self, family:Optional[Family]):
        '''
        Добавляем первых социальных родителей, которых берем из family.
        Вариант когда человек странник обрабатывать не надо. У него нет и никогда уже не будет
        социальных родителей, так как он сам глава семьи.
        '''
        self._parents: Dict[Gender, List[HumanRec]] = {Gender.FEMALE:[], Gender.MALE:[]}
        if family:
            self.assign_parents(family)

    def update(self, family):
        '''
        Обновляем список родителей при следующих изменениях в семье:
        1) Кто-то из родителей умирает
        2) Происходит развод, и отец для детей больше не родитель
        3) происходит свадьба. У детей без одного родителя их снова становится двое.
        4) Ребенок становится отдельной семьей. В силу достижения зрелости  или из-за смерти обоих
        родителей
        '''
        raise NotImplemented('Детям вместо вприсваивания нвогого кшласса родилелей нужно его аптейтить')
        adults = family.adults_dict()
        for g, par in adults.items():
            if self._parents[g] != par:
                self._parents[g].append(HumanRec(par, par.socium.anno.create()))

    def never_parent(self, gender: Gender) -> bool:
        return len(self._parents[gender])==0

    def last_parent(self, gender: Gender) -> Optional[HumanRec]:
        if not self.never_parent(gender):
            return self._parents[gender][-1]

    def current_parent(self, gender: Gender) -> Optional[HumanRec]:
        if not self.never_parent(gender):
            if self._parents[gender][-1].finish is None:
                return self._parents[gender][-1]
        return None

    @property
    def mother(self) -> Optional[human.Human]:
        m = self.current_parent(Gender.FEMALE)
        return m.person if m is not None else None

    @property
    def father(self) -> Optional[human.Human]:
        f = self.current_parent(Gender.MALE)
        return f.person if f is not None else None

    def assign_parent(self, gender, parent: Optional[human.Human]):
        self._parents[gender].append(HumanRec(parent, parent.socium.anno.create()))

    def assign_parents(self, family: Family):
        adults = family.adults_dict()
        for g, par in adults.items():
            if par is not None:
                self.assign_parent(g,par)

    def check_parents_alive(self):
        '''
        Вообще предки сами при своей смерти должны посылать сигналы потомкам, чо они всё

        В данном случае она проверяет, если человек является опекуном, но уже умер, то в записи
        отмечается завершение опеки. Непонятно зачем. И довольно неуклюже. Основной смысл в том,
        чтобы взрослые члены семьи не кормили мертвых стариков. Но у взрослых людей нет социальных
        родителей. А если определять их по последней записи в списке социальных родителей - придется
        постоянно мониторить, живы ли они. Потому что никаких специальных отметок об этом в структуре
        социальных родителей не делается. Разве что действительно, ноны поставить, как концевые
        элементы
        '''
        for g in Gender:
            p = self.current_parent(g)
            if p is not None:
                if p.finish is None and not p.person.is_alive:
                    p.finish = p.person.socium.anno.create()

    @property
    def lst(self):
        '''
        Возвращает итерируемый объект (список), состоящий из родителей. Или None.
        Пока что применение этому списку - кормление стариков. И все будет работать неправильно.
        ТАк как она будет возвращать действующих социальных родителей. А у взрослых людей нет
        социальных родителей, следовательно они никого кормить не будут
        '''
        return [self.mother, self.father]



class SocParentsOld:
    '''
    Социальные родители. У ребенка может смениться множество родителей. Все сони записаны в структуру
    данных. Словарь, в котором лежат два списка родителей: отцов и матерей.
    Если параметр family=None, социальными родителями назначаются два NoneHuman. Но почему не делать
    их равными None, непонятно. Ведь есть же параметр none_soc, который именно так и делает

    '''
    def __init__(self, family:Optional[Family], none_soc = False):
        self._parents: Dict[Gender, Optional[human.Human]] = dict()
        if family:
            self.assign_parents(family)
        else:
            for g in Gender:
                if none_soc: # для странников у них нет социальных родителей
                    self._parents[g] = None
                else:
                    self._parents[g] = human.NoneHuman(g)

    @property
    def mother(self) -> Optional[human.Human]:
        return self._parents[Gender.FEMALE]

    @property
    def father(self) -> Optional[human.Human]:
        return self._parents[Gender.MALE]

    def assign_parents(self, family: Family):
        # у родителей должна быть раскладка по полам. Если жена есть, с полами все понятно.
        # Если жены нет, пол главы семьи может быть любой
        gs = [family.head.gender, opposite_gender(family.head.gender)]
        if family.wife is not None:
            ps = [family.head, family.wife]
        else:
            ps = [family.head, None]

        for gend, par in zip(gs, ps):
            self.assign_parent(gend, par)

    def assign_parent(self, gender, parent: Optional[human.Human]):
        self._parents[gender] = parent


    def check_parents_alive(self):
        for g in Gender:
            if self._parents[g] is not None and not self._parents[g].is_alive:
                self._parents[g] = None

    @property
    def lst(self):
        '''
        Возвращает итерируемый объект (список), состоящий из родителей.
        '''
        return [self.mother, self.father]

    def same_gender_parent(self, person:human.Human)-> human.Human:
        return self._parents[person.gender]

    def opposite_gender_parent(self, person:human.Human)-> human.Human:
        return self._parents[opposite_gender(person.gender)]


class Spouses:
    """
    Содержит список всех супругов с датами женитьбы и развода. Список может быть нулевым. Возвращает
    текущего супруга или None. Так же возвращает последнего по счету супруга, даже если человек в
    разводе или овдовел.
    """
    def __init__(self):
        self._spouses: List[HumanRec] = list()

    @property
    def is_bachelor(self) -> bool:
        '''
        Проверяет, что человек никогда прежде не вступал в брак
        '''
        return self.len() == 0

    @property
    def last_spouse(self)->Optional[human.Human]:
        '''
        Возвращает последнего супруга, с которым был заключен брак, независимо от того, живой он или
        нет, остался в семье или нет. Если человек никогда не вступал в брак, возвращает None.
        '''
        if not self.is_bachelor:
            return self._spouses[-1].person
        return None

    @property
    def spouse(self)-> Optional[human.Human]:
        '''
        Возвращает супруга, с которым человек в данный момент состоит в браке.
        '''
        if not self.is_bachelor:
            if self._spouses[-1].finish is None:
                return self.last_spouse
        return None

    @property
    def is_married(self) -> bool:
        '''
        Состоит ли человек в браке в данный момент
        '''
        return self.spouse is not None

    def marry(self, spouse):
        '''
        Пополняет список супругов и отмечает дату свадьбы.
        '''
        self._spouses.append(HumanRec(spouse, spouse.socium.anno.create()))

    def divorce(self):
        '''
        В запись последнего в списке супруга добавляется дата развода. То есть, он  отмечается как
        бывший.
        Развод еще затрагивает семью. Там обнуляются атрибуты family.husband и family.wife
        '''
        self._spouses[-1].finish = self.spouse.socium.anno.create()

    def len(self) -> int:
        '''
        Возвращает количество супругов
        '''
        return len(self._spouses)

    def display_all_spouses(self, man):
        '''
        Выводит информацию по супругам для некролога.
        '''
        s = f'Супруги ({self.len()}):\n'
        if self.len() > 0:
            for sp in self._spouses:
                delta = sp.finish - sp.start
                name = sp.person.name.display()
                s += f'\t{sp.person.id}| {name}| брак: {delta.display(False)}\n'
                s += f'\t\tСвадьба: {sp.start.display(calendar_date=False, verbose=False)}\n'
                s += f'\t\tРазвод:  {sp.finish.display(calendar_date=False, verbose=False)}'
                # надо следить за тем, чтобы даты смерти не равнялись None, иначе их нельзя будет сравнить
                sdd = sp.person.age.death_date if sp.person.age.death_date is not None else FAR_FUTURE
                mdd = man.age.death_date if man.age.death_date is not None else FAR_FUTURE
                if sp.finish == sdd:
                    s += ' (смерть супруга)\n'
                elif sp.finish == mdd:
                    s += ' (смерть)\n'
                else:
                    s += '\n'
        return s


class Family:
    """
    Поисываеится семья и внутрисемейные отношения. Свадьба развод, смерти супругов, уход из семьи взрослых детей.
    Ну и конечно дележка совместно нажитой пищи.

    Если в семье отдельно выделяется роль главы семьи, то неплохо было бы назначить какую то обязанность,
    характерную только для главы семьи. Которой остальные домочадцы не занимаются.
    """
    family_log_file = None
    family_food_file = None
    family_feeding = None

    def __init__(self, head: human.Human,  # человек
                 depend: Optional[List[human.Human]] = None):  # список иждивенцев
        """
        Создается новая семья. Это происходит в случаях: 1) добавления странника в социум; 2) при разводе;
        3) когда ребенок взрослеет и уходит из семьи; 4) когда у детей умирают все кормильцы
        Если создается семья с дополнительным параметром dependents - это значит жена ушла от мужа с детьми
        (от этого и от предыдущих браков). Мужчина при разводе не забирает с собой детей.
        При объединении семей, жена и дети автоматически меняют свое племя на значение племени главы семьи.
        При разводе жена вспоминает свое изначальное племя tribe_origin - племя последней семьи, в которой
        она воспитывалась. Параметр tribe_origin присваивается только когда ребенок основывает собственную
        семью (когда повзрослеет или осиротеет)
        """
        self.obsolete: bool = False  # признак того, сто семья перестала существовать
        self.id: str = self.generate_family_id()
        # в семье должен быть хотя бы один человек - глава. В начале симуляции все дети получают
        # собственную семью, как и дети-сироты после смерти родителей, как и повзрослевшие дети, покидающие семью
        self.head: human.Human = head
        self.head.socium.families.append(self)  # добавляет семью в список семей
        # если человек холостой, husband  и wife равны None. После свадьбы, этим переменным назначаются конкретные люди
        self.husband: Optional[human.Human] = None
        self.wife: Optional[human.Human] = None
        self.all: List[human.Human] = [self.head]  # все члены семьи кроме стариков, которые и так не члены семьи
        # список детей (не обязательно родных, а пришедших в семью вместе с новым супругом.)
        self.dependents: List[Optional[human.Human]] = list()

        if self.head.biological_parents.mother.is_human:
            self.tribe_id = self.head.family.tribe_id
        else:
            self.tribe_id = self.id
        # при добавлении иждивенцев в семью, они наследуют племя главы семьи
        if depend:
            for i in depend:
                self.add_child(i)
        self.food = FamilySupplies(self)
        s = f'Новая семья: {self.id}| {self.head.name.display()}| {self.head.id}| возраст - {self.head.age.year} лет.\n'
        self.family_log_file.write(s)

    @classmethod
    def init_files(cls):
        cls.family_log_file = open("./families.log", "w", encoding="utf16")
        cls.family_food_file = open("./family_food_distrib.log", "w", encoding="utf16")
        cls.family_feeding = open("./family_feeding.log", "w", encoding="utf16")

    @classmethod
    def close(cls):
        cls.family_log_file.close()
        cls.family_food_file.close()
        cls.family_feeding.close()

    @staticmethod
    def generate_family_id() -> str:
        ALFABET = ('BBCCDDFFGHJKLKLMMNPQRSTPQRRSSTVWXZ', 'AEIAEEIOOUY')
        id = ''
        while len(id) < 7:
            for l in range(2):
                for sec in range(round(random.random() * .75) + 1):
                    id += ALFABET[l][random.randrange(len(ALFABET[l]))]
        return id[:7]

    def adults_dict(self):
        gs = [self.head.gender, opposite_gender(self.head.gender)]
        return {g: a for g, a in zip(gs, [self.head, self.wife])}


    def add_child(self, person: human.Human):
        self.dependents.append(person)
        self.all.append(person)
        person.family = self
        person.social_parents = SocParents(self) # здесь нужно не пересоздавать родителей, а добавляьб новых родителей в список  (social_parents.update)
        return len(self.dependents)


    def add_dependents(self, family: Family):
        '''
        При замужестве добавляем всех детей жены от предыдущего брака в список иждивенцев главы семьи
        Отец их усыновляет.
        '''
        for i in family.dependents:
            if not i.age.is_big:
                i.name.change_fathers_name(self.head) # менем отчество
                i.name.change_family_name(self.head) # меняем фамилию ребенка
                self.add_child(i)


    def unite_families(self, wifes_family: Family):
        '''
        добавляем жену в семью мужа. Семья жены уничтожается
        объединяем иждивенцев жены и мужа в переменную self.dependents
        у жены удаляются родители прежнего мужа
        '''
        s = "Объединились семьи:\n"
        s += "\t %s| %s| %s\n" % (self.id, self.head.id, self.head.name.display())
        s += "\t %s| %s| %s\n" % (wifes_family.id, wifes_family.head.id, wifes_family.head.name.display())
        self.family_log_file.write(s)
        self.wife: human.Human  = wifes_family.head
        self.husband: human.Human  = self.head
        self.wife.name.change_family_name(self.head)  # меняем фамилию жены
        self.all.append(self.wife)
        self.add_dependents(wifes_family)
        self.family_disband(wifes_family)
        self.wife.family = self


    def divide_families(self):
        '''
        происходит развод: разделение на две семьи
        у жены генерится новая семья, дети к своему отцу перестают иметь отношение, переходят в семью матери

        '''
        s = "=======Семья | %s | распалась\n" % self.id
        s += "\t %s| %s\n" % (self.head.id, self.head.name.display())
        s += "\t %s| %s\n" % (self.wife.id, self.wife.name.display())
        self.family_log_file.write(s)
        children = self.dependents[:] # передаем содержимое, а не объект
        self.wife.family = Family(self.wife, children)
        self.wife.family.tribe_id = self.wife.tribe_origin
        # мужчина бросает всех иждивенцев на жену
        self.dependents = []
        # родители разделяются на линии жены и мужа
        # никто ничей муж и не жена, только главы семьи
        self.husband = None
        self.wife = None
        self.all = [self.head]

    def family_disband(self, family: Family):
        '''
        Уничтожение семьи происходит в двух случаях:
        1) при свадьбе семья жены уничтожается - жена с иждивенцами переходит в семью мужа
        2) при смерти холостого главы семьи. Иждивенцы не наследуют его семью, а создают собственные
        '''
        family.obsolete = True
        family.head = None
        family.husband = None
        family.wife = None
        family.all = []
        family.dependents = []

    def dead_in_family(self, person: human.Human):
        '''
        Вызывается, когда в семье кто-то умирает. Не важно, кто: родитель или ребенок. В зависимости
        от тго, кто умер, метод вызывает другие методы. Вызывается из объекта human.Human.
        '''
        if person not in self.dependents:
            # проверяем наличие роли супруга. Если есть wife, то и husband должен быть.
            if self.wife: # нельзя применять person.married(), так как в person.die супруг уже убран
                self.spouse_dies(person)
            else: # человек без пары - семья распадается (дети начинают жить самостоятельно)
                self.orphane_family()
        else:
            self.child_dies(person)

    def spouse_dies(self, person: human.Human):
        '''
        Вызывается, если умирает один из супругов в полной семье. То есть наличие второго супруга
        подразумевается.
        Когда супруг умирает, семья сохраняется
        Списки родителей и иждивенцев остаются без изменения
        Родители умершей жены остаются на попечении вдовца. И наоборот.
        Если умирает супруг, жена становится главой семьи
        '''
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
        for i in self.dependents:
            i.social_parents.check_parents_alive()
        self.family_log_file.write(s)


    def orphane_family(self):
        '''
        Умирает последний (или единственный) взрослый представитель семьи
        если у детей не остается ни одного родителя, они становятся главами своих собственных семей
        '''
        if len(self.dependents) > 0:
            s = "%s| %s из семьи |%s| умер, оставив несовершеннолетних детей.\n" % (self.head.id, self.head.name.display(), self.id)
            for i in self.dependents:
                i.tribe_origin = self.tribe_id
                i.social_parents.check_parents_alive()
                i.family = Family(i)
        else:
            s = "%s| %s из семьи |%s| умер в одиночестве.\n" % (self.head.id, self.head.name.display(), self.id)
        self.family_log_file.write(s)
        self.family_disband(self)


    def child_dies(self, person: human.Human):
        '''
        В семье умирает ребенок
        '''
        self.dependents.remove(person)
        self.all.remove(person)


    def del_grown_up_children(self):
        '''
        Когда ребенок взрослеет, он исключается из состава семьи. Он сам становится новой семьей.
        Вызывается каждый ход в главном цикле объекта socium
        '''
        too_old =[]
        for i in self.dependents:
            if i.age.is_big:
                too_old.append(i)
        if len(too_old) > 0:
            for i in too_old:
                self.dependents.remove(i)
                self.all.remove(i)
                # запоминаем племя, в котором вырос ребенок, так как tribe_id по жизни может меняться
                i.tribe_origin = self.tribe_id
                i.family = Family(i)



    def live(self):
        '''
        Альтернативный метод, двигающий людей по жизни. в отличие от голбального цикла по людям, в
        socium перебираются семьи, а в семье уже перебираются люди.
        К сожалению, этот метод работает некорректно, не знаю, почему.
        '''
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
        '''
        Возвращает роль человека в семье: глава, жена или ребенок
        '''
        if person is self.head:
            s = ' глав'
        elif person is self.wife:
            s = ' жена'
        elif person in self.dependents:
            s = ' чадо'
        else:
            raise Exception('Определение роли человека в семье: неизвестная роль.')
        return s

    def display(self):
        s = '==================================\n'
        s += f'семья:{self.id} племя: {self.tribe_id} статус:{not self.obsolete} \n'
        for nam, person in zip(['head', 'husband', 'wife'], [self.head, self.husband, self.wife]):
            if person is not None:
                s += f'{nam:>7s}: {person.id}| {person.gender.value:6s}| fam:{person.family.id}| orig:{person.tribe_origin}| age: {person.age.display()}\n'
            else:
                s += f'{nam:>7s}: None\n'
        print('---------------------')


        for pers in self.all:
            s += f'{pers.id}| {pers.gender.value:6s}| fam:{pers.family.id}| orig:{pers.tribe_origin}| age: {pers.age.display()}\n'
        return s

class FamilySupplies:
    '''
    Формирует и распределяет семейный бюджет
    '''
    def __init__(self, family:Family):
        self.family = family
        self._supplies = 0.0
        self.budget = 0.0

    def make(self, food):
        '''
        Полняем семейный бюджет.
        Каждый член семьи вкладывает в бюджет долю, пропорциональную его альтруизму. Долю от
        имеющихся у него запасов, полученных после первоначальной добычи пищи
        '''
        # возможность переносить запасы на следующий ход пока не делаю
        self._supplies = 0
        for member in self.family.all:
            # каждый член семьи вкладывает в бюджет долю, пропорциональную его альтруизму
            give = member.health.have_food * genetics.ALTRUISM_COEF * member.genes.get_trait(genetics.GN.ALTRUISM)
            member.health.have_food_change(-give)
            self._supplies += give


    def make_food_supplies(self):
        '''
        Делает то же самое, что и make, по помимо этого пишет в логи кто сколько еды добавил.
        Это неправильный подход, часть с логами надо отделить.
        '''
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
        Считаем распределение еды на всех членов семьи. В какой пропорции нужно поделить еду на
        членов семьи, переданных в переменной fam_list. При распределении еды члены семьи выбывают
        по одному, поэтому функция вызывается несколько раз - пока есть хотя бы один член с
        нераспределенной пайкой.
        '''
        portions = dict()
        denominator = 0
        for member in fam_list:
            # нужно учитывать, что старики плохо уствивают пищу и для насыщения им нужно больше, они будут получать, как взрослые, не бльше 1
            age_proportion = min(DIGEST_FOOD_MULTIPLIER[member.age.stage], 1)
            # опасная штука, если EGOISM==0, может статься, что denominator==0 и деление на ноль, поэтому нужно небольшое смещение
            egoism_proportion = 0.1 + member.genes.get_trait(genetics.GN.EGOISM) / genetics.Gene.MAX_VALUE
            #part = age_proportion + egoism_proportion
            part = egoism_proportion
            portions[member] = part
            denominator += part
        for member in fam_list:
            portions[member] = portions[member] / denominator
        return portions


    def distribute(self):
        # Новая концепция, попробовать кормить детей так, чтобы у всех детей сытость была на одном уровне примерно
        # а потом о родителях думать
        '''
        Распределение пищи между членами семьи
        Если для одного еды слишком много, оставшаяся от него еда перераспределяется между
        оставшимися членами семьи
        Если после всех членов семьи остается еда ...
        '''

        pref = f'{self.family.head.socium.anno.year}:{self.family.head.socium.anno.month}| {self.family.id}|'
        s ='\n'+ pref +"---- питание ---------\n"
        s = s+ pref +"Запасы: %6.1f\n" % self._supplies

        members_list = self.family.all.copy()
        portions = self._calculate_portions(members_list)
        s +=  pref + f'Первоначальное распределение:\n'
        # чтобы не выделять пищу умершим старикам
        for member in self.family.all:
            # почему предки ищутся в family.all. Если нужно смотреть только у взрослых членов семьи
            # разве что на всякий случае, если кто из родителей умрёт
            member.social_parents.check_parents_alive()
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
            family_parents = [] # тут должен быть set, чтобы случайно один родственник не пролез два раза в сучае кровосмесительного брака
            for member in [self.family.head,self.family.wife]:
                if member is not None:
                    for p in member.social_parents.lst:
                        if p is not None:
                            raise NotImplemented('Переделать кормление стариков, так как  они не обязательно None, а последние элементы в списке родителей')
                            family_parents.append(p)

            if len(family_parents) > 0:
                food_per_parent = self._supplies / len(family_parents)
                s = s + pref + f'КОРМИМ СТАРИКОВ: {len(family_parents)} человека, каждлому по {food_per_parent:5.1f} еды\n'
                for i in family_parents:
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

