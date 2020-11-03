
import human
from soc_time import Date, ZERO_DATE, TIK, YEAR, FAR_FUTURE
import genetics
import random


class Fetus:
	# при зачатии мать порождает эмбрион (или несколько), они закреплены зв матерью и в общий социум не добавляются
	#  для эмбрионов определены: билолгические родители, пол и гены

	def __init__(self, mother, gender=None):
		if gender == None:
			self.gender = random.randrange(2)
		else:
			self.gender = gender
		self.biol_father = mother.spouce
		self.biol_mother = mother
		self.genes = genetics.Genes(self)
		self.age = ZERO_DATE
		self.genes = genetics.Genes(self)
		self.genes.define()

	def born(self, socium):
		newborn =  human.Human(socium, (self.mother, self.father), gender=self.gender,age=0 )
		self.genes.transit(newborn)
		return newborn

class Child(human.Human):
	pass

class Man(human.Human):
	pass

class Woman(human.Human):
	pass