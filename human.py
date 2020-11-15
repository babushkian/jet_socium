from __future__ import annotations
import random
import math
from typing import Optional, List, Dict, Tuple, IO, Set, NewType


from names import CharName
import genetics
from common import Stage_of_age, Stage, STAGE_AGES

import prop
import family
from family import FE
import score
from soc_time import Date, ZERO_DATE, TIK, YEAR, FAR_FUTURE
import fetus


# подгоночный коэффициент для беременности, чтобы человек с фертильностью 5
# забеременнил где-то два раза за фертильный возраст
#PREGNANCY_CONST = 0.218 # вроде маловата, надо больше, люди мрут
PREGNANCY_CONST = 0.398


AGE_BABY: Date = Date(0)
AGE_CHILD: Date = Date(3)
AGE_TEEN: Date = Date(13)
AGE_ADULT: Date = Date(18)
AGE_AGED: Date = Date(55)
AGE_SENILE: Date = Date(70)


DIVOCE_CHANSE = 1 / (2 * 20 * Date.DAYS_IN_YEAR) / 20 # вероятность развестись раз в 20 лет, плюс проверяют оба супруга а еще подгоночный коэффициент

FERTIL_RERIOD = (STAGE_AGES[Stage_of_age.AGED] - STAGE_AGES[Stage_of_age.ADULT]).year \
				* Date.DAYS_IN_MONTH * Date.MONTHS_IN_YEAR
PREGNANCY_CHANCE = PREGNANCY_CONST / FERTIL_RERIOD

BirthDate = NewType('BirthDate', Date)
DeathDate = NewType('DeathDate', Date)
MarryDate = NewType('MarryDate', Date)
DivorseDate = NewType('DivorseDate', Date)


