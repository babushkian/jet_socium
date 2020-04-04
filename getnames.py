import sqlite3

def load_family_names():
	conn = sqlite3.connect('names.db')
	c = conn.cursor()
	command = 'SELECT fem, male FROM  family'
	c.execute(command)
	families = c.fetchall()
	conn.close()
	return tuple(families)


def load_male_names():
	first_name = []
	fem_name = []
	male_name = []
	conn = sqlite3.connect('names.db')
	c = conn.cursor()
	command = 'SELECT first_name, second_name_fem, second_name_male  FROM  male_names'
	c.execute(command)
	while True:
		record = c.fetchone()
		if record == None:
			break
		else:
			first_name.append(record[0])
			fem_name.append(record[1])
			male_name.append(record[2])
	conn.close()
	return tuple(first_name), tuple(fem_name), tuple(male_name)


def load_fem_names():
	conn = sqlite3.connect('names.db')
	c = conn.cursor()
	command = 'SELECT first_name FROM fem_names'
	c.execute(command)
	name_tuple = c.fetchall()
	nl = []
	for n in name_tuple:
		nl.append(n[0])
	conn.close()
	fem_name = tuple(nl)
	return fem_name
