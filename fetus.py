from __future__ import annotations
from typing import Tuple, Optional
import random


import score
from soc_time import Date, ZERO_DATE, TIK, YEAR, FAR_FUTURE
import genetics
import human
#from human import Human



class Fetus:
	# при зачатии мать порождает эмбрион (или несколько), они закреплены за матерью и в общий социум не добавляются
	#  для эмбрионов определены: билолгические родители, пол и гены

	def __init__(self, mother: human.Human, gender: Optional[int]=None):
		print('Пошло дело')
		self.score = score.Score()
		if gender == None:
			self.gender: int = random.randrange(2)
		else:
			self.gender: int = gender
		self.father: human.Human = mother.spouse # в момент зачатия муж в любом сдучае есть
		self.mother: human.Human = mother
		self.age = ZERO_DATE
		self.genes = genetics.Genes(self)
		self.genes.define()

	def born(self, socium):
		print('Я родився')
		if self.mother.is_married:
			father = self.mother.spouse
		else:
			father = self.father
		newborn =  human.Human(socium, self.gender, self.mother, father, age=0 )
		self.genes.transit(newborn)
		return newborn

	def parents_in_same_sex_order(self) ->Tuple[human.Human, human.Human]:
		# возвращает пару родителей, сначал  одноименный пол, затем противоположный
		same_gender = None
		opposit_gender = None
		def get_father() -> human.Human:
			if self.mother.is_married:
				father = self.mother.spouse
			else:
				father = sorted(self.mother.divorce_dates.keys(), key = lambda x: x.len())[-1]
			return father
		if self.mother:
			if self.gender:
				same_gender = get_father()
				opposit_gender = self.mother
			else:
				same_gender = self.mother
				opposit_gender = get_father()

		return (same_gender, opposit_gender)

