
def load_family_names():
	family_names = open("./имена и фамилии/mix_fam.csv", "r").readlines()
	families = list()
	for i in family_names:
		i = i.rstrip()
		ff, mf = i.split("\t")
		families.append((ff, mf))
	return tuple(families)


def load_male_names():
	table = open("./имена и фамилии/men_names.csv", "r").readlines()
	first_name = []
	fem_name = []
	male_name = []
	for rec in table:
		rec = rec.rstrip()
		n = rec.split("\t")
		first_name.append(n[0])
		fem_name .append(n[1])
		male_name.append(n[2])
	return tuple(first_name), tuple(fem_name), tuple(male_name)


def load_fem_names():
	table = open("./имена и фамилии/fem_names.csv", "r").readlines()
	fem_name = []
	for rec in table:
		rec = rec.rstrip()
		fem_name.append(rec)
	return tuple(fem_name)
