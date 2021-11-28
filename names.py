from typing import Dict, Tuple
from random import choice
import getnames
from common import Gender


class CharName:
    '''
    Определяет ФИО новорожденного ребенка. Меняет фамилию жены при разводе. Меняет фамилию и отчество
    детей у женщины, которая вышла замуж за другого мужчину.
    Если человек NoneHuman, имя генерится случайно.
    Если человек  из первого поколения, фамилия и отчество берутся от биологического отца NoneHuman.
    Если человек произошел от настоящих родителей, фамилия и отчество берутся от последнего супруга
    матери. То есть фамилия отчество берутся от социального отца. Биологический может умереть на
    момент рождения. А мать к тому времени женится на другом. У меня отчество не является признанием
    родства. Биологические дети (Human.children) отделены от социальных (Family.dependents).
    '''
    family_name: Tuple[Dict[Gender, str]]
    first_name: Dict[str, Dict[Gender, str]]
    second_name:Dict[Gender, Tuple[str]]

    def __init__(self, person):
        self.gender = person.gender
        def gen_nohuman_name(gender):
            family_n = choice(CharName.family_name)
            first = choice(CharName.first_name[gender])
            second = CharName.second_name[choice(CharName.first_name[Gender.MALE])][gender]
            return (family_n, first, second)

        if person.is_human:
            if person.biological_parents.mother.is_human:
                father = person.biological_parents.mother.spouses.last_spouse
            else:
                father = person.biological_parents.father

            self.first = choice(CharName.first_name[self.gender])
            self.second =  CharName.second_name[father.name.first][self.gender]
            self.family_name = father.name.family_name
        else:
            self.family_name, self.first, self.second = gen_nohuman_name(self.gender)

    def display(self):
        '''
        Возвращает Имя Отчество Фамилию человека
        '''
        return f'{self.first} {self.second} {self.family_name[self.gender]}'


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
        self.second = CharName.second_name[stepfather.name.first][self.gender]



CharName.family_name = getnames.load_family_names()
CharName.second_name = getnames.load_second_names()
male_names = tuple(CharName.second_name)
female_names = getnames.load_fem_names()
CharName.first_name = {Gender.FEMALE:female_names, Gender.MALE:male_names}
