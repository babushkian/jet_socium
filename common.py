from __future__ import annotations
import random
from typing import List, Dict, NewType, Union, Optional
from enum import Enum, auto
from soc_time import ZERO_DATE, Date, TIK

class Gender(Enum):
    MALE = auto()
    FEMALE = auto()
    UNKNOWN = auto()

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

if __name__ == '__main__':
    a = Stage_of_age.BABY
    timer = ZERO_DATE
    print(a)
    for _  in range(4):
        next_stage = STAGE_LIST[a.value + 1]
        next_stage_timer = STAGE_AGES[next_stage]
        while timer !=next_stage_timer:
            timer +=TIK
            print(timer.display())
        a = next_stage
        print(a)
