from __future__ import annotations
import random
from typing import List, Dict, NewType, Union, Optional, Tuple
from enum import Enum, auto
import os
import time

from soc_time import ZERO_DATE, Date, TIK

RACES = ['австралийцы', 'арабы', 'атланты', 'галлы', 'германцы', 'гиперборейцы', 'евреи', 'индийцы',
         'инки', 'кавказцы', 'кавказцы', 'латино', 'монголы', 'негры', 'нибиру', 'огнеземельцы',
         'пигмеи', 'полинезийцы', 'славяне', 'франки', 'эскимосы', 'эфиопы']

def init_sim_dir():
    global SIM_DIR
    cur_date = time.time()
    SIM_DIR = 'sim_' + time.strftime("%Y_%m_%d_%H.%M.%S", time.localtime(cur_date)) + f'.{int((cur_date%1)*100//1):02d}'
    try:
        os.mkdir(SIM_DIR)
    except:
        raise Exception('Не удалось создать каталог симуляции')
    os.chdir(SIM_DIR)
    return SIM_DIR


class Gender(str, Enum):
    '''
    Пол человека
    '''
    FEMALE = 'female'
    MALE = 'male'

def opposite_gender(gender:Gender)->Gender:
    return Gender.MALE if gender is Gender.FEMALE else Gender.FEMALE


class Parnt(Enum):
    '''
    Перечисление, содержащее пол родителей.
    '''
    MOTHER = 0
    FATHER = 1

GENDER_LIST = list(Gender)

PARENT_GENDERS = {i:j for i, j in zip(Gender, Parnt)}

def apply_gender(gen: Optional[Gender]) -> Gender:
    if gen is None:
        g = random.choice(GENDER_LIST)
    else:
        g = gen
    return g


class Consume_rate(int, Enum):
    HEDONIC = 10
    RICH = 8
    NORMAL = 6
    POOR = 3
    STARVE = 2


class Stage_of_age(int, Enum):
    BABY = 0
    CHILD = 1
    TEEN = 2
    YOUNG = 3
    ADULT = 4
    AGED = 5
    SENILE = 6

STAGE_LIST =list(Stage_of_age)

STAGE_DICT = {Stage_of_age.BABY: Date(6),
              Stage_of_age.CHILD: Date(12),
              Stage_of_age.TEEN: Date(17),
              Stage_of_age.YOUNG: Date(28),
              Stage_of_age.ADULT: Date(55),
              Stage_of_age.AGED: Date(70),
              Stage_of_age.SENILE: Date(100_000)
              }


# множитель еды для насыщения в зависимости от возраста
'''
На самом деле это не вполне насыщение. Планируется, что это будет коэффициент усвоения пищи
человек может съесть много пищи, но она плохо усвоится, и у человека не будет сил на какие-то действия
а насыщение зависит от размера желудка. У старого человека он не увеличивается. Он будет насыщаться тем же количеством 
пищи, что и молодой. 
вобще-то это у меня уже реализовано, что старик не будет себе брать 1.7 от нормы пищи. Иначе старики никогда бы не 
делилисьпищей, потому что им всегда мало. Просто из-за плохого усвоения у них будет быстрее тратиться жизнь.
 
'''
DIGEST_FOOD_MULTIPLIER = {Stage_of_age.BABY: 0.3,
              Stage_of_age.CHILD: 0.5,
              Stage_of_age.TEEN: 0.7,
              Stage_of_age.YOUNG: 1.0,
              Stage_of_age.ADULT: 1.2,
              Stage_of_age.AGED: 1.4,
              Stage_of_age.SENILE: 1.7
              }
# множитель, сколько еды может добыть человек в зависимости от возраста
GET_FOOD_MULTIPLIER = {Stage_of_age.BABY: 0.0,
              Stage_of_age.CHILD: 0.3,
              Stage_of_age.TEEN: 0.5,
              Stage_of_age.YOUNG: 1.0,
              Stage_of_age.ADULT: 0.9,
              Stage_of_age.AGED: 0.7,
              Stage_of_age.SENILE: 0.5
              }


class Stage:
    """
    Класс показывает возрастную стадию человека и контролирует чтобы стадии своевременно менялись.
    Так же определяет стадию по возрасту.
    """
    def __init__(self,  age_int: int, age: Age):
        self.age = age
        self._stage: Stage_of_age
        self._timer: Date
        self._stage, self._timer = self.get_stage_by_age(age_int)

    def check_stage(self):
        if self.age == self._timer:
            self._stage, self._timer = self.get_next_stage()

    def get_next_stage(self) ->Tuple[Stage_of_age, Date]:
        next_stage: Stage_of_age = STAGE_LIST[self._stage.value + 1]
        # таймер должен перескочить на две стадии
        next_stage_timer: Date = STAGE_DICT[next_stage.value]
        return next_stage, next_stage_timer

    def get_stage_by_age(self, age_int: int) ->Tuple[Stage_of_age, Date]:
        s = Stage_of_age.BABY
        t = ZERO_DATE
        age_date = Date(age_int)
        for stage in STAGE_DICT:
            # возраст наступления следующей стадии
            age_of_next_stage = STAGE_DICT[stage.value]
            if age_date < age_of_next_stage:
                s = stage
                t = age_of_next_stage
                break
        if t == ZERO_DATE:
            raise Exception(f'Ошибка определения фазы возраста у человека {self.age.person.id} {self.age.person}')
        return s, t

    @property
    def value(self):
        return self._stage

    @property
    def name(self):
        return self._stage.name

    @property
    def index(self):
        return self._stage.value

    @property
    def is_big(self):
        return self._stage > Stage_of_age.TEEN

    @property
    def is_fertile_age(self):
        return self._stage in (Stage_of_age.YOUNG, Stage_of_age.ADULT)


    def __str__(self):
        return f'Возрастная стадия {self._stage.name:7s} у человека {self.age.person.id}  возрастом {self.age.display():14s}|{self.age.len():4d} '


class Age(Date):
    def __init__(self, person, age_int=0) : # age_int - число лет ребенка, а не месяцев и дней
        self.person = person
        super(Age, self).__init__(age_int)
        self.birth_date: Date = self.person.socium.anno - self
        self.death_date: Optional[Date] = None
        self._stage = Stage(age_int, self)

    def increase(self):
        self.day += 1
        self._stage.check_stage()

    def display(self):
        self.normalize()
        d = f'{self.year:5d} лет'
        if self.MONTHS_IN_YEAR > 1:
            d += f', {self.month:2d} мес'
        if self.DAYS_IN_MONTH > 1:
            d += f', {self.day:2d} дней'
        return d

    def tech_display(self):
        return self._stage.__str__() + f' next stage time:{self._stage._timer.display():14s}|{self._stage._timer.len():4d}'

    @property
    def stage(self) -> Stage_of_age:
        return self._stage.value


    @property
    def is_big(self):
        return self._stage.is_big

    @property
    def is_fertile_age(self):
        return self._stage.is_fertile_age


if __name__ == '__main__':
    SIM_DIR = init_sim_dir()
    print(SIM_DIR)
    print(os.path.abspath(SIM_DIR))
    f = open('out_file.txt', 'w', encoding='UTF8')
    os.chdir('..')
    a = Stage_of_age.BABY
    timer = ZERO_DATE
    f.write(str(a) + '\n')
    for _  in range(4):
        next_stage = STAGE_LIST[a.value + 1]
        next_stage_timer = STAGE_DICT[next_stage]
        while timer !=next_stage_timer:
            timer += TIK
            f.write(timer.display()+ '\n')
        a = next_stage
        f.write(str(a) + '\n')
    f.close()