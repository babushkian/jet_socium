import random
import soc_time
import common
import human
import family
import genetics
import socium


random.seed(666)

s = socium.Socium()
'''
none_parents = family.Parents(None)
m = human.Human(s, none_parents,  gender=common.Gender.MALE,  age_int=20)
m.health.set_health(100)
s.add_human(m)
none_parents = family.Parents(None)
f = human.Human(s, none_parents,  gender=common.Gender.FEMALE,  age_int=20)
s.add_human(f)

none_parents = family.Parents(None)
m = human.Human(s, none_parents,  gender=common.Gender.MALE,  age_int=20)
m.health.set_health(100)
s.add_human(m)
none_parents = family.Parents(None)
f = human.Human(s, none_parents,  gender=common.Gender.FEMALE,  age_int=20)
s.add_human(f)
'''

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

