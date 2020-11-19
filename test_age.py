import soc_time
import common
import human
import genetics
import socium

s = socium.Socium()
h = human.Human(s, (None, None), 1,  0)
h.health.set_health(1000)
s.add_human(h)
h = human.Human(s, (None, None), 1,  5)
s.add_human(h)
h = human.Human(s, (None, None), 1,  17)
s.add_human(h)




s.stat.count_soc_state()
for i in range(80):
    print('--', s.anno.display() )
    s.tictac()
    for h in s.soc_list:
        print(h.age.display(), h.age.stage)

