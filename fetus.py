from __future__ import annotations
from typing import Tuple, Optional

from common import Gender, apply_gender
import score
from soc_time import Date, ZERO_DATE, TIK, YEAR, FAR_FUTURE
import genetics
import human
import family
from causes import BiolParents

class InnocentError(Exception):
	pass

class Fetus:
	'''
	при зачатии мать порождает эмбрион (или несколько), они закреплены за матерью и в общий социум не добавляются
	 для эмбрионов определены: биологические родители, пол и гены
	'''
	def __init__(self, fam: family.Family, gender: Optional[Gender]=None):
		self.score = score.Score()
		self.gender: Gender = apply_gender(gender)
		self.biological_parents = BiolParents(fam)
		if not isinstance(self.biological_parents.father, human.Human):
			raise InnocentError("Произошло непорочное зачатие. Жена без мужа.")
		self.age = ZERO_DATE

		self.genes = genetics.Genes(self)
		self.genes.define()

	def born(self, socium):
		newborn =  human.Human(socium, self.biological_parents, gender=self.gender, age_int=0)
		self.genes.transit(newborn)
		return newborn

