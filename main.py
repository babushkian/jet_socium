from soc_time import Date
from human import *
from socium import *
import random
import soc_time
import genetics


# хочется повторяемости картины, фиксируем сид
random.seed(666)

FIRST_POPULATION = 10
moskau = Socium(1000)  # создется социум и передается начальный год
TIMELINE = Date(1000)  # кличество лет симуляции

# количество людей в начальной популяции
for p in range(FIRST_POPULATION):
	gender  = random.randrange(2)
	age = random.randrange(9, 21)
	moskau.add_human(Human(moskau, gender, None, None, age))



lohfile = open("./xoutput/population.txt", "w", encoding="UTF16")
human_genes = open("./xoutput/human_genes.txt", "w", encoding="UTF16")
tribes_verbose = open("./xoutput/tribes_verbose.txt", "w", encoding="UTF16")

# инициализируем файл, по мере накопления покойников будем в него дописывать
hall= open("./xoutput/hall_of_fame.txt", "w", encoding="UTF16")
hall.close()

moskau.stat.count_soc_state()
for year in range(TIMELINE.len()):
	if moskau.stat.people_alive_number < 5:
		print("Население вымерло.")
		break

	moskau.tictac()
	print()
	print("="*40)
	print(moskau.anno.display())
	print("население: %d" % moskau.stat.people_alive_number)
	all_health = [i.health.satiety for i in moskau.people_alive]

	lohfile.write("================================================\n")
	lohfile.write("%s\n"% moskau.anno.display())

	lohfile.write("количество племен: %d\n" % len(moskau.stat.tribes_in_socium))
	lohfile.write("количество семей: %d\n" % len(moskau.families))
	lohfile.write("население: %d\n" % moskau.stat.people_alive_number)
	lohfile.write(moskau.display_tribes())
	tribes_verbose.write(moskau.display_tribes_verbose())
	human_genes.write("================================================\n")
	human_genes.write("%s\n"% moskau.anno.display())
	human_genes.write("население: %d\n" % moskau.stat.people_alive_number)

	for i in moskau.people_alive:
		anno_date = "%d:%d|" % (moskau.anno.year, moskau.anno.month)
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

		human_genes.write(z)
last_fame = []
for person in moskau.soc_list:
	if not person.is_alive:
		last_fame.append(person)
moskau.hall_of_fame(last_fame)

lohfile.close()	
human_genes.close()
