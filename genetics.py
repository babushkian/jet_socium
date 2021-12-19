"""
здесь будут все индивидуальные панраметры человека, влияющие на его поведение

"""
from __future__ import annotations
import random
from typing import List, Dict, NewType, Union, Optional
from enum import Enum

from common import Stage_of_age, STAGE_DICT, DIGEST_FOOD_MULTIPLIER, Gender
from soc_time import Date, ZERO_DATE, TIK
import prop

import human
import fetus
import score



Genes_Holder = Union['fetus.Fetus', 'human.Human']

HEDONIC_CONSUME_RATE = 10
RICH_CONSUME_RATE = 8
NORMAL_CONSUME_RATE = 6
POOR_CONSUME_RATE = 3
STARVE_CONSUME_RATE = 2

# у меня 12 градаций бонуса от еды
# переменная FOOD_COEF умножает количество еды на 20 для того, чтобы количество еды более плавно
# менялось и были какие-то промежуточные варианты

FOOD_COEF = 20

# Какой урон или пользу добавляет еда человеку 
# (в качестве индекса должно выступать количество потребленной еды satiety)
#               0     1   2   3     4    5   6    7    8    9     10  11   12 - не должен достигаться
FOOD_BONUS = [-256, -56, -8, -2, -0.6, -0.2, 0, 0.2, 0.1, -0.3, -0.8, -3, -16]
#FOOD_BONUS = [-64, -16, -7, -2, -0.6, -0.2, 0, 0.2, 0.1, -0.2, -0.4, -1, -3]
'''
готовой запас здоровья. сколько здоровья отнимется за год просто в процессе жизни, без всяких модификаторов 
цифра абстрактная, видимо может быть любой
'''
YEAR_HEALTH_AMOUNT = 365.0
# дневной запас здоровья. Вычисляется в зависимости от количества дней в году
HEALTH_PER_DAY = YEAR_HEALTH_AMOUNT / Date.DAYS_IN_YEAR
# для 4-х дней в году  HEALTH_PER_DAY = 91.25, каждый прожитый день будет отниматься столько

FERTILE_DELTA = STAGE_DICT[Stage_of_age.YOUNG] - STAGE_DICT[Stage_of_age.CHILD]

