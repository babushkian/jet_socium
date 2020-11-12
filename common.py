from __future__ import annotations
import random
from typing import List, Dict, NewType, Union, Optional
from enum import Enum, auto
import os
import time

from soc_time import ZERO_DATE, Date, TIK
HOME_DIR = os.getcwd()
SIM_DIR = os.path.join(HOME_DIR, 'xoutput')

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
    UNDEAD = 6

STAGE_LIST = [i for i in Stage_of_age]

STAGE_AGES = {Stage_of_age.BABY: Date(0),
              Stage_of_age.CHILD: Date(3),
              Stage_of_age.TEEN: Date(13),
              Stage_of_age.ADULT: Date(18),
              Stage_of_age.AGED: Date(55),
              Stage_of_age.SENILE: Date(70),
              Stage_of_age.UNDEAD: Date(100_000) # технический таймер до конца жизни. Надеюсь, человек никогда такого возраста не достигнет
}

class Stage:
    """
    Класс показывает возрастную стадию человека и контролирует чтобы стадии совевременном енялись.
    Так же поределяет садию по возрасту.
    """
    def __init__(self, person):
        self.person = person
        self._stage, self._timer = self.get_stage_by_age(person.age)



    def check_stage(self):
        if self.person.age == self._timer:
            self._stage, self._timer = self.get_next_stage()


    def get_next_stage(self):
        next_stage = STAGE_LIST[self._stage.value + 1]
        next_stage_timer = STAGE_AGES[next_stage]
        return next_stage, next_stage_timer


    def get_stage_by_age(self, age):
        s, t = None, None
        for stage in STAGE_AGES:
            if age == STAGE_AGES[stage] or age < STAGE_AGES[stage]:
                s = stage
                t = STAGE_AGES[STAGE_LIST[stage.value+1]]
                break
        if s is None:
            raise Exception(f'Ошибка определения фазы возраста у человека {self.person.id} {self.person}')
        return s, t

    @property
    def value(self):
        return self._stage

    @property
    def index(self):
        return self._stage.value

    @property
    def is_big(self):
        return self._stage in (Stage_of_age.ADULT, Stage_of_age.AGED, Stage_of_age.SENILE)


    def __str__(self):
        return f'Возрастная стадия {self._stage.name} у человека {self.person}  возрастом {self.person.age}'


