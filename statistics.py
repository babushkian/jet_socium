'''
===============================
По-хорошему, надо делать вывод статистики в XML
===============================
Статистические данные по социуму
'''
import socium
import human
import genetics
from soc_time import Date, ZERO_DATE, TIK, YEAR, FAR_FUTURE

MEASURMENT_PERIOD = 40
CHILDREN_COUNT_TRESHOLD = 9


class Soc_stat():
	"""
	Рассчитывает основную статистику по социумк
	"""
	def __init__(self, socium):
		self.socium = socium
		self.families_in_socium = {}
		self.count_of_families = 0
		self.people_alive_number = 0

		# список, содержащий все гены человека для подсчета их средних значений

		self.genes_average = open("./xoutput/genes_average.csv", "w", encoding="UTF16")
		header = "year\t"
		sex = ["women_", "men_"]
		for g in range(len(sex)):
			for i in genetics.Genes.GENOTYPE:
				header += "%s \t" % (sex[g]+i)
		header = header[:-1] +"\n"
		self.genes_average.write(header)

		self.ss = open("./xoutput/statistics.csv", "w", encoding="UTF16")
		# для вычисления среднего возраста смерти содержатся люди умершие за последние 5 дет

		self.death_dist = open("./xoutput/death_distribution.csv", "w", encoding="UTF16")
		dead_head = "год\t"
		for i in range(11):
			dead_head += ">%s\t" % str(i * 10)
		dead_head += "муж смерть\tжен смерть\n"
		self.death_dist.write(dead_head)

		self.childern_average = open("./xoutput/children_average.csv", "w", encoding="UTF16")
		self.childern_average.write("год\tсредн детей у мужчин\tсредн детей у женщин\n")
		self.children_m = open("./xoutput/children_distribution_men.csv", "w", encoding="UTF16")
		self.children_f = open("./xoutput/children_distribution_fem.csv", "w", encoding="UTF16")

		head = "год\t"
		for i in range(CHILDREN_COUNT_TRESHOLD):
			head += "%s\t" % (str(i) + " детей")
		head = head[:-1] + "\n"
		self.children_m.write(head)
		self.children_f.write(head)
		# люди, умершие за последне пять лет. Нужно .чтобы считать средний возраст смерти
		self.dead_pool_avg = []

		header = "год\tлюдей за всю историю\tпища\tживущих\tмужчин\tженщин\tдетей\tвзрослых"
		header += "\tпожилых\tсредний возраст\tсредний возраст смерти\tколичество семей"
		header += "\t% детей\t% взрослых\t% стариков\n"
		#header += ""

		self.ss.write(header)

	

	def people_inc(self, inc =1):
		self.people_alive_number += inc
	

	def people_dec(self, dec =1):
		self.people_alive_number -= dec


	def add_to_deadpool(self, person):
		self.dead_pool_avg.append(person)


	def update_deadpool(self):
		temp = []
		for person in self.dead_pool_avg:
			if self.socium.anno < (person.death_date + Date(5)):
				temp.append(person)
		self.dead_pool_avg = temp


	def count_avg_death_age(self):
		summa = 0
		for person in self.dead_pool_avg:
			summa += (person.death_date - person.birth_date).len()
		ld = len(self.dead_pool_avg)
		if ld > 0:
			avg_date = summa / ld
		else:
			avg_date = 0
		return Date(0, 0, avg_date).years_float()


	def count_death_distribution(self):
		death_age =  [ 0 for i in range(11)]
		number_of_dead_people = 0
		nomb_men = 0
		nomb_women = 0
		men_death_sum = 0
		women_death_sum = 0

		def death_dist(person):
			nonlocal death_age
			nonlocal number_of_dead_people
			number_of_dead_people += 1
			dec_index =int((person.death_date - person.birth_date).years_float()//10)
			if dec_index > 10:
				dec_index = 10
			death_age[dec_index] += 1

		def death_gender(person):
			nonlocal nomb_men
			nonlocal nomb_women
			nonlocal men_death_sum
			nonlocal women_death_sum
			if person.gender:
				nomb_men += 1
				men_death_sum += (person.death_date - person.birth_date).years_float()
			else:
				nomb_women += 1
				women_death_sum += (person.death_date - person.birth_date).years_float()

		for person in self.socium.soc_list:
			if not person.is_alive and self.socium.anno < (person.death_date + Date(MEASURMENT_PERIOD)):
				death_dist(person)
				death_gender(person)

		s = "%s\t" % str(self.socium.anno.year)
		for i in range(len(death_age)):
			if number_of_dead_people == 0:
				s += "0\t"
			else:
				s += "%5f\t" % (death_age[i]/number_of_dead_people*100)
		am = 0 if nomb_men == 0 else men_death_sum / nomb_men
		aw = 0 if nomb_women == 0 else women_death_sum / nomb_women
		s += "%5f\t%5f" % (am, aw)
		s = s[:-1].replace(".", ",") + "\n"
		self.death_dist.write(s)


	def count_children(self):
		children_male = [0 for i in range(CHILDREN_COUNT_TRESHOLD)]
		children_female = [0 for i in range(CHILDREN_COUNT_TRESHOLD)]
		no_male = 0
		no_female = 0
		for person in self.socium.soc_list:
			if person.is_adult and \
					(person.death_date is None or self.socium.anno < (person.death_date + Date(MEASURMENT_PERIOD))):
				# считаем количество детей у мужчин и у женщин по отдельности
				ch = len(person.children)
				if ch >= CHILDREN_COUNT_TRESHOLD:
					ch = CHILDREN_COUNT_TRESHOLD - 1
				if person.gender:
					no_male += 1
					children_male[ch] += 1
				else:
					no_female += 1
					children_female[ch] += 1
		rec_m = rec_f = "%s\t" % str(self.socium.anno.year)
		ch_aver_male = 0
		ch_aver_fem = 0
		for i in range(len(children_female)):
			ch_aver_male += i * children_male[i]
			ch_aver_fem += i * children_female[i]

			if no_male ==0:
				rec_m += "    0\t"
			else:
				rec_m += "%5f\t" % (children_male[i] / no_male * 100)
			if no_female ==0:
				rec_f += "    0\t"
			else:
				rec_f += "%5f\t" % ( children_female[i] / no_female * 100)

		if no_male == 0:
			ch_aver_male = 0
		else:
			ch_aver_male /= no_male
		if no_female == 0:
			ch_aver_fem = 0
		else:
			ch_aver_fem /= no_female

		rec_ave = "%d\t%5f\t%5f\n" % (self.socium.anno.year, ch_aver_male, ch_aver_fem)
		rec_ave = rec_ave.replace(".", ",")
		self.childern_average.write(rec_ave)

		rec_m = rec_m[:-1].replace(".", ",") + "\n"
		rec_f = rec_f[:-1].replace(".", ",") + "\n"
		self.children_m.write(rec_m)
		self.children_f.write(rec_f)




	def count_genes_average(self):
		"""
		рассчет средних значений генов у всей популяции
		"""
		g_m = {i:0 for i in genetics.Genes.GENOTYPE} # мужчины отдельно
		g_f = g_m.copy() # женщины отдельно
		g = [g_m, g_f]
		col = [self.women, self.men]
		for person in self.socium.people_alive:
			for trait in genetics.Genes.GENOTYPE:
				g[person.gender][trait] += person.genes.get_trait(trait)

		genome_record = "%s\t" % self.socium.anno.year

		for gen in range(2):
			for i in g[gen]:
				if col[gen] > 0:
					avg = str(g[gen][i]/col[gen])
				else:
					avg = '0'
				genome_record +=  "%s\t" % avg.replace(".", ",")
		genome_record = genome_record [:-1] +"\n"

		self.genes_average.write(genome_record)


	def count_family_genes_average(self, family):
		g = {i:0 for i in genetics.Genes.GENOTYPE}
		for person in family.all:
			for trait in genetics.Genes.GENOTYPE:
				g[trait] += person.genes.get_trait(trait)
		genome_record = ""
		for i in g:
			g[i] /=len(family.all)
			genome_record +=  "%s = %4.1f | " %(i[:3], g[i])
		genome_record += "\n"
		return genome_record


	def count_tribe_genes_average(self, tribe_name):
		fg = {i: 0 for i in genetics.Genes.GENOTYPE}
		for person in self.tribes_in_socium[tribe_name]:
			for i in fg:
				fg[i] += person.genes.get_trait(i)
		genome_record = ''
		for i in fg:
			fg[i] /= self.tribes_in_socium_count[tribe_name]
			genome_record +=  "%s=%4.1f |" %(i[:3], fg[i])
		return genome_record



	def count_soc_state(self):
		'''
		считаем статистику по социуму
		'''
		self.men = 0
		self.women = 0
		self.children = 0
		self.adult = 0
		self.aged = 0
		alive_age_sum = 0.0

		# делаем список живых людей
		self.socium.clear_people_alive()

		for pers in self.socium.soc_list:	
			if pers.is_alive:
				self.socium.people_alive_add(pers)

				alive_age_sum += pers.age.year  # суммируем возраст всех живых людей,
				# чтобы потом разделить на количество людей (с точностью до года)
				
				if pers.gender:
					self.men += 1     #  количтество мужчин (любого возраста)
				else:
					self.women += 1    #  количтество женщин (любого возраста)
				if pers.is_baby or pers.is_child:
					self.children +=1  #  количтество детей
				elif pers.is_adult:
					self.adult += 1  #  количтество взрослых
				else:
					self.aged +=1    #  количтество стариков


		# средний возраст социума
		average_age = alive_age_sum / self.people_alive_number

		self.family_statistics()
		# количество семей в социуме
		self.count_of_families = len(self.families_in_socium)
		# раз в сорок лет считаем статистику распределения смертей по возрасту
		if self.socium.anno.year_starts() and self.socium.anno.year % (MEASURMENT_PERIOD) == 0 :
			self.count_death_distribution()
			self.count_children()
		# условие для очень длинных периодов. чтобы статистика пореже выводилась
		if self.socium.anno.year_starts() and self.socium.anno.year % 1 ==0:
			#if True:
			food_estimate = socium.Socium.FOOD_RESOURCE//genetics.NORMAL_CONSUME_RATE
			# вычисялем средний возраст смерти
			self.update_deadpool()
			average_death_age = self.count_avg_death_age()

			format_1 = "%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d"
			anno_record = format_1 % (self.socium.anno.year, human.Human.GLOBAL_HUMAN_NUMBER,food_estimate, self.people_alive_number,
				self.men, self.women, self.children, self.adult, self.aged)
			anno_record += "\t%5.1f\t%5.1f" % (average_age, average_death_age)
			anno_record += "\t%d" % self.count_of_families
			child_percent = self.children / self.people_alive_number * 100
			adult_percent = self.adult /self.people_alive_number * 100
			aged_percent = self.aged /self.people_alive_number * 100
			anno_record += "\t%4.1f\t%4.1f\t%4.1f\n" % (child_percent, adult_percent, aged_percent)
			anno_record = anno_record.replace(".", ",")
			self.ss.write(anno_record)
		

	def family_statistics(self):
		self.married_people = []
		self.unmarried_men = []
		self.unmarried_women = []
		self.unmarried_adult_men = []
		self.unmarried_adult_women = []
		for person in self.socium.people_alive:
			# считаем замужних (разделение пополам не требуется, так как их всегда равное число)
			if person.is_married:
				self.married_people.append(person)
			# считаем незамужних (всех и отдельно взрослых)
			else:
				if person.gender:
					self.unmarried_men.append(person)
					if person.is_big:
						self.unmarried_adult_men.append(person)
				else:
					self.unmarried_women.append(person)
					if person.is_big:
						self.unmarried_adult_women.append(person)

		self.married_people_number = len(self.married_people)
		self.unmarried_men_number = len(self.unmarried_men)
		self.unmarried_women_number = len(self.unmarried_women)
		self.unmarried_adult_men_number = len(self.unmarried_adult_men)
		self.unmarried_adult_women_number = len(self.unmarried_adult_women)


	def get_families_in_socium(self):
		self.families_in_socium = {}  # перечисление семей по family_id
		self.tribes_in_socium = {}  # перечисление племен, ключ - tribe_name, значение - список клюей в племени
		self.tribes_in_socium_count = {}  # количество членов племени по ключу tribe_name
		self.families_in_tribe = {}  # перечисление семей в племени по ключу tribe_name
		self.families_in_tribe_count = {}  # количество семей в племени по ключу tribe_name
		for person in self.socium.people_alive:
			#считаем семьи
			temp = self.families_in_socium.get(person.family.id, 0)
			if temp == 0:
				self.families_in_socium[person.family.id] = [person]
			else:
				self.families_in_socium[person.family.id].append(person)

			#считаем племена
			temp = self.tribes_in_socium.get(person.tribe_name, 0)
			if temp == 0:
				self.tribes_in_socium[person.tribe_name] = [person]
				self.tribes_in_socium_count[person.tribe_name] = 1
			else:
				self.tribes_in_socium[person.tribe_name].append(person)
				self.tribes_in_socium_count[person.tribe_name] += 1
		# количество семей в племени
		for fam in self.socium.families:
			tribe = fam.head.tribe_name
			temp = self.families_in_tribe.get(tribe, 0)
			if temp == 0:
				self.families_in_tribe[tribe] = [fam]
				self.families_in_tribe_count[tribe] = 1
			else:
				self.families_in_tribe[tribe].append(fam)
				self.families_in_tribe_count[tribe] += 1
