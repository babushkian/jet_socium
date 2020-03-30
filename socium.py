import random

from soc_time import Date, Anno
from family import Family
from human import Human
import statistics
import genetics
import score
import soc_roles



class Socium:
	ESTIMAED_NUMBER_OF_PEOPLE = None
	FOOD_RESOURCE = None

	def __init__(self, anno=1000):
		# список всех людей в социуме, на данный помент вклюяая мертвых(проверить)
		Socium.class_var_init()
		Human.init_files()
		Family.init_files()
		self.soc_list = []
		self.families = []
		
		self.stat = statistics.Soc_stat(self)
		# текущий год
		self.anno = Anno(anno)
		# локальный счетчик смертей, после появления чужака обнуляется
		self.short_death_count = 0
		# общий счетчик смертей
		self.global_death_count = 0
		# давно умершие родственники (чтобы зря не крутить большие циклы)
		self.forgotten = []

	@staticmethod
	def class_var_init():
		Socium.ESTIMAED_NUMBER_OF_PEOPLE = 6000 # предполагаемое количество людей
		# общее клоичестов пищи за ход, которое люди делят между собой
		Socium.FOOD_RESOURCE = genetics.FOOD_COEF * genetics.NORMAL_CONSUME_RATE * Socium.ESTIMAED_NUMBER_OF_PEOPLE
		Socium.feeding_log = open("./xoutput/global_food_distribution.log", "w", encoding="utf16")

	def close(self):
		self.__class__.class_var_init()
		self.feeding_log.close()
		Human.close()
		family.Family.close()

	def add_human(self, human):
		self.soc_list.append(human)
	
	def remove_human(self, human):
		self.soc_list.remove(human)
	
	def clear_people_alive(self):
		self.people_alive = [] #живые люди

	def people_alive_add(self, person):
		self.people_alive.append(person)

	def forgot_ancestors(self):
		temp = []
		self.forgotten = []
		for person in self.soc_list:
			if not person.is_alive() and self.anno - person.death_date > Date(40):
				self.forgotten.append(person)
			else:
				temp.append(person)
		self.soc_list = temp
		self.hall_of_fame(self.forgotten)

	def reduce_food_resource(self):
		if self.anno.year > 2400 and self.anno.year < 2700:
			#Socium.ESTIMAED_NUMBER_OF_PEOPLE -=1
			#Socium.FOOD_RESOURCE =Socium.FOOD_RESOURCE - (0.03*genetics.NORMAL_CONSUME_RATE* Socium.ESTIMAED_NUMBER_OF_PEOPLE)
			#Socium.FOOD_RESOURCE = int(0.995 * Socium.FOOD_RESOURCE )
			pass
		if self.anno.year > 3000 and self.anno.year <3300:
			#Socium.ESTIMAED_NUMBER_OF_PEOPLE -=1
			#Socium.FOOD_RESOURCE =Socium.FOOD_RESOURCE - (0.03*genetics.NORMAL_CONSUME_RATE* Socium.ESTIMAED_NUMBER_OF_PEOPLE)
			#Socium.FOOD_RESOURCE = int(1.002 * Socium.FOOD_RESOURCE )
			pass


	def tictac(self):
		def families_list_update():
			temp = []
			for fam in self.families:
				if not fam.obsolete:
					temp.append(fam)
			self.families = temp

		self.anno.time_pass()
		# уменьшаем количество пищи
		if self.anno.year_starts() and self.anno.year % 4 == 0:
			pass
			#self.reduce_food_resource()

		# чистим социум от давно умерших людей
		if self.anno.year_starts() and self.anno.year % 40 == 0: # раз в 40 лет
			self.forgot_ancestors()

		# первичное распределение еды. Потом еда распределяется внутри семьи, а потом каждый употребляет еду индивидуально
		self.food_distribution()

		# женим холостых людей
		self.search_spouce()
		# проверяем семьи # в результате свадеб часть семей могла устареть
		families_list_update()

		# каждый человек делает свои индивидуальные дела: ест, рожает детей, умирает
		for person  in self.people_alive:
			person.live()

		#----------------------------------------------
		# вот он метод, из-за которого у меня основные проблемы. Он енправильно обрабатывает семьи
		# семьи трудный, постоянно меняющийся объект, в отличии от людей. Когда перебираешь людей,
		#  социум рзвивается стабильно. Когда обрабатываешь семьи - все вымирают
		#---------------------------------------------
		'''
		for fam in self.families:
			fam.live()
		# проверяем семьи # в результате смерти главы семьи, часть семей могла устареть
		'''
		families_list_update()

		# добавляем странника именно в это место, потому что список живых людей еще не модифицирован
		# и участвовать в общественной жизни страннику нельзя
		if self.anno.year_starts():
			if self.anno.year < 1200:
				self.stranger_comes_to_socium()

		Family.print_something("\n==============================\n"+ self.anno.display())
		Family.print_something("Количество семей: %d" % len(self.families))
		for fam in self.families:
				fam.update()
		# подсчет статистики социума
		self.stat.count_soc_state()
		self.stat.get_families_in_socium()


		# считается, как изменяются средние значения генов (каждый год считать не обязательно)
		if self.anno.year_starts() and self.anno.year % 4 ==0: 
			self.stat.count_genes_average()


	def	search_spouce(self):
		def success_marry_chanse(person1, person2):
			attraction = (genetics.lust_coef(person1.age.year) *
				genetics.lust_coef(person2.age.year))
			return attraction >= random.random()
		# если есть возможность создать хоть одну пару
		if min(self.stat.unmarried_adult_men_number, self.stat.unmarried_adult_women_number) > 0:
			s = f'Холостых мужчин: {self.stat.unmarried_adult_men_number}\nХолостых женщин: {self.stat.unmarried_adult_women_number}'
			Human.write_chronicle(s)
			if self.stat.unmarried_adult_men_number < self.stat.unmarried_adult_women_number:
				a = self.stat.unmarried_adult_men
				b = self.stat.unmarried_adult_women
			else:
				b = self.stat.unmarried_adult_men
				a = self.stat.unmarried_adult_women
			random.shuffle(b)
			# за один раз можно попытать счастья только с одним избранниким
			# цикл идет по представителям пола, который сейчас в меньшинстве
			for person in a:
				if person.close_ancestors.isdisjoint(b[-1].close_ancestors): # ксли не являются близкими родственниками
					if success_marry_chanse(person, b[-1]):
						tup = (person.id, b[-1].id, person.name.display(), person.age.year, b[-1].name.display(), b[-1].age.year)
						Human.write_chronicle(Human.chronicle_marriage.format(*tup))
						person.get_marry(b[-1])
						b[-1].get_marry(person)
						person.score.update(person.score.MARRY_SCORE)
						b[-1].score.update(b[-1].score.MARRY_SCORE)
						if person.gender:
							person.family.unite_families(b[-1].family)
						else:
							b[-1].family.unite_families(person.family)
					b.pop() # человек удаляется из списка кандидатов в супруги независтмо от того, заключил он брак или нет



	def food_distribution(self):
		# флаг изобилия. Когда изобилие, люди не отбирают еду у других людей, 
		# просто берут из природных резервов
		# сюда склажываются излищки еды, образовавшиеся при первоначальном прспределении, потом наспределятся повторно
		food_waste = 0
		# abundance - изобилие, при отором не должна происходить конкуренция между семьями за еду
		abundance = False
		# первоначальное распределение еды
		food_per_man = Socium.FOOD_RESOURCE / self.stat.people_alive_number
		if food_per_man > genetics.RICH_CONSUME_RATE * genetics.FOOD_COEF:
			abundance = True
			food_per_man_corrected = genetics.RICH_CONSUME_RATE * genetics.FOOD_COEF# это ограничение надо будет потом убрать
		else:
			food_per_man_corrected = food_per_man
		s = f'\n==================\n{self.anno.year}:{self.anno.month}\n'
		s += f'Общее количество еды: {Socium.FOOD_RESOURCE:10.2f}\n'
		s += f'Количество людей: {self.stat.people_alive_number}\n'
		s += f'Изначальное количество еды на человека: {food_per_man:7.2f}\n'
		s += f'Скорректированое количество еды на человека: {food_per_man_corrected:7.2f}\n'
		for person  in self.people_alive:
			# присваивает каждому человеку первоначальное количество пищи
			person.health.have_food_equal(food_per_man_corrected)
			# дети до трех лет пищу не добывают
			# дети добывают вдвое меньше еды
			if person.is_baby():
				person.health.have_food_equal(0)
				food_waste += food_per_man_corrected
			elif not person.is_big():
				half_food = person.health.have_food/ 2
				person.health.have_food_equal(half_food)
				food_waste += food_per_man_corrected - half_food
			# женщины с детьми добывают меньше (минус за каждого иждивенца в семье)
			# по идее эту дельту надо передавать в детский бюджет, а не выкидывать в ппустоту
			elif person.gender == 0:
				woman_food_delta = -len(person.family.dependents)* genetics.FOOD_COEF/2 # штраф к еде за каждого ребенка
				person.health.have_food_change(woman_food_delta)
				food_waste -= woman_food_delta # штраф отрицательный, поэтому не прибавляем, а отнимаем
				# тут должен быть else. но его случай обрабатывается в самом начале без условий : это взрослые мужчины
				#print(f'человек: {person.id}  пол: {person.gender} возраст:{person.age.display()}')
		# === строгий подсчет потребляемой пищи по людям ===
		men = 0
		men_count = 0
		women_childless = 0
		women_childless_count = 0
		women_with_children = 0
		women_with_children_count = 0
		women_dep = 0 # сумма иждивенцев в семьях
		children = 0
		children_count = 0
		# считаем, сколько еды потребили все категории населения: мужчины, детные и бездетные женщины, дети
		for person in self.people_alive:
			if person.is_big():
				if person.gender:
					men_count += 1
					men += person.health.have_food
				else:
					if len(person.family.dependents) == 0:
						women_childless_count += 1
						women_childless += person.health.have_food
					else:
						women_dep += len(person.family.dependents)
						women_with_children_count += 1
						women_with_children += person.health.have_food
			else:
				children += person.health.have_food
				children_count += 1
		teor_men = men_count * food_per_man_corrected
		teor_women_childless = women_childless_count * food_per_man_corrected
		teor_women_with_children = women_with_children_count * food_per_man_corrected - women_dep * genetics.FOOD_COEF/2
		teor_children = children_count * food_per_man_corrected/2
		s += "=======================================\n"
		s += "Мужчины %d| потребили фактически %8.2f| теоретически %8.2f|\n" % (men_count, men, teor_men)
		s += "Бездетные женщины %d| потребили фактически %7.2f| теоретически %7.2f|\n" % (women_childless_count, women_childless, teor_women_childless)
		s += "Детные женщины %d| потребили фактически %8.2f| теоретически %8.2f| из-за %d иждивенцев\n" % (women_with_children_count, women_with_children, teor_women_with_children, women_dep)
		s += "Дети %d| потребили фактически %8.2f| теоретически %8.2f|\n" % (children_count, children, teor_children)
		real_f = men + women_childless + women_with_children + children
		teor_f = teor_men + teor_women_childless + teor_women_with_children + teor_children
		s += f'Остатки пищи: {food_waste}\n'
		s += "Итог фактич  %8.2f| теоретич  %8.2f|\n" % (real_f, teor_f)

		#================================
		# считаем пропавшую еду
		wasted_food = 0
		# еда пропавшая из-за детей
		wasted_food += self.stat.children * food_per_man / 2
		s += "Еда пропавшая из-за %d детей: %8.2f\n" % (self.stat.children, wasted_food)
		# еда пропавшая из-за женщин с иждивенцами
		dependents_sum = 0
		for fam in self.families:
			dependents_sum += len(fam.dependents)
		dep_wast = dependents_sum * genetics.FOOD_COEF/2
		s += "Еда пропавшая из-за %d иждивенцев: % 7.1f\n" % (dependents_sum, dep_wast)
		wasted_food += dep_wast
		s += "Пропавшая еда в целом: % 7.1f\n" % wasted_food

		soc_food_budget = 0
		for fam in self.families:
			fam.food_display("первоначальное распределение")
			soc_food_budget += fam.budget
		s += "Сумма распределенного % 7.1f| и пропавшего % 7.1f|: % 7.1f\n" % (soc_food_budget, wasted_food, soc_food_budget + wasted_food)
		s += "%s первоначальное распределение еды : %7.1f\n" % (self.anno.display(), soc_food_budget)

		# откладываем часть еды в семейный бюджет
		self.feeding_log.write(s)
		for fam in self.families:
			fam.make_food_supplies()

		def shuffle_families(number):
			diap = number//3  # треть семей
			seq = [x for x in range(number)]
			random.shuffle(seq)
			m = seq[:diap]
			n = seq[diap:2*diap]
			return (m, n)  # две группы семей, которые будут делить еду между собой

		sum_family_resourses = 0
		soc_food_budget = 0
		group_1, group_2 = shuffle_families(len(self.families))
		for fam in self.families:
			fam.food_display("После создания запасов")
			soc_food_budget += fam.budget
			sum_family_resourses += fam.resource
		self.feeding_log.write("%s еда после создания запасов : %7.1f + %7.1f = %7.1f\n" % (self.anno.display(), soc_food_budget, sum_family_resourses, soc_food_budget + sum_family_resourses))

		for i in range(len(group_1)):
			Family.figth_for_food(self.families[group_1[i]], self.families[group_2[i]], abundance)
		soc_food_budget = 0
		for fam in self.families:
			fam.food_dist()
			fam.food_display("FINAL")
			soc_food_budget += fam.budget
		self.feeding_log.write("%s Потребленная еда: %7.1f\n" % (self.anno.display(), soc_food_budget))




	def stranger_comes_to_socium(self):
		'''
		процедура для пополнения социума свежей кровью.
		в срежнем после пяти умарших персонажей в социум приходит взрослый чужак,
		который никому не является родственником и может завести семью
		'''
		if self.short_death_count > random.randrange(9):
			# пока будет случайный пол, но пол незнакомцев должен выравнивать демографическую обстановку в социуме
			stranger_gender =  random.randrange(2)
			self.add_human(Human(self, stranger_gender, None, None, random.randrange(18, 35)))
			self.short_death_count = 0


	def display_tribes(self):
		'''
		Краткая сводка по племенам, когда выводятся их айдишники, количество членов и средние значения генов в племени
		'''
		st = ''
		for tri in self.stat.tribes_in_socium:
			elder_of_tribe = self.stat.tribes_in_socium[tri][0]
			tribe_family_name = elder_of_tribe.name.family[1]
			st += '%d:%d| '% (self.anno.year, self.anno.month)
			st += '%12s| %7s: %4d | ' % ( tribe_family_name, tri, self.stat.families_in_tribe_count[tri])
			st += '%4d | %s\n' %(self.stat.tribes_in_socium_count[tri], self.stat.count_tribe_genes_average(tri))
		return st


	def display_tribes_verbose(self):
		'''
		Подробная информация о племенах. С перечислением каждого члена племени, к какой семье он нотнсится, какую роль
		в семье занимает. Ну и указание ФИО и идентификатора. В общем выводятся все живые люди.
		'''
		st = ''
		for tri in self.stat.tribes_in_socium:
			#st += ("=======================\n")
			elder_of_tribe = self.stat.tribes_in_socium[tri][0]
			tribe_family_name = elder_of_tribe.name.family[1]
			for fam in self.stat.families_in_tribe[tri]:
				st += ("-------------\n")
				date_fam = "%d:%d| %s| %s| " % (self.anno.year, self.anno.month, tri, fam.id)
				for member in fam.all:
					if member is fam.head:
						role = 'глав'
					elif member is fam.wife:
						role = 'жена'
					else:
						role = 'чадо'
					st =  st + date_fam + role
					st +=" | %s| %s\n" % (member.id, member.name.display())
		return st




	def hall_of_fame(self, list_of_dead):
		hall= open("./xoutput/hall_of_fame.txt", "a", encoding = "UTF16")
		list_of_dead.sort(key=lambda x: x.id)
		for person in list_of_dead:
			# записи про каждого мертвого человека с подробностями его жизни
			hall.write("\n====================================\n")
			hall.write(person.necrolog())
		hall.close()