class Health:
    def __init__(self, person, age=ZERO_DATE):
        self.person = person
        # сколько еды удалось достать за ход
        self.have_food = 0
        # странная переменная. Нужна для статистики, чтобы показывватьь, сколько еды было у человека до перераспределения
        # то есть предполагается, что будет выводиться сравнение, сколько еды было изначально, и сколько стало по слеперераспределения. Но  перераспределений может быть несколько
        self.have_food_prev = 0
        # Определяем запас здоровья человека через его предполагаемый возраст.
        # Задаем его предполагаемый возраст смерти, отнимаем текущий возраст, переводим в дни и умнодаем на дневную норму очков жизни
        # определяем возраст смерти персоны (минимум: 55 - 48; максимум: 55 + 48)
        presume_life: Date = STAGE_DICT[Stage_of_age.AGED] + Date(prop.gauss_sigma_16())
        months: int = random.randrange(2 * Date.MONTHS_IN_YEAR) - Date.MONTHS_IN_YEAR #+- меяцев к жизни
        days: int = random.randrange(2 * Date.DAYS_IN_MONTH) - Date.DAYS_IN_MONTH #+- дней к жизни
        presume_life += Date(0, months, days)
        self.health: Date = presume_life - age # здоровье - это количество дней до смерти умноженных на коэффициент
        self.health: float = HEALTH_PER_DAY * float(self.health.len())  # здоровье это число, а не дата

        self.satiety = 5  # сытость. При рождении сытость нормальная.
        self.food_sum = 0

    def set_health(self, years):
        self.health: float = HEALTH_PER_DAY * float(Date(years).len())

    def have_food_change(self, number):
        """
        Изменяет количество добытой человеком еды на параметр number
        :param number: количество еды, на которе нужно изменить переменную  have_food
        """
        self.have_food_prev = self.have_food
        self.have_food += number
        self.have_food = self.have_food if self.have_food > 0 else 0

    def have_food_equal(self, number):
        """
        Присваивает человеку количество добытой еды =  number
        """
        self.have_food_prev = self.have_food
        self.have_food = number
        self.have_food = self.have_food if self.have_food > 0 else 0


    def ideal_food_amount(self):
        '''
        Определяем сколько бы человек хотел съетсть. Назанчение функции: распределение еды среди детей в семье.
        Чтобы ребенок не брал себе больше, чем ему нужно.
        У стариков коэффициент усвояемости больше единицы, таким образом они будут требовать  для себя больше пищи, мем им нужно
        Но концепция а том, мто старики так же едят обычную взрослую пайку, но еда усваивается хуже. Так что максимальный коэ всегда равноа единице, даже
        '''
        digest =  DIGEST_FOOD_MULTIPLIER[self.person.age.stage] if DIGEST_FOOD_MULTIPLIER[self.person.age.stage] < 1 else 1
        return NORMAL_CONSUME_RATE * FOOD_COEF * digest

    def modify(self):
        """
        общий метод для изменения здоровья в зависимости от множества факторов
        """
        # уменьшение здоровья за прожитый день (фиксированное количество)
        self.reduce()
        # голод
        abstinence_bonus = 0.2 * (self.person.genes.get_trait(GN.ABSTINENCE) - 5)  # чем меньше, тем хуже усваивается еда
        pregnancy_bonus = 0
        fertility_bonus = 0
        if self.person.age.is_big:
            # за свою половую энергию человек расплачивается жизнью
            # для мужчин трата энергии более выражена
            if self.person.gender is Gender.MALE:
                fertility_bonus = - 0.2 * (self.person.genes.get_trait(GN.FERTILITY) - 5)
            else:
                fertility_bonus = - 0.07 * (self.person.genes.get_trait(GN.FERTILITY) - 5)
                if self.person.pregnant:
                    pregnancy_bonus = -1
        # на основе количества пищи у человека и дополнительных факторов (в основном отрицательных) вычисляется его сытость
        # а на основе сытости человека вычисляется урон, наносимый здоровью
        # мало ест - сильный урон
        # также делим еду на возрастной коэффициент(пока маленьктй, легко питаться)
        fp = self.person.health.have_food / FOOD_COEF / DIGEST_FOOD_MULTIPLIER[self.person.age.stage] \
             + abstinence_bonus + fertility_bonus + pregnancy_bonus
        self.satiety = int(fp)
        self.satiety = self.satiety if self.satiety >= 0 else 0
        if self.satiety > 11:
            self.satiety = 11
            fp = 11
        self.satiety = min(self.satiety, 11)
        main_health_bonus = FOOD_BONUS[self.satiety]  # целая часть еды
        f_delta = FOOD_BONUS[self.satiety + 1] - FOOD_BONUS[self.satiety]
        additional_health_bonus = f_delta * (fp - self.satiety)  # дробная часть бонуса вычисленная по линейной пропорции
        self.food_sum = - HEALTH_PER_DAY * (main_health_bonus + additional_health_bonus)
        self.reduce(self.food_sum)

    def reduce(self, amount=HEALTH_PER_DAY):
        """
        Уменьшает здоровье человека. По умолчанию - на количество здоровья, отнимающееся за один прожитый день.
        """
        self.health = self.health - amount

    @property
    def is_zero_health(self):
        """
        Проверка на то, умер ли человек. Если здоровье равно или меньше нуля, то умер
        """
        return True if self.health <= 0.0 else False


def lust_coef(age):
    """
    с возрастом желание жениться пропадает
    хорошо бы описать это гладкой кривой, но я формулы не знаю, поэтому будет серия опорных точек
    """
    lust_checkpoints = [21, 26, 31, 37, 50]  # возраст
    lust_curve = [0.5, 0.6, 0.4, 0.3, 0.2]  # вероятность пожениться (вероятности пары перемножаются)
    attraction = 0.1
    for i in range(len(lust_checkpoints)):
        if age < lust_checkpoints[i]:
            attraction = lust_curve[i]
            break
    return attraction


