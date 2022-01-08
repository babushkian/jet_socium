from __future__ import annotations
from typing import Optional, List, Dict, TypeVar, Generic, Union
from dataclasses import dataclass
from enum import Enum


from soc_time import Date, FAR_FUTURE
import human

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
Action = Union[SpouseCause, ParentCause]
'''
@dataclass
class HumanRecCause(Generic[T]):
    person: human.Human
    start: Date
    #cause_type: T
    cause: T
    finish: Date = FAR_FUTURE

'''


@dataclass
class HumanTest:
    person: human.Human
    start: Date
    cause: ParentCause = ParentCause.NONE
    finish: Date = FAR_FUTURE


@dataclass
class HumanTest2(Generic[T]):
    person: human.Human
    start: Date
    cause: T
    finish: Date = FAR_FUTURE

    def __post_init__(self):
        self.cause = self.cause.NONE

class HumanRecCause:
    def __init__(self, hum: int, start:Date, cause: Generic[T], finish: Date = FAR_FUTURE):
        self.human = hum
        self.start = start
        self.finish = finish
        self.cause: T = cause.NONE



start_date = Date(1000, 1, 1)
finish_date = Date(1010, 1, 1)
a = HumanRecCause(1, start_date, SpouseCause.NONE)
b = HumanRecCause(1, start_date, ParentCause.NONE)
print(a.cause)
print('---------------')
a.cause = SpouseCause.DEATH

b.cause = ParentCause.PDEATH
print(a.cause)
print(b.cause)
print(a.cause==b.cause)

print('---------------')
print('---------------')
print('---------------')
c = HumanTest(1, start_date)
print(c)
print(c.cause)

print('---------------')
print('---------------')
print('---------------')
c = HumanTest2(1, start_date, ParentCause)
b = HumanTest2(1, start_date,  SpouseCause)
print(c)
print(c.cause)
print(b.cause)
print(c==b)
print(type(c.cause))
print(type(b.cause))
print(ParentCause.NONE==SpouseCause.NONE)
