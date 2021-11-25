from __future__ import annotations
import random
import math
from typing import Optional, List, Dict, Tuple, IO, Set, NewType
from copy import copy

from names import CharName
import genetics
from genetics import GN

from common import Stage_of_age, Age, STAGE_DICT, Gender, apply_gender, Parnt

import prop
import family
import score
from soc_time import Date, ZERO_DATE, TIK, YEAR, FAR_FUTURE
import fetus


# подгоночный коэффициент для беременности, чтобы человек с фертильностью 5
# забеременнил где-то два раза за фертильный возраст
#PREGNANCY_CONST = 0.218 # вроде маловата, надо больше, люди мрут
PREGNANCY_CONST = 0.398

PREGNANCY_DURATION = Date(0, 0, round(Date.DAYS_IN_YEAR*3/4))
print(PREGNANCY_DURATION.display())
print(PREGNANCY_DURATION.len())


DIVOCE_CHANSE = 1 / (2 * 20 * Date.DAYS_IN_YEAR) / 40 # вероятность развестись раз в 20 лет, плюс проверяют оба супруга а еще подгоночный коэффициент

FERTIL_RERIOD = (STAGE_DICT[Stage_of_age.AGED] - STAGE_DICT[Stage_of_age.ADULT]).year \
                * Date.DAYS_IN_MONTH * Date.MONTHS_IN_YEAR
PREGNANCY_CHANCE = PREGNANCY_CONST / FERTIL_RERIOD

#BirthDate = NewType('BirthDate', Date)
#DeathDate = NewType('DeathDate', Date)
MarryDate = NewType('MarryDate', Date)
DivorseDate = NewType('DivorseDate', Date)


