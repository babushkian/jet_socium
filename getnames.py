import sqlite3
from pprint import pprint
from typing import Tuple, Dict
from common import Gender

def load_family_names()->Tuple[Dict[Gender, str]]:
	conn = sqlite3.connect('names.db')
	c = conn.cursor()
	command = 'SELECT fem, male FROM  family'
	c.execute(command)
	families = c.fetchall()
	conn.close()
	flist = list()
	for f in families:
		flist.append({g:fam for g, fam in zip(Gender, f)})
	return tuple(flist)


def load_second_names():
	first_name = []
	fem_name = []
	male_name = []
	conn = sqlite3.connect('names.db')
	c = conn.cursor()
	command = 'SELECT first_name, second_name_fem, second_name_male  FROM  male_names'
	c.execute(command)
	namedict: Dict[str, Dict[Gender, str]] = dict()
	while True:
		record = c.fetchone()
		if record == None:
			break
		else:
			namedict[record[0]] = {Gender.FEMALE:record[1], Gender.MALE:record[2]}
	conn.close()
	return namedict


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
	return tuple(nl)

if __name__ == '__main__':
	# x = load_family_names()
	# print(x)

	x = load_second_names()
	pprint(x)