from __future__ import annotations
import random
from typing import List, Dict, NewType, Union, Optional, Tuple
from enum import Enum, auto
import os
import time

from soc_time import ZERO_DATE, Date, TIK


def init_sim_dir():
    global SIM_DIR
    cur_date = time.time()
    SIM_DIR = 'sim_' + time.strftime("%Y_%m_%d_%H.%M.%S", time.localtime(cur_date))
    try:
        os.mkdir(SIM_DIR)
    except:
        raise Exception('Не удалось создать каталог симуляции')
    os.chdir(SIM_DIR)
    return SIM_DIR


class Gender(str, Enum):
    MALE = 'male'
    FEMALE = 'female'
    UNKNOWN = 'unknown'

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
    ADULT = 3
    AGED = 4
    SENILE = 5

STAGE_LIST = [i for i in Stage_of_age]

STAGE_DICT = {Stage_of_age.BABY: Date(6),
              Stage_of_age.CHILD: Date(13),
              Stage_of_age.TEEN: Date(18),
              Stage_of_age.ADULT: Date(55),
              Stage_of_age.AGED: Date(70),
              Stage_of_age.SENILE: Date(100_000)
              }


class Stage:
    """
    Класс показывает возрастную стадию человека и контролирует чтобы стадии совевременном енялись.
    Так же поределяет садию по возрасту.
    """
    def __init__(self,  age_int: int, age: Age):
        self.age = age
        self._stage, self._timer = self.get_stage_by_age(age_int)

    def check_stage(self):
        self._stage: Stage_of_age
        self._timer: Date
        if self.age == self._timer:
            self._stage, self._timer = self.get_next_stage()

    def get_next_stage(self) ->Tuple[Stage_of_age, Date]:
        next_stage: Stage_of_age = STAGE_LIST[self._stage.value + 1]
        # таймер должен перескочить на вле стадии
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
        return self._stage in (Stage_of_age.ADULT, Stage_of_age.AGED, Stage_of_age.SENILE)

    def __str__(self):
        return f'Возрастная стадия {self._stage.name} у человека {self.age.person.id}  возрастом {self.age.display()}'


class Age(Date):
    def __init__(self, person, age_int=0) :
        self.person = person
        super(Age, self).__init__(age_int)
        self._stage = Stage(age_int, self)

    def increase(self):
        self.day += 1
        self._stage.check_stage()

    def display(self):
        self.nornalize()
        d = f'{self.year:5d} лет'
        if self.MONTHS_IN_YEAR > 1:
            d += f', {self.month:2d} мес'
        if self.DAYS_IN_MONTH > 1:
            d += f', {self.day:2d} дней'
        return d

    @property
    def stage(self) -> Stage_of_age:
        return self._stage.value


    @property
    def is_big(self):
        return self._stage.is_big



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