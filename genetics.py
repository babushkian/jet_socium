"""
здесь будут все индивидуальные панраметры человека, влияющие на его поведение

"""
from __future__ import annotations
import random
from typing import List, Dict, NewType, Union, Optional

from soc_time import Date, ZERO_DATE, TIK
import prop

import human
import fetus
import score

Genes_Holder = Union['fetus.Fetus', 'human.Human']

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
# для 4-х дней в году  HEALTH_PER_DAY = 91.25, каждый прожитый день будет отниматься столько

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
		months = random.randrange(2 * Date.MONTHS_IN_YEAR) - Date.MONTHS_IN_YEAR #+- меяцев к жизни
		days = random.randrange(2 * Date.DAYS_IN_MONTH) - Date.DAYS_IN_MONTH #+- дней к жизни
		presume_life += Date(0, months, days)
		self.health = presume_life - age # здоровье - это количество дней до смерти умноженных на коэффициент
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


def generate_genome(genome_len: int)-> List[int]:
	genome = [random.randint(Gene.GENE_MIN_VALUE+2, Gene.GENE_MAX_VALUE-2) for _ in range(genome_len)]
	genome[0] = 9 # ген наследования
	return genome

class Genes:
	gene_profile_0 = (9,  # наследование генов
					5,  # плодовитость
					5,  # проспособленность
					5,  # умеренность
					5,  # неуживчивость
					6,  # альтруизм
					5,  # возраст деторождения
					3,  # сытость, при которой невозможно зачать ребенка
					3)  # вероятность мутации

	GENOTYPE = ('enheritance',  # вероятность наследовать ген от предка своего пола
				'fertility',   # плодовитость
				'strongness',     # приспособленность (лучше добывает пищу)
				'abstinence',  # способность насытится малым
				'harshness',   # склонность к разводам
				'altruism',    # склонность отдавать часть еды родным
				'fert_age',    #  возраст деторождения
				'fert_satiety', # сытость, при которой невозможно зачать ребенка
				'mutation') # вероятность мутации, формула: 1/(mutation + 2)**2
	GEN_PSEUDONYM = {'enheritance':'enhr',
				'fertility': 'fert',
				'strongness': 'fitn',
				'abstinence':'abst',
				'harshness': 'hars',
				'altruism': 'altr',
				'fert_age': 'fage',
				'fert_satiety': 'fsat',
				'mutation': 'muta'}

	def __init__(self, person: Genes_Holder):
		self.person: Genes_Holder = person
		self.genome: Dict[str,Gene] = {i: Gene(i, self) for i in self.GENOTYPE}

	@staticmethod
	# в начале симуляции случайным образом создает шаблон генома для всей популяции
	def init_constants():
		Genes.gene_profile_0 = generate_genome(len(Genes.GENOTYPE))

	def define(self):
		# определяет геном новорожденного
		print(f'Геном по умолчанию: {self.genome}')
		for i in self.genome.values():
			i.init_gene()

	def define_adult(self):
		# применяет шаблон генома популяции для странника
		for i in range(len(self.GENOTYPE)):
			key = self.GENOTYPE[i]
			val = self.gene_profile_0[i]
			self.genome[key].value = val
			self.genome[key].pred_value = val


	def transit(self, person: human.Human):
		# копирует геном в целевого человека
		# это при рождении происходит передача генов от эмбриона  вобъект человека
		for i in self.genome:
			person.genes.genome[i] = self.genome[i]
			#person.genes.genome = self.genome.copy()

	def get_trait(self, trait):
		return self.genome[trait].value


class Gene:
	GENE_MIN_VALUE = 0
	GENE_MAX_VALUE = 11
	def __init__(self, name: str, genome: Genes, value: int=5):
		self.name: str = name
		self.containing_genome: Genes = genome
		self.person: Genes_Holder = genome.person
		self.value: int = value
		self.predecessor: Optional[human.Human] = None

	def init_gene(self):
		# если эмбрион имеет живых рподителей, то гаследуем от родителей
		# если у объекта не тродителей, то это не эмбрион,  а странник, и он получает гены без наследования
		parents = self.person.parents_in_same_sex_order()
		print('=============================')
		print(f'Инициируем ген {self.name}  {self}',  )
		print('у эмбриончика :', type(self.containing_genome.person), self.containing_genome.person)
		print('Его одители:')
		print(self.containing_genome.person.father.is_human, self.containing_genome.person.father)
		print(self.containing_genome.person.mother.is_human, self.containing_genome.person.mother)
		print('Геном, в который входит этот ген: ', self.containing_genome)
		#  ген "наследование" наследуется тольлко от родителя того же пола. От отца к сыну, от матери к дочери.
		# этот ген определяет вероятность того, что другие гены будут копироваться по половой линии
		if self.name == 'enheritance':
			self.inherit_gene(parents[0])
		else: # остальные гены с вероятностью, зависящей от "наследование" могут быть унаследованы от любого из родителей
			self.inherit_any_gene(parents)

		self.pred_value = self.predecessor.genes.get_trait(self.name)
		self.gene_score()


	def inherit_any_gene(self, parents,  default=5):
		# выбираем, от кого из родителей будем наследовать ген

		if random.random() < 1 / (self.person.genes.get_trait('enheritance') + 1) and parents[1] is not None:
			parents = (parents[1], parents[0])  # предков местами, будем наследовать от родителя противоположного пола
		print(f'определяем, что ген наследуется от {parents[0]}')
		self.inherit_gene(parents[0], default)

	def inherit_gene(self, parent,  default=5):
		print( self. name, 'наследуем от предка')
		print(type(parent), parent.is_human, parent)
		self.predecessor = parent
		def trait_limit(trait):
			if trait > Gene.GENE_MAX_VALUE:
				trait = Gene.GENE_MAX_VALUE
			if trait < Gene.GENE_MIN_VALUE:
				trait = Gene.GENE_MIN_VALUE
			return trait
		self.value = trait_limit(self.mutate_gene())

	def mutate_gene(self) -> int:
		shift: float = 0 # величина мутации
		mutation_chance: float = 1 / (self.predecessor.genes.get_trait('mutation') + 2) ** 2 # вероятность мутации
		if mutation_chance > random.random():
			shift = 0.45 * prop.gauss_sigma_1() # величина мутации
			if shift < 0:
				shift -= 1 # если мутация случилась, то ее величина  должна быть больше или меньше единицы,
			if shift >= 0: # иначе пнри округлении эффект мутации равен нулю
				shift += 1
		trait = round(self.predecessor.genes.get_trait(self.name) + shift)
		return trait

	def gene_score(self):
		# очки за изменение генов. Изменения в любую сторону, лишь бы значительные
		gene_delta = abs(self.value - self.pred_value)
		if gene_delta > 0:
			self.person.score.update_gene(gene_delta)


class Gene_Inheritance(Gene):
	def inherit_gene(self, parents, default=5):
		# надо будет переписать особое поведение гена наслеоования
		# и удалить из суперкласса inherit_enheritance
		pass


if __name__ == '__main__':
	# тестирование коэффициента привлекательности (который зависит от возраста)
	for i in range(20):
		x = random.randrange(15, 60)
		attract = lust_coef(x)
		print("%d - %4f" % (x, attract))
