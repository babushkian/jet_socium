"""
здесь будут все индивидуальные панраметры человека, влияющие на его поведение

"""

from soc_time import Date, ZERO_DATE, TIK
import prop
import random
import human
import score

HEDONIC_CONSUME_RATE = 10
RICH_CONSUME_RATE = 8
NORMAL_CONSUME_RATE = 6
POOR_CONSUME_RATE = 3
STARVE_CONSUME_RATE = 2

# у меня 12 градаций бонуса от еды
# переменная FOOD_COEF умножает клдичество еды на 20 лоя того чтобы количество еды более плавно
# менялось и были какие-то промежуточные варианты

FOOD_COEF = 20

# Какой урон или пользу добавляет еда человеку 
# (в качестве индекса должно выптупать количество потребленной еды satiety)
#              0     1   2   3     4    5   6    7    8    9    10  11  12 - на должен достигаться
FOOD_BONUS = [-64, -16, -7, -2, -0.6, -0.2, 0, 0.2, 0.1, -0.4, -1, -4, -16]

YEAR_HEALTH_AMOUNT = 365.0
HEALTH_PER_DAY = YEAR_HEALTH_AMOUNT / (Date.MONTHS_IN_YEAR * Date.DAYS_IN_MONTH)
# для 4-х дней в году  HEALTH_PER_DAY = 91.25

# print("Дней в месяце ", Date.DAYS_IN_MONTH)
# print("Месяцев в году ",Date.MONTHS_IN_YEAR)
# print("Нормальной пищи на год ", YEAR_HEALTH_AMOUNT)
# print("Ежедневный расход здоровья", HEALTH_PER_DAY )


class Health:
	def __init__(self, person, age=ZERO_DATE):
		self.person = person
		# склькл еды удалось достать за ход
		self.have_food = 0
		self.have_food_prev = 0
		# определяем возраст смерти персоны (минимум: 55 - 48; максимум: 55 + 48)
		presume_life = human.AGE_AGED + Date(prop.gauss_sigma_16())
		months = random.randrange(2 * Date.MONTHS_IN_YEAR) - Date.MONTHS_IN_YEAR
		days = random.randrange(2 * Date.DAYS_IN_MONTH) - Date.DAYS_IN_MONTH
		presume_life += Date(0, months, days)
		self.health = presume_life - age
		self.health = HEALTH_PER_DAY * float(self.health.len())  # здоровье это число, а не дата

		self.satiety = 5  # сытость
		self.food_sum = 0

	def have_food_change(self, number):
		"""
		Изменяет количество добытой человектом еды на пареметр number
		:param number: количество еды, на которе нужно изменить переменную  have_food
		"""
		self.have_food_prev = self.have_food
		self.have_food += number
		self.have_food = self.have_food if self.have_food > 0 else 0

	def have_food_equal(self, number):
		"""
		Присваивает человеку количество добытой еды =  number
		"""
		self.have_food_prev = self.have_food
		self.have_food = number
		self.have_food = self.have_food if self.have_food > 0 else 0

	def modify(self):
		"""
		общий метод для изменения здоровья ,в завистмости от множества факторов
		"""
		# уменьшение зроровья просто от прожитых дней
		self.reduce()
		# голод
		abstinence_bonus = 0.3 * (self.person.genes.get_trait('abstinence') - 5)  # чем меньше, тем хуже усваивается еда
		pregnancy_bonus = 0
		fertility_bonus = 0
		if self.person.is_big:
			# за свою половую энергию человек расплачивается жизнью
			# для мужчин трата энергии более выражена
			if self.person.gender:
				fertility_bonus = - 0.2 * (self.person.genes.get_trait('fertility') - 5)
			else:
				fertility_bonus = - 0.07 * (self.person.genes.get_trait('fertility') - 5)
				if self.person.pregnant:
					pregnancy_bonus = -1

		fp = self.person.health.have_food / FOOD_COEF + abstinence_bonus + fertility_bonus + pregnancy_bonus
		self.satiety = int(fp)
		if self.satiety < 0:
			self.satiety = 0
		if self.satiety > 11:
			self.satiety = 11
			fp = 11
		main_health_bonus = FOOD_BONUS[self.satiety]  # целая часть еды
		f_delta = FOOD_BONUS[self.satiety + 1] - FOOD_BONUS[self.satiety]
		additional_health_bonus = f_delta * (fp - self.satiety)  # дробная часть еды вычисленная по линейной пропорции
		self.food_sum = - HEALTH_PER_DAY * (main_health_bonus + additional_health_bonus)
		self.reduce(self.food_sum)

	def reduce(self, amount=HEALTH_PER_DAY):
		self.health = self.health - amount

	def zero_health(self):
		die = False
		if self.health <= 0.0:
			die = True
		return die


