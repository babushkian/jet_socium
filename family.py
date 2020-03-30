import random
from typing import Optional, List
from soc_time import Date
import genetics
import human


ALTRUISM_COEF = .66/12 # при максимальном альтруизме вкадывает в семей. бюдж. 2/3 еды

class Family:

	id: str
	head: Optional['human.Human']
	husband: Optional['human.Human']
	wife: Optional['human.Human']
	dependents: List['human.Human']
	favorite_child: Optional['human.Human']
	favorite_child_timer: Date
	parents: List['human.Human']
	all: List['human.Human']
	def __init__(self, head: 'human.Human', depend: Optional[List['human.Human']]=None):  # (человек; список иждивенцев)
		self.obsolete = False
		self.id = generate_family_id()
		self.head = head
		self.head.socium.families.append(self) # добавляет семью в список семей
		self.husband = None
		self.wife = None
		self.parents = list()
		self.add_parents()
		self.favorite_child = None
		self.favorite_child_timer = self.head.socium.anno + Date(2, 0, 0)  # счетчик на два года
		self.all = [self.head] # все члены семьи кроме стариков, которые и так не члены семьи
		# список детей до 18 лет (не обязательно родных)
		self.dependents = []
		if depend:
			# как обычно, массив детей присвоил, а дперписать детей в другую семью забыл
			#self.dependents = depend
			for i in depend:
				self.add_child(i)

		# временная мера: любимый ребенок в семье. В будущем у каждого родителя будет свой любимчик

		# пищевой ресурс семьи
		self.resource = 0
		s = "Новая семья: %s| %s | %s| возраст - %d лет.\n" % (self.id, self.head.name.display(),
															   self.head.id, self.head.age.year)
		self.family_log_file.write(s)


	@staticmethod
	def init_files():
		Family.family_log_file = open("./xoutput/families.log", "w", encoding="utf16")
		Family.family_food_file = open("./xoutput/family_food_distrib.log", "w", encoding="utf16")
		Family.family_feeding = open("./xoutput/family_feeding.log", "w", encoding="utf16")

	@staticmethod
	def close():
		Family.family_log_file.close()
		Family.family_food_file.close()
		Family.family_feeding.close()

	def add_parents(self):
		for i in [self.head.father, self.head.mother]:
			if i is not None:
				if i.is_alive():
					self.parents.append(i)

	def add_child(self, person):
		self.dependents.append(person)
		self.all.append(person)
		person.family = self
		self.favorite_child = self.get_favorite_child()


	def add_dependents(self, family: 'Family'):
		for i in family.dependents:
			if not i.is_big():
				i.tribe_name = self.head.tribe_name
				# меняем имя и фамилию
				i.name.change_father(self.head)
				i.name.change_family(self.head)
				self.add_child(i)


	def unite_families(self, other: 'Family'):
		# добавляем жену в семью мужа. Семья жены уничтожается
		# объединяем родителей жены и мужа
		# объединяем иждивенцев жены и мужа
		# у жены удаляются родители прежнего мужа
		s = "Объединились семьи:\n"
		s += "\t %s| %s| %s\n" % (self.id, self.head.id, self.head.name.display())
		s += "\t %s| %s| %s\n" % (other.id, other.head.id, other.head.name.display())
		Family.family_log_file.write(s)
		self.wife = other.head
		self.husband = self.head
		self.wife.tribe_name = self.head.tribe_name
		self.all.append(self.wife)
		self.parents.extend(other.parents)
		self.add_dependents(other)
		self.family_disband(other)
		self.wife.family = self


	def divide_families(self):
		"""
		это разводик
		у жены генерится новая семья, дети к совоему отцу перестают иметь отношение
		"""
		s = "=======Семья | %s | распалась\n" % self.id
		s += "\t %s| %s\n" % (self.head.id, self.head.name.display())
		s += "\t %s| %s\n" % (self.wife.id, self.wife.name.display())
		Family.family_log_file.write(s)
		children = self.wife.family.dependents[:] # передаем содержимое, а не объект
		self.wife.family = Family(self.wife, children)
		# мужчина бросает всех иждивенцев на жену
		self.dependents = []
		# родители разделяются на линии жены и мужа
		self.parents = []
		self.add_parents()
		# никто ничей муж и не жена, только главы семьи
		self.husband = None
		self.wife = None
		self.all = [self.head]

	def family_disband(self, family: 'Family'):
		'''
		Уничтожение семьи происходит в двух случаях:
		1) при свадьбе семья жены уничтожается - жена с иждивенцами переходит в семью мужа
		2) при смерти холостого гоавы семьи. Иждивенцы не наслебуют его семью, а создаютс собственные
		'''
		family.obsolete = True
		family.head = None
		family.husband = None
		family.wife = None
		family.all = []
		family.dependents = []

	def dead_in_family(self, person: 'human.Human'):
		if person not in self.dependents:
			if self.wife: # нельзя применять person.married(), так как в person.die супруг уже убран
				self.spouse_dies(person)
			else: # одинок или одинеока
				self.orphane_family()
		else:
			self.child_dies(person)

	def spouse_dies(self, person: 'human.Human'):
		# когда супруг умирает, семья сохраняеися
		# списки родителей и иждивенцев остаются без изменения
		# если умирает супруг, жена становится главой семьи
		if person == self.head:
			s ="\nВ семье |%s|  умер супруг |%s| %s\n"% (self.id, self.head.id, self.head.name.display())
			self.all.remove(self.head)
			self.head = self.wife
			self.husband = None
			self.wife = None
			s += "Теперь |%s| %s глава семьи.\n" % (self.head.id, self.head.name.display())
		else:
			s = "\nВ семье |%s|  умерла супруга |%s| %s\n" % (self.id, self.wife.id, self.wife.name.display())
			self.all.remove(self.wife)
			self.husband = None
			self.wife = None
		Family.family_log_file.write(s)


	def orphane_family(self):
		# если у детей умирают оба родителя, они становятся главами своих собственных семей
		if len(self.dependents) > 0:
			s = "%s| %s из семьи |%s| умер, оставив несовершеннолетних детей.\n" % (self.head.id, self.head.name.display(), self.id)
			for i in self.dependents:
				i.family = Family(i)
		else:
			s = "%s| %s из семьи |%s| умер в одиночестве.\n" % (self.head.id, self.head.name.display(), self.id)
		Family.family_log_file.write(s)
		self.family_disband(self)


	def child_dies(self, person: 'human.Human'):
		self.dependents.remove(person)
		self.all.remove(person)
		if person == self.favorite_child:
			self.favorite_child = self.get_favorite_child()

	def get_favorite_child(self) -> Optional['human.Human']:
		favorite = None
		if self.dependents:
			tail = 0
			child_weights = {}
			for child in self.dependents:
				head = tail
				square = (18 - child.age.year) ** 2
				tail += square  # вероятность стать любимчиком падает по кавдратичному закону
				child_weights[child] = [head, tail]
			# print(f'{child.number} -- {child.age:>2d} -- {square:>4d} -- [{child_weights[child][0]:>5d}:{child_weights[child][1]:>5d}]')
			point = random.randrange(tail)
			# print(f'max : {tail}')
			# print(f'random: {point}')
			for prob in child_weights:
				if point in range(child_weights[prob][0], child_weights[prob][1]):
					favorite = prob
					break
			self.favorite_child_timer = self.head.socium.anno + Date(2, 0, 0) # счетчик на два года
		return favorite

	def make_food_supplies(self):
		'''
		Каждый член семьи откладывает часть добытой еды в общий семейный запас self.resource.
		Доля пищи, переданнойи из личного в семейный бюджет, зависит от  альтруизма человека.
		'''
		pref = "%d:%d| %s|" % (self.head.socium.anno.year, self.head.socium.anno.month, self.id)
		s = pref +"-------------\n"
		# глава семьи создает запасы
		give = self.head.health.have_food * ALTRUISM_COEF * self.head.genes.get_trait('altruism')
		s = s + pref + " Глава alt=%d| имеет %5.1f| вкладывает %5.1f\n" % ( self.head.genes.get_trait('altruism'),
																			self.head.health.have_food, give)
		self.head.health.have_food_change(-give)
		self.resource = give

		# жена создает запасы
		if self.wife:
			give = self.wife.health.have_food * ALTRUISM_COEF * self.wife.genes.get_trait('altruism')
			s = s + pref + " Жена  alt=%d| имеет %5.1f| вкладывает %5.1f\n" % (self.wife.genes.get_trait('altruism'),
																			   self.wife.health.have_food, give)
			self.wife.health.have_food_change(-give)
			self.resource += give
		# дети участвуют в создании запасов
		if len(self.dependents) > 0:
			for i in self.dependents:
				give = i.health.have_food * ALTRUISM_COEF * 0.75 * i.genes.get_trait('altruism') # ребенок пусть поменьше кладет
				s = s + pref + "ребенок %s| имеет %5.1f| вкладывает %5.1f\n" % (i.id, i.health.have_food, give)
				i.health.have_food_change(-give)
				self.resource += give
		s = s + pref + " Всего запас: %6.1f\n" %  self.resource
		self.family_feeding.write(s)

	@staticmethod
	def figth_for_food(first: 'Family', second: 'Family', abundance):
		family_fitnes = []
		for i in (first, second):
			# нельзя чтобы у семейной пары было слишком большое приемущество над одиночками, поэтому параметры жены малось срезаем
			ff = i.wife.genes.get_trait('fitness') / 2 if i.wife else 0
			ff += i.head.genes.get_trait('fitness')
			family_fitnes.append(ff)

		delta = family_fitnes[0] - family_fitnes[1]
		# print("%s| еды: %s | приспособленность: %d" % (first.id, first.resource, family_fitnes[0]))
		# print("%s| еды: %s | приспособленность: %d" % (second.id, second.resource, family_fitnes[1]))
		# print("Дельта: %f\n-------" % delta)
		if delta != 0:
			if delta > 0:
				res = second.resource
			else:
				res = first.resource
			# ОПАСНО, нет проверки на отрицательный общак у терпил
			food_reqisition = res / 15.5 * delta
			pref = "%d:%d|" % (first.head.socium.anno.year, first.head.socium.anno.month)
			s = ""
			for sign, fam in zip((1, -1), (first, second)):
				movement = sign * food_reqisition
				fam.resource += movement
				direct = "семья нашла " if movement > 0 else "семья потеряла "
				s = s + pref + " %s|" % fam.id + direct + "%5.1f\n" % movement
			Family.family_feeding.write(s)

	def food_dist(self):
		# префикс для описания описания питания семей, создающийся каждый цикл
		pref = f'{self.head.socium.anno.year}:{self.head.socium.anno.month}| {self.id}|'
		s = pref +"---- питание ---------\n"
		s = s+ pref +"Запасы: %6.1f\n" % self.resource
		# кормим детей
		if len(self.dependents) > 0:
			dependents_budget = self.resource / 2
			self.resource /= 2
			ideal_food = genetics.RICH_CONSUME_RATE * genetics.FOOD_COEF
			# кормим иждивенцев поровну
			food_addon_per_child = dependents_budget / len(self.dependents)
			s = s + pref + "Кромим %d детей\n" % len(self.dependents)
			s = s + pref + "Каждому выдаем по %5.1f еды\n" % food_addon_per_child
			for i in self.dependents:
				temp = i.health.have_food + food_addon_per_child

				fd = temp - ideal_food
				if fd > 0: # если для ребенка слишком много еды, излишки возвращаются в запас
					i.health.have_food_equal(ideal_food)
					self.resource += fd
				else:
					i.health.have_food_equal(temp)
				s = s + pref + "ребенок %s| съедает %5.1f\n" % (i.id, i.health.have_food)

			s = s + pref + "Запасы: %6.1f\n" % self.resource
		food_for_old_ones = 0
		# откладываем часть еды для стариков
		if len(self.parents) > 0:
			if self.wife:
				alt_to_old = 1.5 * (self.head.genes.get_trait('altruism') + self.wife.genes.get_trait('altruism'))
			else:
				alt_to_old = 2* self.head.genes.get_trait('altruism')
			food_for_old_ones = self.resource * (alt_to_old - 4)/100
			food_for_old_ones = food_for_old_ones if food_for_old_ones > 0 else 0
			self.resource -= food_for_old_ones
			s = s + pref + "Для стариков откладываем : %5.1f\n" % food_for_old_ones
		# кормим жену
		if self.wife:
			fitness_addon = 0.02 * self.wife.genes.get_trait('fitness')
			altruism_addon = 0.02 * (1.1 * self.wife.genes.get_trait('altruism') - self.husband.genes.get_trait('altruism'))
			wife_food_addon = self.resource * (0.5 + fitness_addon + altruism_addon)
			self.resource -= wife_food_addon
			ideal_food = genetics.FOOD_COEF * genetics.HEDONIC_CONSUME_RATE
			temp = self.wife.health.have_food + wife_food_addon
			fd = temp - ideal_food
			if fd > 0:  # чтобы жена не переедала
				self.wife.health.have_food_equal(ideal_food)
				self.resource += fd
			else:
				self.wife.health.have_food_equal(temp)
			s = s + pref + "Жена берет %5.1f| съедает %5.1f\n" % (wife_food_addon, self.wife.health.have_food)
			s = s + pref + "Запасы: %5.1f\n" % self.resource
		#кормим главу семьи
		ideal_food = genetics.FOOD_COEF * genetics.HEDONIC_CONSUME_RATE
		tf = self.resource
		self.resource = 0
		temp = self.head.health.have_food + tf
		fd = temp - ideal_food
		if fd > 0:  # чтобы жена не переедала
			self.head.health.have_food_equal(ideal_food)
			self.resource = fd
		else:
			self.head.health.have_food_equal(temp)
		s = s + pref + "Глава берет %5.1f| съедает %5.1f\n" % (tf, self.head.health.have_food)
		s = s + pref + "Запасы: %6.1f\n" % self.resource

		#кормим стариков
		if len(self.parents) > 0:
			self.resource = food_for_old_ones
			if self.resource > 0 and  len(self.parents) > 0:
				food_per_parent = self.resource / len(self.parents)
				for i in self.parents:
					i.health.have_food_change(food_per_parent)
				self.resource = 0

				s = s + pref + "Остатками еды кормим родителей по %5.1f\n" % food_per_parent
		self.family_feeding.write(s)

	def food_display(self, message=""):
		pref = "%s|=================%s\n" % (self.id, message)
		self.family_food_file.write(pref)
		pref = "%d:%d| %s|" % (self.head.socium.anno.year, self.head.socium.anno.month, self.id)
		self.budget = 0
		budget_prev = 0
		for i in self.all:
			self.budget += i.health.have_food
			budget_prev += i.health.have_food_prev
			if i is self.head:
				role = "гла"
			elif i is self.wife:
				role = "жен"
			else:
				role = "реб"
			s = pref + " %s| %5.1f| %5.1f| %2d\n" % (role, i.health.have_food, i.health.have_food_prev,
													 int(i.health.have_food/genetics.FOOD_COEF) )
			self.family_food_file.write(s)
		b = "Бюждет до %6.1f  после %6.1f \n" % (budget_prev, self.budget)
		self.family_food_file.write(pref + b)


	def del_grown_up_children(self)->bool:
		"""
		убираем повзрослевших иждивенцев
		возвращает True если среди повзрослевших был любимчик
		"""
		grow_up = False
		too_old =[]
		for dep in self.dependents:
			if dep.is_big():
				too_old.append(dep)
		if too_old:
			if self.favorite_child in too_old:
				grow_up = True
			for i in too_old:
				self.dependents.remove(i)
				self.all.remove(i)
				i.family = Family(i)
		return grow_up

	def live(self):
		for i in self.all:
			i.live()

	def update(self):
		grow_up = self.del_grown_up_children()
		if grow_up:
			self.favorite_child = self.get_favorite_child()
		if self.head.socium.anno == self.favorite_child_timer: # любимчики - это временное явление
			self.favorite_child = self.get_favorite_child()
		self.print_family()

	@staticmethod
	def print_something(some):
		some += "\n"
		Family.family_log_file.write(some)


	def print_family(self) -> None:
		Family.family_log_file.write(self.family_info())


	def family_info(self) -> str:
		strok = f'===========\nСемья: {self.id}\n'
		strok += f'\tГлава:  {self.head.id}| {self.head.name.display()}\n'
		if self.wife:
			strok += f'\tЖена:   {self.wife.id}| {self.wife.name.display()}\n'
		if len(self.dependents)>0:
			strok += f'\tДети:  \n'
			for i in self.dependents:
				strok += f'\t\t{i.id}| {i.name.display()}\n'
		return strok + '\n'





def generate_family_id() -> str:
	ALFABET =('BBCCDDFFGHJKLKLMMNPQRSTPQRRSSTVWXZ', 'AEIAEEIOOUY')
	id = ''
	while  len(id) < 7:
		for l in range(2):
			for sec in range(round(random.random() * .75) + 1):
				id += ALFABET[l][random.randrange(len(ALFABET[l]))]
	return id[:7]
