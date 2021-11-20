﻿from typing import List, Tuple
from random import choice
import random
import getnames
from common import Gender




class CharName:
    '''
    Определяет ФИО новорожденного ребенка. Меняет фамилию жены при разводе. Меняет фамилию и отчество
    детей у женщины, которая вышла замуж за другого мужчину.
    '''
    family_name: Tuple
    female_name: Tuple
    male_name: Tuple
    second_name_female: Tuple
    second_name_male: Tuple

    def __init__(self, person):
        self.person = person
        self.gender = self.person.gender
        if self.gender is Gender.MALE:
            self.first = choice(CharName.male_name)
            if person.is_human:
                point = CharName.male_name.index(person.father.name.first)
                self.second =  CharName.second_name_male[point]
                self.family_name = person.father.name.family_name
            else:
                self.second = choice(CharName.second_name_male)
                self.family_name = choice(CharName.family_name)

        else:
            self.first = choice(CharName.female_name)
            if person.is_human:
                point = CharName.male_name.index(person.father.name.first)
                self.second =  CharName.second_name_female[point]
                self.family_name = person.father.name.family_name
            else:
                self.second = choice(CharName.second_name_female)
                self.family_name = choice(CharName.family_name)

    def display(self):
        '''
        Возвращает Имя Отчество Фамилию человека
        '''
        gend_index = 1 if self.gender is Gender.MALE else 0
        return f'{self.first} {self.second} {self.family_name[gend_index]}'


    def change_family_name(self, head):
        '''
        При замужестве изменяет фамилию жены и ее детей от предыдущих браков на фамилию мужа.
        Не трогает скрытое свойство tribe_id
        '''
        self.family_name = head.name.family_name

    def change_fathers_name(self, stepfather):
        '''
        Меняет отчество ребенка, если мать вышла замуж за другого мужчину.
        '''
        point = CharName.male_name.index(stepfather.name.first)
        if self.gender is Gender.MALE:
            self.second = CharName.second_name_male[point]
        else:
            self.second = CharName.second_name_female[point]



CharName.family_name = getnames.load_family_names()
CharName.female_name = getnames.load_fem_names()
CharName.male_name, CharName.second_name_female, CharName.second_name_male = getnames.load_male_names()