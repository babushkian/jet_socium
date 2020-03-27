import random
import math
from typing import Optional, List, Dict

import names
import genetics
import prop
import family
import score
from soc_time import Date, ZERO_DATE, TIK, YEAR, FAR_FUTURE
import fetus


# подгоночный коэффициент для беременности, чтобы человек с фертильностью 5
# забеременнил где-то два раза за фертильный возраст
#PREGNANCY_CONST = 0.218 # вроде маловата, надо больше, люди мрут
PREGNANCY_CONST = 0.398

AGE_BABY = Date(0)
AGE_CHILD = Date(3)
AGE_TEEN = Date(13)
AGE_ADULT = Date(18)
AGE_AGED = Date(55)
AGE_SENILE = Date(70)

DIVOCE_CHANSE = 1/(240*Date.MONTHS_IN_YEAR * Date.DAYS_IN_MONTH)

FERTIL_RERIOD = (AGE_AGED - AGE_ADULT).year * Date.DAYS_IN_MONTH * Date.MONTHS_IN_YEAR
PREGNANCY_CHANCE = PREGNANCY_CONST/FERTIL_RERIOD



class Human:
	GLOBAL_HUMAN_NUMBER = 0
	#DIVORCE_CASES_DICT = {spouse_cause: "по вине супруга", self_cause: "по своей инициативе",
	# spouse_death: "из-за сметри супруга", death: "по причине смерти"}
	# такое ощущение, чт надо два наследственных подкласса сделать Male и Female для простоты обработки ситуаций
	id: str
	gender: Optional[int]
	father: Optional['Human']
	mother: Optional['Human']
	age: Date
	spouse: Optional['Human']
	children: List['Human']
	close_ancestors: List['Human']
	birth_date: Date
	death_date: Optional[Date]
	marry_dates: Dict[Date, 'Human']
	divorce_dates:Dict[Date, 'Human']
	pregnant: List[fetus.Fetus]
	family: family.Family
	def __init__(self, socium, gender: Optional[int]=None, mother: Optional['Human']=None,
				 father: Optional['Human']=None, age: int=0):
		Human.GLOBAL_HUMAN_NUMBER += 1
		self.id = "%07d" % Human.GLOBAL_HUMAN_NUMBER
		self.socium = socium
		self.socium.stat.people_inc()

		if gender is None:
			self.gender = random.randrange(2)
		else:
			self.gender = gender
		# что если ввести список parents в классе Family
		self.father = father
		self.mother = mother
		# множество близких родственников для определения, на ком можно жениться
		# self.close_ancestors = set()
		self.define_close_ancestors()

		self.state = True
		# начальный возраст человека, будет увеличиваться каждый тик
		self.age = Date(age)
		self.birth_date = self.socium.anno - self.age
		self.death_date = None

		self.health = genetics.Health(self)
		self.score = score.Score()
		self.genes = genetics.Genes(self)
		self.tribe_name: str = ''

		self.spouse = None  # супруга нет
		# текущий супруг в этот список не входит
		self.children = []
		self.marry_dates = {}  # для каждого супруга своя дата свадьбы, причем на
		# одном человеке можно жениться несколько раз, бывает и такое
		# в этих словарях дата указывает на объект бывшего супруга
		self.divorce_dates = {}
		self.pregnant = []

		self.name = names.CharName(self, father)
		# формирование семьи
		if self.mother:
			self.mother.family.add_child(self)
		else:
			self.family = family.Family(self)

		if self.mother is None:
			self.genes.define_adult()
			self.tribe_name = self.family.id
			form = "%s| В социум влился %s, возраст - %d лет."
			print(form % (self.id, self.name.display(), self.age.year))
		else:
			self.tribe_name = self.mother.tribe_name
			form = "%s| Родился %s. Мать: |%s| %s(%d). Отец: |%s| %s(%d)."
			print(form % (self.id, self.name.display(), self.mother.id,
							self.mother.name.display(), self.mother.age.year, self.father.id,
							self.father.name.display(), self.father.age.year))



	@staticmethod
	def close():
		Human.GLOBAL_HUMAN_NUMBER = 0

	def live(self) -> None:
		self.health.modify() # уменьшается счетчик жизней
		self.age += TIK
		is_dead = self.health.zero_health()
		if is_dead == True:
			self.die() # перс умирает
		if self.is_alive:
			self.score.update(self.score.LIVE_SCORE)
			if self.is_adult():
				# Рожаем детей
				if self.married() and self.gender == False and self.check_fertil_age() and self.check_fertil_satiety():
					self.check_pregnant()
				# Разводимся
				# шанс развода: 1 на три семьи, если они живут вместе по 40 лет в серднем (два прохода на обоих супругов)

				if self.married():
					chanse = DIVOCE_CHANSE / 4 * (self.genes.get_trait('harshness') * self.spouse.genes.get_trait('harshness')
												  - self.spouse.genes.get_trait('abstinence')) # супруг сопротивляется разводу
					if random.random() < chanse:
						self.score.update(self.score.DIVORSE_ACTIVE_SCORE)
						self.spouse.score.update(self.score.DIVORSE_PASSIVE_SCORE)
						self.make_divorce()


	# удалять мертвых людей не надо может быть перемещать в какой-то другой список
	def die(self) -> None:
		self.socium.short_death_count +=1
		self.socium.global_death_count +=1
		self.socium.stat.people_dec()  # уменьшаем количество живущих людей
		self.state = False
		self.death_date = self.socium.anno.create()
		if self.gender:
			form = "%s| %s умер в возрасте %d лет"
		else:
			form = "%s| %s умерла в возрасте %d лет"
		print(form % (self.id, self.name.display(), self.age.year))
		self.socium.stat.add_to_deadpool(self)
		if self.spouse:
			if self.gender:
				form = "%s| %s овдовела."
			else:
				form = "%s| %s овдовел."
			print(form % (self.spouse.id, self.spouse.name.display()))
			self.add_divorce_date()
			self.spouse.add_divorce_date()
			spouse = self.spouse
			self.spouse = None
			spouse.spouse = None
		self.family.dead_in_family(self)




	def define_close_ancestors(self) -> None:
		def get_close_ancestors(person: 'Human', close_an: set, step: int) -> None:
			if step >0:
				if person.father:
					close_an.add(person.father)
					get_close_ancestors(person.father, close_an, step-1)
				if person.mother:
					close_an.add(person.mother)
					get_close_ancestors(person.mother, close_an, step-1)
		s = set()
		s.add(self)
		get_close_ancestors(self, s, 2)
		self.close_ancestors = s


	def get_marry(self, spouse: Optional['Human']) -> None:
		self.spouse = spouse
		self.add_marry_date()
		if self.gender == False:
			self.name.change_family(spouse)


	def add_marry_date(self) -> None:
		self.marry_dates[self.socium.anno.create()] = self.spouse


	def make_divorce(self) -> None:
		spouse = self.spouse
		print("%s| %s| %s(%d) и %s(%d) развелись." % (self.id, spouse.id, self.name.display(), self.age.year,
													  spouse.name.display(), spouse.age.year))
		self.divorce()
		spouse.divorce()
		self.family.divide_families()


	def	divorce(self) -> None:
		self.add_divorce_date()
		self.spouse = None


	def add_divorce_date(self) -> None:
		self.divorce_dates[self.socium.anno.create()] = self.spouse


	def check_pregnant(self) -> None:
		if len(self.pregnant) == 0:
			check = PREGNANCY_CHANCE*(self.genes.get_trait('fertility') * math.sqrt(self.spouse.genes.get_trait('fertility')) )
			if  check > random.random():
				fetus_num = int(1 +  abs(prop.gauss_sigma_1()) + 1/12 * (self.genes.get_trait('fertility') - 5))
				if fetus_num < 1:
					fetus_num = 1
				for num in range(fetus_num):
					self.pregnant.append(fetus.Fetus(self))
				print("%s| %s беременна. Ожидается %d ребенка." % (self.id, self.name.display(), fetus_num))
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

	def give_birth(self) -> None:
		# сделать цикл для двойни, тройни и тд
		while len(self.pregnant) > 0 :
			child = self.pregnant.pop().born(self.socium)
			self.socium.add_human(child)
			self.children.append(child)
			self.spouse.children.append(child)

			self.score.update(self.score.MAKE_CHILD)
			self.spouse.score.update(self.score.MAKE_CHILD)

			fit_bonus = self.genes.g['fitness'].value * 0.2 # меньше родовая травма
			birth_injury = genetics.HEALTH_PER_DAY * (2 + abs(prop.gauss_sigma_2() - fit_bonus))
			self.health.reduce(birth_injury)


	def adult_and_free(self) -> bool:
		return self.is_alive() and self.is_adult() and  not self.married()

	def married(self) -> bool:
		return self.spouse is not None

	def is_baby(self) -> bool:
		return self.age < AGE_CHILD

	def is_child(self) -> bool:
		condition = False
		if (not self.age < AGE_CHILD) and self.age < AGE_ADULT:
			condition = True
		return condition

	def is_big(self) -> bool:
		return not self.age < AGE_ADULT

	def is_adult(self) -> bool:
		condition = False
		if (not self.age < AGE_ADULT) and self.age < AGE_AGED:
			condition = True
		return condition

	def is_aged(self) -> bool:
		return not self.age < AGE_AGED

	def is_senile(self) -> bool:
		return not self.age < AGE_SENILE

	def is_married(self) -> bool:
		return self.spouse != None

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
				if self.genes.g[i].predecessor is None:
					sex = 'нет'
				elif self.genes.g[i].predecessor.gender:
					sex = 'отец'
				else:
					sex = 'мать'
				pv = self.genes.g[i].pred_value
				delta = self.genes.g[i].value - pv
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