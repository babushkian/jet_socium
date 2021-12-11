import random
import soc_time
import common
import human
import family
import genetics
import socium


random.seed(666)

s = socium.Socium()

for  i in  range(12):
    none_parents = family.Parents(None)
    f = human.Human(s, none_parents, gender=None, age_int=18)
    s.add_human(f)

s.stat.count_soc_state()
for i in range(110):
    print('--', s.anno.display() )
    s.tictac()
    for pers in s.soc_list:
        print(pers.display())

    for fam in s.families:
        print(fam.display())

