import random
import soc_time
import common
import human
import family
import genetics
import socium
from common import Stage_of_age, Age, STAGE_DICT, Gender, apply_gender, Parnt

random.seed(666)

s = socium.Socium()


f = human.Human(s, family.BiolParents(None), gender=Gender.MALE, age_int=28)
m = human.Human(s, family.BiolParents(None), gender=Gender.FEMALE, age_int=20)
s.add_human(f)
s.add_human(m)
for pers in s.soc_list:
    print(pers.display())

s.stat.count_soc_state()

print('--', s.anno.display() )
s.tictac()
s.marry(f, m)
s.stat.count_soc_state()
s.tictac()
for pers in s.soc_list:
    print(pers.display())

for fam in s.families:
    print(fam.display())