def lust_coef(age):
	"""
	с возрастом желание жениться пропадает
	ходошо бы описать это гладкой кривой, но я формулы не знаю
	поэтому будет серия опорных точек
	"""
	lust_checkpoints = [21, 26, 31, 37, 50]  # возраст
	lust_curve = [0.5, 0.6, 0.4, 0.3, 0.2]  # вероятность пожениться (вероятности пары перемннжаются)
	attraction = 0.1
	for i in range(len(lust_checkpoints)):
		if age < lust_checkpoints[i]:
			attraction = lust_curve[i]
			break
	return attraction


class Genes:
	gene_profile_0 = (9, 5, 5, 5, 5, 8)
	gene_profile_1 = (6, 4, 5, 4, 2, 9)
	gene_profile_2 = (10, 9, 9, 5, 6, 6)
	gene_profile_3 = (7, 4, 5, 5, 8, 3) # нежизнеспособный

	GENOTYPE = ('enheritance', # вероятность наследовать ген от предка своего пола
				'fertility',  # плодовитость
				'fitness', # приспособленность (лучше добывает пищу)
				'abstinence', # способность насытится малым
				'harshness', # склонность к разводам
				'altruism') # склонность отдавать часть еды родным

	def __init__(self, person, modifier=0):
		# приспособленность к жизни,параметр ответающиий за добычу пищи
		self.person = person
		self.g = {i: Gene(i, self.person) for i in self.GENOTYPE}

	def define(self):
		for i in self.g.values():
			i.init_gene()

	def define_adult(self):
		for i in range(len(self.GENOTYPE)):
			key = self.GENOTYPE[i]
			val = self.gene_profile_0[i]
			self.g[key].value = val
			self.g[key].pred_value = val


	def transit(self, person):
		for i in self.g:
			person.genes.g[i] = self.g[i]

	def get_trait(self, trait):
		return self.g[trait].value


class Gene:
	def __init__(self, name, person,  value = 5):
		self.name = name
		self.person = person
		self.value = value
		self.predecessor = None

	def init_gene(self):
		if self.person.mother is None:
			parents = (None, None)
		else:
			parents = self.person.get_gender_parents()
		if self.name == 'enheritance':
			self.inherit_enheritance(parents)
		else:
			self.inherit_gene(parents)

		if self.predecessor:
			self.pred_value = self.predecessor.genes.get_trait(self.name)
		else:
			self.pred_value = self.value
		self.gene_score()


	def inherit_enheritance(self, par, num=7):
		trait = None
		for i in  par:
			if i is not None:
				trait = round(i.genes.get_trait('enheritance') + 0.76 * prop.gauss_sigma_1())
				self.predecessor = i
				break
		if trait is None:
			trait = num
		if trait > 11:
			trait = 11
		if trait < 0:
			trait = 0
		self.value = trait


	def inherit_gene(self, parents,  default=5):
		trait = None
		# parents[0] - родитель одного пола с ребенком
		# parents[1] - родитель противоположного с ребенком пола
		if random.random() < 1/ (self.person.genes.get_trait('enheritance') +1) and parents[1] is not None:
			parents = (parents[1], parents[0]) # предков местами, будем наследовать от родителя противоположного пола
		for i in  parents:
			if i is not None:
				self.predecessor = i
				trait = round(i.genes.get_trait(self.name) + 0.76 * prop.gauss_sigma_1())
				break
		if trait is None:
			trait = default
		if trait > 11:
			trait = 11
		if trait < 0:
			trait = 0
		self.value = trait

	def gene_score(self):
		# очки за изменение генов. Изменения в любую сторону, лишь бы значительные
		if self.predecessor is not None:
			gene_delta = abs(self.value - self.pred_value)
			if gene_delta > 0:
				self.person.score.update_gene(gene_delta)



if __name__ == '__main__':
	# тестирование коэффициента привлекательности (который зависит от возраста)
	for i in range(20):
		x = random.randrange(15, 60)
		attract = lust_coef(x)
		print("%d - %4f" % (x, attract))