class Human:
    GLOBAL_HUMAN_NUMBER: int = 0
    chronicle: IO
    chronicle_stranger_come = '{0}| В социум влился {1}, возраст - {2} лет.'
    chronicle_marriage = '{0}| {1}| свадьба между {2}({3}) и {4}({5})'
    chronicle_pregnacy = '{0}| {1} беременна. Ожидается {2} ребенка.'
    chronicle_born = '{0}| Родился {1}. Мать: |{2}| {3}({4}). Отец: |{5}| {6}({7}).'
    chronicle_divorce = '{0}| {1}| {2}({3}) и {4}({5}) развелись.'
    chronicle_widowed_fem = '{0}| {1} овдовела.'
    chronicle_widowed_mal = '{0}| {1} овдовел.'
    chronicle_died_fem = '{0}| {1} умерла в возрасте {2} лет'
    chronicle_died_mal = '{0}| {1} умер в возрасте {2} лет'
    #DIVORCE_CASES_DICT = {spouse_cause: "по вине супруга", self_cause: "по своей инициативе",
    # spouse_death: "из-за сметри супруга", death: "по причине смерти"}
    # такое ощущение, чт надо два наследственных подкласса сделать Male и Female для простоты обработки ситуаций

    def __init__(self, socium, biol_parents:family.Parents, gender: Optional[Gender]=None, age_int: int=0):
        Human.GLOBAL_HUMAN_NUMBER += 1
        self.id: str = f'{Human.GLOBAL_HUMAN_NUMBER:07d}'
        self.socium = socium
        self.socium.stat.people_inc()
        self.gender = apply_gender(gender)

        self.state: bool = True
        # начальный возраст человека, будет увеличиваться каждый тик
        self.age: Age = Age(self, age_int)

        self.health: genetics.Health = genetics.Health(self)
        self.score = score.Score()
        self.genes: genetics.Genes = genetics.Genes(self)

        self.spouse: Optional[Human] = None  # супруга нет
        # текущий супруг в этот список не входит

        self.marry_dates: Dict[MarryDate, Human] = dict()  # для каждого супруга своя дата свадьбы, причем на
        # одном человеке можно жениться несколько раз, бывает и такое
        # в этих словарях дата указывает на объект бывшего супруга
        self.divorce_dates: Dict[DivorseDate, Human] = dict()
        self.pregnant: List[Optional[fetus.Fetus]] = list()
        self.children: List[Optional[Human]] = list()


        # родители, которые зачали ребенка
        self.biological_parents: family.Parents = biol_parents

        if self.biological_parents.mother.is_human :
            # ребенок родился естественным путем
            self.mother: Human = self.biological_parents.mother
            self.father: Human = self.mother.spouse
        else:
            # пришел странник
            self.father: Human = self.biological_parents.father
            self.mother: Human = self.biological_parents.mother

        # имя надо дать до создания семьи. Тем более что биологические родители известны
        # когда в семье определятся социальные родители, можно переопределить отчество-фамилию,
        # тем более в классе семьи это должно делаться автоматически
        self.name: CharName = CharName(self)

        # по идее структура так должна выглядеть, потому что у ребенка может смениться несколько отцов и матерей
        # социальные родители определяются после попадания в семью
        self.social_parents: Dict[Parnt, List[Human]] # пои идее структура так должна выглядеть

        if self.biological_parents.mother.is_human:
            self.family: family.Family = self.biological_parents.mother.family
            self.child_number_in_mothers_family = self.mother.family.add_child(self)
            self.social_parents = family.Parents(self.family)
            self.tribe_origin = None # племя той семьи, в которой вырос ребенок. Используется только во взрослом виде

        else:
            self.child_number_in_mothers_family = 0
            self.family: family.Family = family.Family(self)
            self.genes.define_adult()
            self.social_parents = copy(biol_parents)
            self.tribe_origin = self.family.id # основатель имеет свое изначальное племя



        # множество близких родственников для определения, на ком можно жениться
        self.close_ancestors: Set[Human] = self.define_close_ancestors()

        if self.mother.is_human:
            tup = (self.id, self.name.display(), self.mother.id, self.mother.name.display(), self.mother.age.year,
                   self.father.id,	self.father.name.display(), self.father.age.year)
            Human.write_chronicle(Human.chronicle_born.format(*tup))
        else:
            Human.write_chronicle(Human.chronicle_stranger_come.format(self.id, self.name.display(), self.age.year))


    @staticmethod
    def init_files():
        #Human.chronicle = open('./xoutput/chronicle.txt', 'w', encoding='utf16')
        Human.chronicle = open('./chronicle.txt', 'w', encoding='utf16')

    @staticmethod
    def close():
        Human.GLOBAL_HUMAN_NUMBER = 0
        Human.chronicle.close()

    @staticmethod
    def write_chronicle( message):
        Human.chronicle.write(message + '\n')

    @property
    def is_human(parent: Human) -> bool:
        return True

    def live(self) -> None:
        self.health.modify() # уменьшается счетчик жизней
        self.age.increase()
        is_dead = self.health.is_zero_health
        if is_dead == True:
            self.die() # перс умирает
        if self.is_alive:
            self.score.update(self.score.LIVE_SCORE)
            if self.age.is_big:
                # Зачинаем детей
                if self.is_married and self.gender is Gender.FEMALE and self.age.is_fertile_age:
                    if self.check_fertil_age() and self.check_fertil_satiety():
                        self.check_pregnant()
                # Разводимся
                # шанс развода: 1 на три семьи, если они живут вместе по 40 лет в серднем (два прохода на обоих супругов)

                if self.check_divorce():
                    self.divorce()

    def check_divorce(self) -> bool:
        if self.is_married:
            chanse: float = DIVOCE_CHANSE *(1+ (
                    self.genes.get_trait(genetics.GN.EGOISM) * self.spouse.genes.get_trait(genetics.GN.EGOISM)
                    - self.spouse.genes.get_trait(genetics.GN.ALTRUISM)/ 4))  # супруг сопротивляется разводу
            return chanse > random.random()
        else:
            return False

    def divorce(self) -> None:
        def divorce_one_spouse(person: Human) -> None:
            person.add_divorce_date()
            person.spouse = None

        spouse = self.spouse
        self.score.update(self.score.DIVORSE_ACTIVE_SCORE)
        spouse.score.update(self.score.DIVORSE_PASSIVE_SCORE)
        tup = (self.id, spouse.id, self.name.display(), self.age.year, spouse.name.display(), spouse.age.year)
        Human.write_chronicle(Human.chronicle_divorce.format(*tup))
        divorce_one_spouse(self)
        divorce_one_spouse(spouse)
        self.family.divide_families()

    # удалять мертвых людей не надо может быть перемещать в какой-то другой список
    def die(self) -> None:
        self.socium.short_death_count +=1
        self.socium.global_death_count +=1
        self.socium.stat.people_dec()  # уменьшаем количество живущих людей
        self.state = False
        self.age.death_date = self.socium.anno.create()
        if self.gender is Gender.MALE:
            form = Human.chronicle_died_mal
        else:
            form = Human.chronicle_died_fem
        Human.write_chronicle(form.format(self.id, self.name.display(), self.age.year))
        self.socium.stat.add_to_deadpool(self)
        if self.spouse:
            if self.gender is Gender.MALE:
                form = Human.chronicle_widowed_fem
            else:
                form = Human.chronicle_widowed_mal
            Human.write_chronicle(form.format(self.spouse.id, self.spouse.name.display()))
            self.add_divorce_date()
            self.spouse.add_divorce_date()
            spouse = self.spouse
            self.spouse = None
            spouse.spouse = None
        self.family.dead_in_family(self)


    def define_close_ancestors(self) -> Set[Human]:
        '''
        Метод определяет близких родственников человека для предотвращения кровосмешения. С первого взгляда может
        показаться, что он работает неправильно, так как в близкие родственники записывает только отца с матерью
        и бабушек с дедушками. А двоюродные братья и дяди с тетями остаются за бортом. Но на самом деле ищутся
        пересечения множеств у двух человек. Если у жениха с невестой общий бабущка или ддедушка, это означает
        как минимум их двоюродное родство.
        '''
        def get_close_ancestors(person: Human, close_an: set, step: int) -> None:
            if step > 0:
                if person.is_human:
                    close_an.add(person.father)
                    close_an.add(person.mother)
                    get_close_ancestors(person.father, close_an, step-1)
                    get_close_ancestors(person.mother, close_an, step-1)
        s = set()
        s.add(self)
        get_close_ancestors(self, s, 2)
        return s

    def get_marry(self, spouse: Human) -> None:
        self.spouse = spouse
        self.add_marry_date()
        if self.gender is Gender.FEMALE:
            self.name.change_family_name(spouse)

    def add_marry_date(self) -> None:
        self.marry_dates[self.socium.anno.create()] = self.spouse

    def add_divorce_date(self) -> None:
        self.divorce_dates[self.socium.anno.create()] = self.spouse


    def compare_genes(self, other):
        return math.log(self.genes.difference(other.genes)+2)



    def give_birth(self) -> None:
        # сделать цикл для двойни, тройни и тд
        while len(self.pregnant) > 0 :
            child = self.pregnant.pop().born(self.socium)
            self.socium.add_human(child)
            self.children.append(child)
            self.spouse.children.append(child)

            self.score.update(self.score.MAKE_CHILD)
            self.spouse.score.update(self.score.MAKE_CHILD)
            # на сколько лет сокращается жизнь в результате родов
            damage = abs(prop.gauss_sigma_2())
            # урон, вызванный привычкой умеренно питаться (в годах)
            # если женщина неумеренная, наоборот, роды пройдут лучше
            frail_damage =  self.genes.get_trait(genetics.GN.STRONGNESS) - 5
            # бонус от физической выносливости
            recovery = self.genes.get_trait(genetics.GN.STRONGNESS) # меньше родовая травма
            total_damage = max(0, damage + frail_damage - recovery)
            # в среднем должен получаться год-два уронм, поэтому делю на 4
            birth_injury = genetics.HEALTH_PER_DAY * Date.DAYS_IN_YEAR * total_damage / 4
            self.health.reduce(birth_injury)


    def check_pregnant(self) -> None:
        if len(self.pregnant) == 0:
            check = PREGNANCY_CHANCE*3*(self.genes.get_trait(genetics.GN.FERTILITY) * math.sqrt(self.spouse.genes.get_trait(genetics.GN.FERTILITY)) )
            if  check > random.random():
                fetus_amount = int(1 +  abs(prop.gauss_sigma_1()) + 1/12 * (self.genes.get_trait(genetics.GN.FERTILITY) - 5))
                if fetus_amount < 1:
                    fetus_amount = 1
                for num in range(fetus_amount):
                    self.pregnant.append(fetus.Fetus(self))
                Human.write_chronicle(Human.chronicle_pregnacy.format(self.id, self.name.display(), fetus_amount))
        else:
            for i in self.pregnant:
                i.age += TIK
            # не важно, сколько детей, берем первого попавшегося ; срок беременности > 3 месяцев, то есть год
            if self.pregnant[0].age > PREGNANCY_DURATION:
                self.give_birth()

    def check_fertil_age(self) -> bool:
        def _count_fertil_age(trait: int) -> Date:
            add_date = genetics.FERTILE_DELTA * (trait/genetics.Gene.MAX_VALUE)
            date = STAGE_DICT[Stage_of_age.CHILD] + add_date
            return date
        fert = True
        for person in (self, self.spouse):
            if person.age < _count_fertil_age(person.genes.get_trait(GN.FERT_AGE)):
                fert = False
                break
        return fert

    def check_fertil_satiety(self) -> bool:
        fert = True
        for person in (self, self.spouse):
            if person.health.satiety < person.genes.get_trait(GN.FERT_SATIETY):
                fert = False
                break
        return fert

    @property
    def is_married(self) -> bool:
        return self.spouse is not None

    @property
    def is_alive(self) -> bool:
        return self.state

    def display(self):
        s= f'{self.id}| {self.gender.value:7s} семья:{self.family.id:7s}  trib_orig:{str(self.tribe_origin):7s} '
        s+=f'{self.age.display()} жив:{self.state}'


        return s

    def necrolog(self) -> str:
        nec  = "%s| %s | %s \n" % (self.id, self.name.display(), self.family.id)
        nec += "Дата рождения: %s \n" % self.age.birth_date.display()
        nec += "Дата смерти: %s \n" % self.age.death_date.display()
        nec += "Возраст смерти: %s\n" % (self.age.death_date-self.age.birth_date).display(False)
        nec += "Карма: %d\n" % self.score.score

        def show_genes() -> str:
            g = 'Гены:\n'
            for i in GN:
                g += '\t%s: %2d' %(i[:6], self.genes.get_trait(i))
                if self.genes.genome[i].predecessor is None:
                    sex = 'нет'
                elif self.genes.genome[i].predecessor.gender is Gender.MALE:
                    sex = 'отец'
                else:
                    sex = 'мать'
                pv = self.genes.genome[i].pred_value
                delta = self.genes.genome[i].value - pv
                prog = '+' if delta > 0 else '-'
                g += ' (%2d)| %s |%s\n' % (pv, sex, prog * abs(delta))
            return g

        g = show_genes()
        nec = nec +g +"\n"

        nec +="Супруги (%d):\n" % len(self.marry_dates)
        if len(self.marry_dates) > 0:
            sp=""
            # а может они и так упорядочены?
            rec_m = sorted(self.marry_dates.keys(), key=lambda x: x.len()) # список упорядоченных дат женитьбы
            rec_d = sorted(self.divorce_dates.keys(), key=lambda x: x.len())  # список упорядоченных дат развода
            for (dm, dd) in zip(rec_m, rec_d):
                spouse = self.marry_dates[dm]
                delta = dd - dm
                sp += "\t%s| %s | брак - %s\n" % (spouse.id, spouse.name.display(), delta.display(False))
                sp += "\t\tСвадьба: %s\n" % dm.display()
                sp += "\t\tРазвод:  %s" % dd.display()
                ss = "\n"
                if dd == self.age.death_date:
                    ss = " (смерть)\n"
                elif spouse.age.death_date is None:
                    pass
                elif dd == spouse.age.death_date:
                    ss = " (смерть супруга)\n"
                sp +=ss
            nec += sp

            nec +="Дети (%d):\n" % len(self.children)
            if len(self.children)==0:
                sp = "\tнет\n"
            else:
                sp=""
                for child in self.children:
                    sp += "\t%s| %s (%s)" % (child.id, child.name.display(), child.age.birth_date.display())
                    if child.father == self:
                        other_patent = "(мать:  %s)\n" % child.mother.id
                    else:
                        other_patent = "(отец:  %s)\n" % child.father.id
                    sp += other_patent

        else:
            sp = "\tнет\n"
        nec += sp
        return nec

    def magareport(self):
        stat_list= list()
        # гены
        for i in GN:
            stat_list.append(self.genes.get_trait(i))
        # возраст отца и матери на момент проверки. Человек может умереть, радителт все еще живут
        # так же возраст родителей на момент рождения человека
        preds_old_age = {x:0 for x in Gender}
        preds_age_on_birthday = preds_old_age.copy()
        if self.biological_parents.mother.is_human:
            for pred in self.biological_parents.lst:
                preds_old_age[pred.gender] = pred.age.len()
                preds_age_on_birthday[pred.gender] = (self.age.birth_date - pred.age.birth_date).len()
        for gen in Gender:
            stat_list.append(preds_old_age[gen])
            stat_list.append(preds_age_on_birthday[gen])

        # каким по счету ребенком в семье он был
        stat_list.append(self.child_number_in_mothers_family)
        stat_list.append(len(self.marry_dates))
        # количество детей у человека
        stat_list.append(len(self.children))
        # возраст смерти
        stat_list.append(self.age.len())
        return stat_list



class NoneHuman(Human):

    def __init__(self, gender):
        self.id: str = 'NoneHuman_id'
        self.gender: Gender = gender
        self.state: bool = False
        self.name: CharName = CharName(self)


    @property
    def is_human(parent: Human) -> bool:
        return False

    def info(self):
        return self.name.display()