def generate_genome()-> Dict[GN, int]:
    """
    Генерирует базовый геном: список целых чисел по длине генов. Этими числами будут инициироваться гены.
    Это не геном, а прототип генома.
    """
    genome: Dict[GN, int] = {i: random.randint(Gene.MIN_VALUE + 2, Gene.MAX_VALUE - 2) for i in GN}
    genome[GN.MUTATION] = 9
    return genome

class GN(str, Enum):
    ENHERITANCE = 'enheritance' # вероятность наследовать ген от предка своего пола
    FERTILITY = 'fertility' # плодовитость
    STRONGNESS = 'strongness' # приспособленность (лучше добывает пищу)
    ABSTINENCE = 'abstinence' # способность насытится малым
    EGOISM = 'egoism' # склонность к разводам
    ALTRUISM = 'altruism' # склонность отдавать часть еды родным
    FERT_AGE = 'fertile age' #  возраст деторождения
    FERT_SATIETY = 'fertile satiety' # определяет минимальную сытость, при которой невозможно зачать ребенка
    MUTATION = 'mutation' # параметр, влияющий на вероятность мутации одного гена, а прогон идет по всем генам


class Genes:
    '''
    Геном человека. Словарь генов.
    Содержит методы инициации генома для младенца и для странника (взрослого человека без предков,
    от которых можно было наследовать гены).
    '''
    protogenome_profile = {GN.ENHERITANCE: 9,  # наследование генов
                           GN.FERTILITY: 5,  # плодовитость
                           GN.STRONGNESS: 5,  # приспособленность
                           GN.ABSTINENCE: 5,  # умеренность
                           GN.EGOISM: 5,  # неуживчивость
                           GN.ALTRUISM: 6,  # альтруизм
                           GN.FERT_AGE: 5,  # возраст деторождения
                           GN.FERT_SATIETY: 3,  # сытость, при которой невозможно зачать ребенка
                           GN.MUTATION: 3}  # вероятность мутации


    GEN_PSEUDONYM = {GN.ENHERITANCE:'enhr',
                     GN.FERTILITY: 'fert',
                     GN.STRONGNESS: 'stro',
                     GN.ABSTINENCE:'abst',
                     GN.EGOISM: 'ego ',
                     GN.ALTRUISM: 'altr',
                     GN.FERT_AGE: 'fage',
                     GN.FERT_SATIETY: 'fsat',
                     GN.MUTATION: 'muta'}

    def __init__(self, person: Genes_Holder):
        self.person: Genes_Holder = person
        self.genome: Dict[GN, Gene] = {i: Gene(i, self) for i in GN}

    @classmethod
    def init_protogenome(cls):
        """
        В начале симуляции случайным образом создает шаблон генома для всей популяции.
        Для людей первого поколения, а так же для странников - взрослых людей, периодически
        приходящих в социум.
        """
        cls.protogenome_profile = generate_genome()

    def define(self):
        """
        Определяет геном новорожденного. Вызывается из класса Fetus при зачатии, так что не стоит
        опасаться , что к моменту рождения у ребенка сменится отец и гены отнаследуюстя от чужого дяди.
        Проводит инициацию каждого гена, который наследуется от одного из родителей и с некоторой
        вероятностью модифицируется.
        """
        for i in self.genome.values():
            i.init_gene()

    def define_adult(self):
        """
        Применяет шаблон генома всей популяции (протогеном) для странника (взрослого человека).
        Гены не наследуются при этом, а инициализируются числами из протогенома.
        """
        for i in GN:
            val = self.protogenome_profile[i]
            self.genome[i].value = val
            self.genome[i].pred_value = val


    def transit(self, person: human.Human):
        """
        Копирует геном из эмбриона в целевого человека, когда тот рождается
        Метод вызывается из класса Fetus
        """
        for i in self.genome:
            person.genes.genome[i] = self.genome[i]

    def get_trait(self, trait):
        """
        Возвращает значение гена из словаря генома
        """
        return self.genome[trait].value

    def difference(self, other):
        '''
        Количественная разница генома с другим геномом.
        '''
        d = 0
        for i in GN:
            d +=abs(self.genome[i].value - other.genome[i].value)
        return d


