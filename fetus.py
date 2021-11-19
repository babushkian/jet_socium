from __future__ import annotations
from typing import Tuple, Optional

from common import Gender, apply_gender
import score
from soc_time import Date, ZERO_DATE, TIK, YEAR, FAR_FUTURE
import genetics
import human
import family


class InnocentError(Exception):
	pass

class Fetus:
	'''
	при зачатии мать порождает эмбрион (или несколько), они закреплены за матерью и в общий социум не добавляются
	 для эмбрионов определены: биологические родители, пол и гены
	'''
	def __init__(self, mother: human.Human, gender: Optional[Gender]=None):
		self.score = score.Score()
		self.gender: Gender = apply_gender(gender)
		self.parents = family.Parents(mother.family)
		self.mother: human.Human = mother


		if not isinstance(self.mother.spouse, human.Human):
			raise InnocentError("Произошло непорочное зачатие. Жена без мужа.")
		else:
			self.father: human.Human = mother.spouse # в момент зачатия муж в любом случае есть (это при рождении он может уйти или умереть)
		self.age = ZERO_DATE

		self.genes = genetics.Genes(self)
		self.genes.define()

	def born(self, socium):
		newborn =  human.Human(socium, self.parents, gender=self.gender, age_int=0 )
		self.genes.transit(newborn)
		return newborn


	def parents_in_same_sex_order(self) ->Tuple[human.Human, human.Human]:
		if self.gender is Gender.MALE:
			same_gender = self.parents.father
			opposit_gender = self.parents.mother
		else:
			same_gender = self.parents.father
			opposit_gender = self.parents.mother
		return (same_gender, opposit_gender)