class Human:
	GLOBAL_HUMAN_NUMBER: int = 0
	chronicle: IO
	chronicle_stranger_come = '{0}| В социум влился {1}, возраст - {2} лет.'
	chronicle_marriage = '{0}| {1}| свадьба между {2}({3}) и {4}({5})'
	chronicle_pregnacy = '{0}| {1} беременна. Ожидается {2} ребенка.'
	chronicle_born = '{0}| Родился {1}. Мать: |{2}| {3}({4}). Отец: |{5}| {6}({7}).'
	chronicle_divorce = '{0}| {1}| {2}({3}) и {4}({5}) развелись.'
	chronicle_widowed_fem = '{0}| {1} овдовела.'
	chronicle_widowed_mal = '{0}| {1} овдовел.'
	chronicle_died_fem = '{0}| {1} умерла в возрасте {2} лет'
	chronicle_died_mal = '{0}| {1} умер в возрасте {2} лет'
	#DIVORCE_CASES_DICT = {spouse_cause: "по вине супруга", self_cause: "по своей инициативе",
	# spouse_death: "из-за сметри супруга", death: "по причине смерти"}
	# такое ощущение, чт надо два наследственных подкласса сделать Male и Female для простоты обработки ситуаций

	def __init__(self, socium, biol_parents:Tuple[Optional[Human], Optional[Human]], gender: Optional[int]=None, age: int=0):
		Human.GLOBAL_HUMAN_NUMBER += 1
		self.id: str = f'{Human.GLOBAL_HUMAN_NUMBER:07d}'
		self.socium = socium
		self.socium.stat.people_inc()
		if gender is None:
			self.gender = random.randrange(2)
		else:
			self.gender = gender

		self.state: bool = True
		# начальный возраст человека, будет увеличиваться каждый тик
		self.age: Date = Date(age)
		self.age_stage: Stage = Stage(self)

		self.birth_date: BirthDate = self.socium.anno - self.age
		self.death_date: Optional[DeathDate] = None

		self.health: genetics.Health = genetics.Health(self)
		self.score = score.Score()
		self.genes: genetics.Genes = genetics.Genes(self)
		self.tribe_name: str = ''

		self.spouse: Optional[Human] = None  # супруга нет
		# текущий супруг в этот список не входит

		self.marry_dates: Dict[Optional[MarryDate]] = dict()  # для каждого супруга своя дата свадьбы, причем на
		# одном человеке можно жениться несколько раз, бывает и такое
		# в этих словарях дата указывает на объект бывшего супруга
		self.divorce_dates: Dict[Optional[DivorseDate]] = dict()
		self.pregnant: List[Optional[fetus.Fetus]] = list()
		self.children: List[Optional[Human]] = list()


		# родители, которые зачали ребенка
		self.biological_parents: Tuple[Human, Human] = biol_parents

		if self.biological_parents[0] is not None:
			# ребенок родиляся естественным путем
			self.mother: Human = self.biological_parents[0]
			self.father: Human = self.mother.spouse
		else:
			# пришел странник
			self.father: Human = NoneHuman()
			self.mother: Human = NoneHuman()
		self.social_parents: Dict[FE, Human] = {FE.MOTHER: self.mother, FE.FATHER: self.father}

		self.name: CharName = CharName(self)

		# множество близких родственников для определения, на ком можно жениться
		self.close_ancestors: Set[Human] = self.define_close_ancestors()
		if self.mother.is_human:
			self.mother.family.add_child(self)
			self.family: family.Family = self.mother.family
			self.tribe_name = self.mother.tribe_name
			tup = (self.id, self.name.display(), self.mother.id, self.mother.name.display(), self.mother.age.year,
				   self.father.id,	self.father.name.display(), self.father.age.year)
			Human.write_chronicle(Human.chronicle_born.format(*tup))
		else:
			self.family: family.Family = family.Family(self)
			self.genes.define_adult()
			self.tribe_name = self.family.id
			Human.write_chronicle(Human.chronicle_stranger_come.format(self.id, self.name.display(), self.age.year))


	@staticmethod
	def init_files():
		#Human.chronicle = open('./xoutput/chronicle.txt', 'w', encoding='utf16')
		Human.chronicle = open('./chronicle.txt', 'w', encoding='utf16')

	@staticmethod
	def close():
		Human.GLOBAL_HUMAN_NUMBER = 0
		Human.chronicle.close()

	@staticmethod
	def write_chronicle( message):
		Human.chronicle.write(message + '\n')

	@property
	def is_human(parent: Human) -> bool:
		#return not isinstance(parent, NoneHuman)
		return True

	def live(self) -> None:
		self.health.modify() # уменьшается счетчик жизней
		self.age += TIK
		self.age_stage.check_stage()
		is_dead = self.health.is_zero_health
		if is_dead == True:
			self.die() # перс умирает
		if self.is_alive:
			self.score.update(self.score.LIVE_SCORE)
			if self.age_stage.value is Stage_of_age.ADULT:
				# Рожаем детей
				if self.is_married and self.gender == False and self.check_fertil_age() and self.check_fertil_satiety():
					self.check_pregnant()
				# Разводимся
				# шанс развода: 1 на три семьи, если они живут вместе по 40 лет в серднем (два прохода на обоих супругов)

				if self.check_divorce():
					self.divorce()

	def check_divorce(self) -> bool:
		if self.is_married:
			chanse: float = DIVOCE_CHANSE *(1+ (
						self.genes.get_trait('harshness') * self.spouse.genes.get_trait('harshness')
						- self.spouse.genes.get_trait('altruism')/ 4))  # супруг сопротивляется разводу
			return chanse > random.random()
		else:
			return False

	def divorce(self) -> None:
		def divorce_one_spouse(person: Human) -> None:
			person.add_divorce_date()
			person.spouse = None

		spouse = self.spouse
		self.score.update(self.score.DIVORSE_ACTIVE_SCORE)
		spouse.score.update(self.score.DIVORSE_PASSIVE_SCORE)
		tup = (self.id, spouse.id, self.name.display(), self.age.year, spouse.name.display(), spouse.age.year)
		Human.write_chronicle(Human.chronicle_divorce.format(*tup))
		divorce_one_spouse(self)
		divorce_one_spouse(spouse)
		self.family.divide_families()

	# удалять мертвых людей не надо может быть перемещать в какой-то другой список
	def die(self) -> None:
		self.socium.short_death_count +=1
		self.socium.global_death_count +=1
		self.socium.stat.people_dec()  # уменьшаем количество живущих людей
		self.state = False
		self.death_date = self.socium.anno.create()
		if self.gender:
			form = Human.chronicle_died_mal
		else:
			form = Human.chronicle_died_fem
		Human.write_chronicle(form.format(self.id, self.name.display(), self.age.year))
		self.socium.stat.add_to_deadpool(self)
		if self.spouse:
			if self.gender:
				form = Human.chronicle_widowed_fem
			else:
				form = Human.chronicle_widowed_mal
			Human.write_chronicle(form.format(self.spouse.id, self.spouse.name.display()))
			self.add_divorce_date()
			self.spouse.add_divorce_date()
			spouse = self.spouse
			self.spouse = None
			spouse.spouse = None
		self.family.dead_in_family(self)


	def define_close_ancestors(self) -> Set[Human]:
		def get_close_ancestors(person: Human, close_an: set, step: int) -> None:
			if step > 0:
				if person.is_human:
					close_an.add(person.father)
					close_an.add(person.mother)
					get_close_ancestors(person.father, close_an, step-1)
					get_close_ancestors(person.mother, close_an, step-1)
		s = set()
		s.add(self)
		get_close_ancestors(self, s, 2)
		return s

	def get_marry(self, spouse: Optional['Human']) -> None:
		self.spouse = spouse
		self.add_marry_date()
		if self.gender == False:
			self.name.change_family_name(spouse)

	def add_marry_date(self) -> None:
		self.marry_dates[self.socium.anno.create()] = self.spouse

	def add_divorce_date(self) -> None:
		self.divorce_dates[self.socium.anno.create()] = self.spouse

	def give_birth(self) -> None:
		# сделать цикл для двойни, тройни и тд
		while len(self.pregnant) > 0 :
			child = self.pregnant.pop().born(self.socium)
			self.socium.add_human(child)
			self.children.append(child)
			self.spouse.children.append(child)

			self.score.update(self.score.MAKE_CHILD)
			self.spouse.score.update(self.score.MAKE_CHILD)
			# на сколько лет сокращается жизнь в результате родов
			damage = abs(prop.gauss_sigma_2())
			# урон, вызванный привычкой умеренно птиаться (в годах)
			# если женщина неумеренная, наоборот, роды пройдут лучше
			frail_damage =  self.genes.get_trait('strongness') - 5
			# бонус от физической выносливости
			recovery = self.genes.get_trait('strongness') # меньше родовая травма
			total_damage = max(0, damage + frail_damage - recovery)
			# в среднем должен получаться год-два уронм, поэтому делю на 4
			birth_injury = genetics.HEALTH_PER_DAY * Date.DAYS_IN_YEAR * total_damage / 4
			self.health.reduce(birth_injury)


	def check_pregnant(self) -> None:
		if len(self.pregnant) == 0:
			check = PREGNANCY_CHANCE*3*(self.genes.get_trait('fertility') * math.sqrt(self.spouse.genes.get_trait('fertility')) )
			#print(f'{self.socium.anno.display()} {self.id} пл мужа:{self.spouse.genes.get_trait("fertility")} пл жены:{self.genes.get_trait("fertility")} Шанс забеременнеть: {check:>5.3f}')
			if  check > random.random():
				fetus_amount = int(1 +  abs(prop.gauss_sigma_1()) + 1/12 * (self.genes.get_trait('fertility') - 5))
				if fetus_amount < 1:
					fetus_amount = 1
				for num in range(fetus_amount):
					self.pregnant.append(fetus.Fetus(self))
				Human.write_chronicle(Human.chronicle_pregnacy.format(self.id, self.name.display(), fetus_amount))
		else:
			for i in self.pregnant:
				i.age += TIK
			# не важно, сколько детей, берем первого попавшегося ; срок беременности > 3 месяцев, то есть год
			if self.pregnant[0].age > Date(0, 3):
				self.give_birth()

	def check_fertil_age(self) -> bool:
		def count_fertil_age(trait: int) -> Date:
			return Date(0, 0, trait*6) + Date(17, 0, 0)
		fert = False
		if self.age > count_fertil_age(self.genes.get_trait('fert_age')):
			if self.spouse.age > count_fertil_age(self.spouse.genes.get_trait('fert_age')):
				fert = True
		return fert

	def check_fertil_satiety(self) -> bool:
		fert = False
		if self.health.satiety > self.genes.get_trait('fert_satiety') and \
						self.spouse.health.satiety > self.spouse.genes.get_trait('fert_satiety'):
			fert = True
		return fert


	@property
	def adult_and_free(self) -> bool:
		return self.age_stage.value is Stage_of_age.ADULT and  not self.is_married

	@property
	def is_married(self) -> bool:
		return self.spouse is not None

	@property
	def is_alive(self) -> bool:
		return self.state

	def necrolog(self) -> str:
		nec  = "%s| %s | %s \n" % (self.id, self.name.display(), self.family.id)
		nec += "Дата рождения: %s \n" % self.birth_date.display()
		nec += "Дата смерти: %s \n" % self.death_date.display()
		nec += "Возраст смерти: %s\n" % (self.death_date-self.birth_date).display(False)
		nec += "Карма: %d\n" % self.score.score

		def show_genes() -> str:
			g = 'Гены:\n'
			for i in self.genes.GENOTYPE:
				g += '\t%s: %2d' %(i[:6], self.genes.get_trait(i))
				if self.genes.genome[i].predecessor is None:
					sex = 'нет'
				elif self.genes.genome[i].predecessor.gender:
					sex = 'отец'
				else:
					sex = 'мать'
				pv = self.genes.genome[i].pred_value
				delta = self.genes.genome[i].value - pv
				prog = '+' if delta > 0 else '-'
				g += ' (%2d)| %s |%s\n' % (pv, sex, prog * abs(delta))
			return g

		g = show_genes()
		nec = nec +g +"\n"

		nec +="Супруги (%d):\n" % len(self.marry_dates)
		if len(self.marry_dates) > 0:
			sp=""
			# а может они и так упорядочены?
			rec_m = sorted(self.marry_dates.keys(), key=lambda x: x.len()) # список упорядоченных дат женитьбы
			rec_d = sorted(self.divorce_dates.keys(), key=lambda x: x.len())  # список упорядоченных дат развода
			for (dm, dd) in zip(rec_m, rec_d):
				spouse = self.marry_dates[dm]
				delta = dd - dm
				sp += "\t%s| %s | брак - %s\n" % (spouse.id, spouse.name.display(), delta.display(False))
				sp += "\t\tСвадьба: %s\n" % dm.display()
				sp += "\t\tРазвод:  %s" % dd.display()
				ss = "\n"
				if dd == self.death_date:
					ss = " (смерть)\n"
				elif spouse.death_date is None:
						pass
				elif dd == spouse.death_date:
					ss = " (смерть супруга)\n"
				sp +=ss
			nec += sp

			nec +="Дети (%d):\n" % len(self.children)
			if len(self.children)==0:
				sp = "\tнет\n"
			else:
				sp=""
				for child in self.children:
					sp += "\t%s| %s (%s)" % (child.id, child.name.display(), child.birth_date.display())
					if child.father == self:
						other_patent = "(мать:  %s)\n" % child.mother.id
					else:
						other_patent = "(отец:  %s)\n" % child.father.id
					sp += other_patent

		else:
			sp = "\tнет\n"
		nec += sp
		return nec


class NoneHuman(Human):

	def __init__(self):
		self.id: str = 'NoneHuman_id'
		self.gender: int = 1
		self.state: bool = False
		self.name: CharName = CharName(self)

	@property
	def is_human(parent: Human) -> bool:
		#return not isinstance(parent, NoneHuman)
		return False

	def info(self):
		return self.name.display()