import sqlite3

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
	names = []
	for rec in table:
		rec = rec.rstrip()
		names.append(rec.split("\t"))
	return names


def load_fem_names():
	table = open("./имена и фамилии/fem_names.csv", "r").readlines()
	fem_name = []
	for rec in table:
		rec = rec.rstrip()
		fem_name.append(rec)
	return tuple(fem_name)


conn = sqlite3.connect('names.db')
c = conn.cursor()

c.execute('DROP TABLE IF EXISTS family')
c.execute('DROP TABLE IF EXISTS fem_names')
c.execute('DROP TABLE IF EXISTS male_names')


c.execute("""CREATE TABLE IF NOT EXISTS fem_names (
	id INTEGER PRIMARY KEY,
	first_name TEXT NOT NULL)""")
c.execute("""CREATE TABLE IF NOT EXISTS male_names (
	id INTEGER PRIMARY KEY,
	first_name TEXT NOT NULL, 
	second_name_fem TEXT NOT NULL,
	second_name_male TEXT NOT NULL)""")

c.execute("""CREATE TABLE IF NOT EXISTS family (
	id INTEGER PRIMARY KEY,
	fem TEXT NOT NULL, 
	male TEXT NOT NULL)""")
conn.commit()

fff= load_family_names()
for fm in fff:
	c.execute('INSERT INTO family (fem, male) VALUES(?, ?)', (fm))

fff= load_fem_names()
for fm in fff:
	c.execute('INSERT INTO fem_names (first_name) VALUES("{}")'.format(fm))

fff= load_male_names()
for fm in fff:
	c.execute('INSERT INTO male_names (first_name, second_name_fem, second_name_male) VALUES(?, ?, ?)', (fm))

conn.commit()
c.close()
conn.close()
