import getnames
import random
from typing import List, Tuple

class CharName:
	family_name: Tuple
	female_name: Tuple
	male_name: Tuple
	second_name_female: Tuple
	second_name_male: Tuple

	def __init__(self, person):
		self.person = person
		self.gender = self.person.gender
		if self.gender:
			self.first = CharName.male_name[random.randrange(len (CharName.male_name))]
			if person.is_human:
				point = CharName.male_name.index(person.father.name.first)
				self.second =  CharName.second_name_male[point]
				self.family = person.father.name.family
			else:
				self.second = CharName.second_name_male[random.randrange(len(CharName.second_name_male))]
				self.family = CharName.family_name[random.randrange(len(CharName.family_name))]

		else:
			self.first = CharName.female_name[random.randrange(len (CharName.female_name))]
			if person.is_human:
				point = CharName.male_name.index(person.father.name.first)
				self.second =  CharName.second_name_female[point]

				self.family = person.father.name.family
			else:
				self.second = CharName.second_name_female[random.randrange(len(CharName.second_name_female))]
				self.family = CharName.family_name[random.randrange(len(CharName.family_name))]

	def display(self):
		'''
		Возвращает Имя Отчество Фамилию
		'''
		return f'{self.first} {self.second} {self.family[self.gender]}'


	def change_family_name(self, head):
		'''
		При замужестве изменяет фамилию жены и ее детей от предыдущих браков на фамилию мужа.
		'''
		self.family = head.name.family

	def change_father(self, stepfather):
		point = CharName.male_name.index(stepfather.name.first)
		if self.gender:
			self.second = CharName.second_name_male[point]
		else:
			self.second = CharName.second_name_female[point]



CharName.family_name = getnames.load_family_names()
CharName.female_name = getnames.load_fem_names()
CharName.male_name, CharName.second_name_female, CharName.second_name_male = getnames.load_male_names()