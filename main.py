from soc_time import Date
from human import Human
from socium import Socium
import random
import soc_time
import genetics


# хочется повторяемости картины, фиксируем сид
#random.seed(666)
# количество людей в начальной популяции
FIRST_POPULATION = 500
TIMELINE = Date(300)  # кличество лет симуляции


class Simulation:
	def __init__(self, first_popul, timeline):
		self.lohfile = open("./xoutput/population.txt", "w", encoding="UTF16")
		self.every_man_state_log = open("./xoutput/human_state.txt", "w", encoding="UTF16")
		self.tribes_verbose = open("./xoutput/tribes_verbose.txt", "w", encoding="UTF16")
		# инициализируем файл, по мере накопления покойников будем в него дописывать
		hall= open("./xoutput/hall_of_fame.txt", "w", encoding="UTF16")
		hall.close()

		self.soc = Socium()  # создется социум
		self.timeline = timeline
		self.populate(first_popul)
		self.soc.stat.count_soc_state()

	def close(self):
		self.lohfile.close()
		self.every_man_state_log.close()
		self.tribes_verbose.close()
		self.soc.close()

	def populate(self, first_popul):
		for p in range(first_popul):
			gender  = random.randrange(2)
			age = random.randrange(9, 21)
			# почему он сразу не  добавляется в социум по праву создания, зачем отдельно добавлять
			self.soc.add_human(Human(self.soc, gender, None, None, age))

	def simulate(self):
		extinct = False
		for year in range(self.timeline.len()):
			if self.soc.stat.people_alive_number < 6:
				#print("Население вымерло.")
				extinct = True
				break
			self.write_chronicle_title()
			self.soc.tictac()
			Human.write_chronicle(f'население: {self.soc.stat.people_alive_number}')
			self.write_to_logs()
		self.last_record_to_annals()
		self.close()
		return not extinct, self.soc.anno

	def write_chronicle_title(self):
		s = f'\n {"="*40}\n{self.soc.anno.display()}\nнаселение: {self.soc.stat.people_alive_number}'
		Human.write_chronicle(s)

	def write_to_logs(self):
		def write_lohfile(town):
			town.lohfile.write("================================================\n")
			town.lohfile.write("%s\n" % town.soc.anno.display())
			town.lohfile.write("количество племен: %d\n" % len(town.soc.stat.tribes_in_socium))
			town.lohfile.write("количество семей: %d\n" % len(town.soc.families))
			town.lohfile.write("население: %d\n" % town.soc.stat.people_alive_number)
			town.lohfile.write(town.soc.display_tribes())

		def write_human_state(town):
			town.every_man_state_log.write("================================================\n")
			town.every_man_state_log.write("%s\n" % town.soc.anno.display())
			town.every_man_state_log.write("население: %d\n" % town.soc.stat.people_alive_number)
			for i in town.soc.people_alive:
				anno_date = "%d:%d|" % (town.soc.anno.year, town.soc.anno.month)
				famil = " %s|" % i.family.id
				a = i.id
				sex = "М" if i.gender else "Ж"
				b = i.genes.get_trait('fitness')
				c = i.genes.get_trait('abstinence')
				d = i.health.satiety
				e = Date(0, 0, round(i.health.health / genetics.HEALTH_PER_DAY)).display(False)
				fb = - i.health.food_sum
				hf = i.health.have_food
				z = anno_date + famil
				z += " %s| %s|%14s| fit= %2d| abs = %2d| sat = %2d| fd = %5.1f| bonus = %6.1f | heal = %s\n" \
					 % (a, sex, i.age.display(False), b, c, d, hf, fb, e)
				town.every_man_state_log.write(z)

		write_lohfile(self)
		write_human_state(self)
		self.tribes_verbose.write(self.soc.display_tribes_verbose())



	def last_record_to_annals(self):
		dead = []
		for person in self.soc.soc_list:
			if not person.is_alive:
				dead.append(person)
		self.soc.hall_of_fame(dead)

def display_start_genotype(genome) -> str:
	s = ''
	for name, num in zip(genetics.Genes.GEN_PSEUDONYM,  genome):
		s += f'| {genetics.Genes.GEN_PSEUDONYM[name]:4s}:{num:3d} '
	return s

if __name__ == '__main__':
	print('Start.')
	town = Simulation(FIRST_POPULATION, TIMELINE)
	result, final_date = town.simulate()
	print(display_start_genotype(genetics.Genes.gene_profile_0))
	print(f'Последний год: {final_date.display()}')