class Gene:
    MIN_VALUE = 0
    MAX_VALUE = 11
    def __init__(self, name: GN, genome: Genes, value: int=5):
        self.name: GN = name
        self.containing_genome: Genes = genome
        self.person: Genes_Holder = genome.person
        self.value: int = value
        self.predecessor: Optional[human.Human] = None # ссылка на родителя, от которого унаследован конкретный ген

    def init_gene(self):
        #  ген "наследование" наследуется только от родителя того же пола. От отца к сыну, от матери к дочери.
        # этот ген определяет вероятность того, что другие гены будут копироваться по половой линии
        if self.name == GN.ENHERITANCE:
            self.inherit_gene(self.person.biological_parents.same_gender_parent(self.person))
        else: # остальные гены с вероятностью, зависящей от "наследование" могут быть унаследованы от любого из родителей
            self.inherit_any_gene()

        self.pred_value = self.predecessor.genes.get_trait(self.name)
        self.gene_score()


    def inherit_any_gene(self,  gene_value=5):
        """
        Случайно определяем, от кого из родителей будет копироваться данный ген
        """
        if random.random() < 1 / (self.person.genes.get_trait(GN.ENHERITANCE) + 1):
            parent = self.person.biological_parents.opposite_gender_parent(self.person)
        else:
            parent = self.person.biological_parents.same_gender_parent(self.person)
        self.inherit_gene(parent, gene_value)

    def inherit_gene(self, parent,  default=5):
        self.predecessor = parent
        def trait_limit(trait):
            if trait > Gene.MAX_VALUE:
                trait = Gene.MAX_VALUE
            if trait < Gene.MIN_VALUE:
                trait = Gene.MIN_VALUE
            return trait
        self.value = trait_limit(self.mutate_gene())

    def mutate_gene(self) -> int:
        shift: float = 0 # величина мутации
        # при mutation  = 11 шанс у гена мутировать: 0.444 (каждый человек мутант гарантированно)
        # при mutation  = 0 шанс у гена мутировать: 0.02 (мутирует каждый 0.02*len(GENOME) человек)
        mutation_chance: float = 4 / (14 - self.predecessor.genes.get_trait(GN.MUTATION)) ** 2
        if mutation_chance > random.random():
            shift = 0.45 * prop.gauss_sigma_1() # величина мутации
            if shift < 0:
                shift -= 1 # если мутация случилась, то ее величина  должна быть больше или меньше единицы,
            if shift >= 0: # иначе при округлении эффект мутации равен нулю
                shift += 1
        trait = round(self.predecessor.genes.get_trait(self.name) + shift)
        return trait

    def gene_score(self):
        # очки за изменение генов. Изменения в любую сторону, лишь бы значительные
        gene_delta = abs(self.value - self.pred_value)
        if gene_delta > 0:
            self.person.score.update_gene(gene_delta)



# при максимальном альтруизме вкадывает в семейный бюждет всю  еду. При минимальном - нисколько.
ALTRUISM_COEF = 1/Gene.MAX_VALUE



if __name__ == '__main__':
    # тестирование коэффициента привлекательности (который зависит от возраста)
    for i in range(20):
        x = random.randrange(15, 60)
        attract = lust_coef(x)
        print("%d - %4f" % (x, attract))

    print('================================')
    print('Считаем фертильный возраст:')
    print(f'промежуток в годах:{FERTILE_DELTA.display(False)}')
    print(f'между {STAGE_DICT[Stage_of_age.CHILD].display(False)} и {STAGE_DICT[Stage_of_age.YOUNG].display(False)}')
    for i in range(Gene.MAX_VALUE):
        fage = STAGE_DICT[Stage_of_age.CHILD] + FERTILE_DELTA * (i/Gene.MAX_VALUE)
        print(f'ген: {i}, возраст: {fage.display(False)}')
