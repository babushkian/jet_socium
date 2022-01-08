from __future__ import annotations
from typing import Optional, List, Dict, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum

import human
from common import (Gender,
                    opposite_gender)

from soc_time import Date, FAR_FUTURE
from family import Family


class SpouseCause(str, Enum):
    NONE = ''
    DIVORCE = 'развод'
    DEATH = 'смерть'
    SDEATH = 'смерть супруга'

class ParentCause(str, Enum):
    NONE = ''
    GROW_UP = 'совершеннолетие'
    DIVORCE = 'развод'
    DEATH = 'смерть'
    PDEATH = 'смерть родителя'

T= TypeVar('T')

@dataclass
class HumanRecCause(Generic[T]):
    person: human.Human
    cause: T
    start: Date= FAR_FUTURE
    finish: Date = FAR_FUTURE

    def __post_init__(self):
        self.cause = self.cause.NONE
        self.start = self.person.socium.anno.create()

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
    Если параметр family=None, то список социальных родителей у человека пуст и в дальнейшем не меняется,
    так как такой человек изначально является главой семьи
    Метод init вызывается при рождении ребенка. В дальнейшем все его семейные изменения уточняются
    методом update.
    '''
    def __init__(self):
        '''
        Социальные родители добавятся при инициализации объекта Human
        '''
        self._parents: Dict[Gender, List[HumanRecCause]] = {Gender.FEMALE:[], Gender.MALE:[]}


    def never_parent(self, gender: Gender) -> bool:
        return len(self._parents[gender])==0

    def last_parent(self, gender: Gender) -> Optional[HumanRecCause]:
        if not self.never_parent(gender):
            return self._parents[gender][-1]
        else:
            return None

    def current_parent(self, gender: Gender) -> Optional[HumanRecCause]:
        if not self.never_parent(gender):
            if self.last_parent(gender).finish == FAR_FUTURE:
                return self.last_parent(gender)
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
        '''
        Добавляет непустого родителя в список родителей указанного пола
        '''
        if parent is not None:
            self._parents[gender].append(HumanRecCause(parent, ParentCause))

    def finish_parentship(self, parent: HumanRecCause, cause:ParentCause):
        parent.finish = parent.person.socium.anno.create()
        parent.cause = cause


    def update(self, family):
        '''
        Обновляем список родителей при следующих изменениях в семье:
        1) Кто-то из родителей умирает
        2) Происходит развод, и отец для детей больше не родитель
        3) происходит свадьба. У детей без одного родителя их снова становится двое.
        4) Ребенок становится отдельной семьей. В силу достижения зрелости  или из-за смерти обоих
        родителей
        '''
        adults: Dict[Gender, Optional[human.Human]] = family.adults_dict()
        for g, par in adults.items():
            if self.never_parent(g):
                self.assign_parent(g, par)
            else:
                # добавляем родителя только если он отличается от предыдущего
                # или у того же родителя  был разрыв в родительстве
                last = self.last_parent(g) # предыдущий ненулевой родитель должен быть если этот if выполнился

                if last.person == par: # если это тот же родитель, что и прошлый
                    if last.finish != FAR_FUTURE: # если родительство прерывалось, записываем как очередного родителя
                        self.assign_parent(g, par)
                elif par is None: # новый родитель отсутствует (None) (произошел развод)
                    if last.finish == FAR_FUTURE: # завершаем родительство предыдущего родителя
                        self.finish_parentship(last, ParentCause.DIVORCE)
                    else:
                        raise NotImplemented('Второй раз применяется None к родителю')
                else: # другой родитель
                    if last.finish == FAR_FUTURE: # прошлое родительство не закончилось, но началось новое
                        raise NotImplemented('прошлое родительство не закончилось, но началось новое')
                    else: # прошлый родитель уже не родитель, применяем нового
                        self.assign_parent(g, par)


    def finish_parents_death(self,):
        '''
        Родительство завершается, если у родителей умирает ребенок.
        '''
        for g in Gender:
            par = self.current_parent(g)
            if par:
                self.finish_parentship(par, ParentCause.DEATH)

    def finish_parents_grow_up(self):
        '''
        Вызывается, когда ребенок взрослеет и уходит из семьи. У родителей ставятся даты завершения опекунства.
        '''
        for g in Gender:
            par = self.current_parent(g)
            if par:
                self.finish_parentship(par, ParentCause.GROW_UP)


    def check_parents_alive(self):
        '''
        Вызывается из методов смерти родителей в семье. Завершается родительсвто мертвых родителей.
        В данном случае она проверяет, если человек является опекуном, но уже умер, то в записи
        отмечается завершение опеки.
        У странника никогда не будет вызвано ,потому что у него нет социальных родителей.

        Но нужно еще рассматривать тот вариант, когда у взрослых детей уже нет социальных родителей.
        Чтобы взрослые члены семьи не кормили мертвых стариков. Но у взрослых людей нет социальных
        родителей. А если определять их по последней записи в списке социальных родителей - придется
        постоянно мониторить, живы ли они. Потому что никаких специальных отметок об этом в структуре
        социальных родителей не делается. Разве что действительно, ноны поставить, как концевые
        элементы
        '''
        for g in Gender:
            p = self.current_parent(g)
            if p is not None:
                if p.finish == FAR_FUTURE and not p.person.is_alive:
                    self.finish_parentship(p, ParentCause.PDEATH)


    @property
    def lst(self):
        '''
        Возвращает итерируемый объект (список), состоящий из родителей. Или None.
        Пока что применение этому списку - кормление стариков. И все будет работать неправильно.
        ТАк как она будет возвращать действующих социальных родителей. А у взрослых людей нет
        социальных родителей, следовательно они никого кормить не будут
        '''
        return [self.mother, self.father]

    def display(self):
        s = 'Социальные родители:\n'
        for status, gender in zip(['Мать', 'Отец'], Gender):
            if self.never_parent(gender):
                s += f'\t{status}: Неизвестно\n'
            else:
                s += f'\t{status}({len(self._parents[gender])}):\n'
                for parent in self._parents[gender]:
                    pp = parent.person
                    ps = f'\t{" "*6}{pp.id} |{pp.name.display()}| племя: {pp.tribe_origin}|'
                    time = f'{parent.start.display(calendar_date=False, verbose=False)} -' \
                           f'{parent.finish.display(calendar_date=False, verbose=False)}| '
                    cause = f'{parent.cause.value}\n'
                    s+= ps + time+ cause

        return s

class Spouses:
    '''
    Содержит список всех супругов с датами женитьбы и развода. Список может быть нулевым. Возвращает
    текущего супруга или None. Так же возвращает последнего по счету супруга, даже если человек в
    разводе или овдовел.
    '''
    def __init__(self):
        self._spouses: List[HumanRecCause] = list()

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
            if self._spouses[-1].finish == FAR_FUTURE:
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
        self._spouses.append(HumanRecCause(spouse, SpouseCause))

    def divorce(self, cause:SpouseCause):
        '''
        В запись последнего в списке супруга добавляется дата развода. То есть, он  отмечается как
        бывший.
        Развод еще затрагивает семью. Там обнуляются атрибуты family.husband и family.wife
        '''
        self._spouses[-1].finish = self.spouse.socium.anno.create()
        self._spouses[-1].cause = cause

    def len(self) -> int:
        '''
        Возвращает количество супругов
        '''
        return len(self._spouses)

    def display(self, man):
        '''
        Выводит информацию по супругам для некролога.
        '''
        s = f'Супруги ({self.len()}):\n'
        if self.len() > 0:
            for sp in self._spouses:
                delta = sp.finish - sp.start
                name = sp.person.name.display()
                s += f'\t{sp.person.id}| {name}|'
                s += f'{sp.start.display(calendar_date=False, verbose=False)} -'
                s += f'{sp.finish.display(calendar_date=False, verbose=False)}|'
                s += f'{delta.display(False)}|'
                s += f' ({sp.cause.value})\n'
        return s

    def display_all_spouses_old(self, man):
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

