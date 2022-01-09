from __future__ import annotations
import random
from typing import Optional, List, Dict, Any, Set



from common import (DIGEST_FOOD_MULTIPLIER,
                    Gender,
                    opposite_gender)
import human

import genetics


class Family:
    """
    Поисываеится семья и внутрисемейные отношения. Свадьба развод, смерти супругов, уход из семьи взрослых детей.
    Ну и конечно дележка совместно нажитой пищи.

    Если в семье отдельно выделяется роль главы семьи, то неплохо было бы назначить какую то обязанность,
    характерную только для главы семьи. Которой остальные домочадцы не занимаются.
    """
    family_log_file = None
    family_food_file = None
    family_feeding = None

    def __init__(self, head: human.Human,  # человек
                 depend: Optional[List[human.Human]] = None):  # список иждивенцев
        """
        Создается новая семья. Это происходит в случаях: 1) добавления странника в социум; 2) при разводе;
        3) когда ребенок взрослеет и уходит из семьи; 4) когда у детей умирают все кормильцы
        Если создается семья с дополнительным параметром dependents - это значит жена ушла от мужа с детьми
        (от этого и от предыдущих браков). Мужчина при разводе не забирает с собой детей.
        При объединении семей, жена и дети автоматически меняют свое племя на значение племени главы семьи.
        При разводе жена вспоминает свое изначальное племя tribe_origin - племя последней семьи, в которой
        она воспитывалась. Параметр tribe_origin присваивается только когда ребенок основывает собственную
        семью (когда повзрослеет или осиротеет)
        """
        self.obsolete: bool = False  # признак того, сто семья перестала существовать
        self.id: str = self.generate_family_id()
        # в семье должен быть хотя бы один человек - глава. В начале симуляции все дети получают
        # собственную семью, как и дети-сироты после смерти родителей, как и повзрослевшие дети, покидающие семью
        self.head: human.Human = head
        self.head.socium.families.append(self)  # добавляет семью в список семей
        # если человек холостой, husband  и wife равны None. После свадьбы, этим переменным назначаются конкретные люди
        self.husband: Optional[human.Human] = None
        self.wife: Optional[human.Human] = None
        self.all: List[human.Human] = [self.head]  # все члены семьи кроме стариков, которые и так не члены семьи
        # список детей (не обязательно родных, а пришедших в семью вместе с новым супругом. Иждивенцы, короче.)
        self.dependents: List[Optional[human.Human]] = list()

        if self.head.biological_parents.mother.is_human:
            self.tribe_id = self.head.family.tribe_id
        else:
            self.tribe_id = self.id
        # при добавлении иждивенцев в семью, они наследуют племя главы семьи
        if depend:
            for i in depend:
                self.add_child(i)
        self.food = FamilySupplies(self)
        s = f'Новая семья: {self.id}| {self.head.name.display()}| {self.head.id}| возраст - {self.head.age.year} лет.\n'
        self.family_log_file.write(s)

    @classmethod
    def init_files(cls):
        cls.family_log_file = open("./families.log", "w", encoding="utf16")
        cls.family_food_file = open("./family_food_distrib.log", "w", encoding="utf16")
        cls.family_feeding = open("./family_feeding.log", "w", encoding="utf16")

    @classmethod
    def close(cls):
        cls.family_log_file.close()
        cls.family_food_file.close()
        cls.family_feeding.close()

    @staticmethod
    def generate_family_id() -> str:
        ALFABET = ('BBCCDDFFGHJKLKLMMNPQRSTPQRRSSTVWXZ', 'AEIAEEIOOUY')
        id = ''
        while len(id) < 7:
            for l in range(2):
                for sec in range(round(random.random() * .75) + 1):
                    id += ALFABET[l][random.randrange(len(ALFABET[l]))]
        return id[:7]

    def adults_dict(self) -> Dict[Gender, Optional[human.Human]]:
        '''
        Выдает словарь взрослых членов семьи по ключу "пол". Вместо отсутствущего члена семьи выдается
        None. Сначала идет self.head, так как эта позиция просто не может быть пустой (разве что когда
        глава семьи внезапно умер). Если self.head женского пола, значит жены у нее точно нет. Если
        мужского - возможно, есть.
        '''
        gs = [self.head.gender, opposite_gender(self.head.gender)]
        return {g: a for g, a in zip(gs, [self.head, self.wife])}


    def add_child(self, person: human.Human):
        self.dependents.append(person)
        self.all.append(person)
        person.family = self
        person.social_parents.update(self)
        return len(self.dependents)


    def add_dependents(self, family: Family):
        '''
        При замужестве добавляем всех детей жены от предыдущего брака в список иждивенцев главы семьи
        Отец их усыновляет.
        '''
        for i in family.dependents:
            if not i.age.is_big:
                i.name.change_fathers_name(self.head) # менем отчество
                i.name.change_family_name(self.head) # меняем фамилию ребенка
                self.add_child(i)


    def unite_families(self, wifes_family: Family):
        '''
        добавляем жену в семью мужа. Семья жены уничтожается
        объединяем иждивенцев жены и мужа в переменную self.dependents
        у жены удаляются родители прежнего мужа
        '''
        s = "Объединились семьи:\n"
        s += "\t %s| %s| %s\n" % (self.id, self.head.id, self.head.name.display())
        s += "\t %s| %s| %s\n" % (wifes_family.id, wifes_family.head.id, wifes_family.head.name.display())
        self.family_log_file.write(s)
        self.wife: human.Human  = wifes_family.head
        self.husband: human.Human  = self.head
        self.wife.name.change_family_name(self.head)  # меняем фамилию жены
        self.all.append(self.wife)
        self.add_dependents(wifes_family)
        self.family_disband(wifes_family)
        self.wife.family = self


    def divide_families(self):
        '''
        происходит развод: разделение на две семьи
        у жены генерится новая семья, дети к своему отцу перестают иметь отношение, переходят в семью матери

        '''
        s = "=======Семья | %s | распалась\n" % self.id
        s += "\t %s| %s\n" % (self.head.id, self.head.name.display())
        s += "\t %s| %s\n" % (self.wife.id, self.wife.name.display())
        self.family_log_file.write(s)
        children = self.dependents[:] # передаем содержимое, а не объект
        self.wife.family = Family(self.wife, children)
        self.wife.family.tribe_id = self.wife.tribe_origin
        # мужчина бросает всех иждивенцев на жену
        self.dependents = []
        # родители разделяются на линии жены и мужа
        # никто ничей муж и не жена, только главы семьи
        self.husband = None
        self.wife = None
        self.all = [self.head]

    def family_disband(self, family: Family):
        '''
        Уничтожение семьи происходит в двух случаях:
        1) при свадьбе семья жены уничтожается - жена с иждивенцами переходит в семью мужа
        2) при смерти холостого главы семьи. Иждивенцы не наследуют его семью, а создают собственные
        '''
        family.obsolete = True
        family.head = None
        family.husband = None
        family.wife = None
        family.all = []
        family.dependents = []

    def dead_in_family(self, person: human.Human):
        '''
        Вызывается, когда в семье кто-то умирает. Не важно, кто: родитель или ребенок. В зависимости
        от тго, кто умер, метод вызывает другие методы. Вызывается из объекта human.Human.
        '''
        if person not in self.dependents:
            # проверяем наличие роли супруга. Если есть wife, то и husband должен быть.
            if self.wife: # при проверке нельзя применять person.married(), так как в person.die супруг уже убран
                self.spouse_dies(person)
            else: # человек без пары - семья распадается (дети начинают жить самостоятельно)
                self.orphane_family()
        else:
            self.child_dies(person)

    def spouse_dies(self, person: human.Human):
        '''
        Вызывается, если умирает один из супругов в полной семье. То есть наличие второго супруга
        подразумевается.
        Когда супруг умирает, семья сохраняется
        Списки родителей и иждивенцев остаются без изменения
        Родители умершей жены остаются на попечении вдовца. И наоборот.
        Если умирает супруг, жена становится главой семьи
        '''
        if person == self.head:
            s ="\nВ семье |%s|  умер супруг |%s| %s\n"% (self.id, self.head.id, self.head.name.display())
            self.all.remove(self.head)
            self.head = self.wife
            self.husband = None
            self.wife = None
            s += "Теперь |%s| %s глава семьи.\n" % (self.head.id, self.head.name.display())
        else:
            s = "\nВ семье |%s|  умерла супруга |%s| %s\n" % (self.id, self.wife.id, self.wife.name.display())
            self.all.remove(self.wife)
            self.husband = None
            self.wife = None
        for i in self.dependents:
            i.social_parents.check_parents_alive()

        self.family_log_file.write(s)

    def orphane_family(self):
        '''
        Умирает последний (или единственный) взрослый представитель семьи
        если у детей не остается ни одного родителя, они становятся главами своих собственных семей
        '''
        if len(self.dependents) > 0:
            s = "%s| %s из семьи |%s| умер, оставив несовершеннолетних детей.\n" % (self.head.id, self.head.name.display(), self.id)
            for i in self.dependents:
                i.tribe_origin = self.tribe_id
                i.social_parents.check_parents_alive()
                i.family = Family(i)
        else:
            s = "%s| %s из семьи |%s| умер в одиночестве.\n" % (self.head.id, self.head.name.display(), self.id)
        self.family_log_file.write(s)
        self.family_disband(self)

    def child_dies(self, person: human.Human):
        '''
        В семье умирает ребенок
        '''
        self.dependents.remove(person)
        person.social_parents.finish_parents_death()
        self.all.remove(person)

    def del_grown_up_children(self):
        '''
        Когда ребенок взрослеет, он исключается из состава семьи. Он сам становится новой семьей.
        Вызывается каждый ход в главном цикле объекта socium
        '''
        too_old =[]
        for i in self.dependents:
            if i.age.is_big:
                too_old.append(i)
        if len(too_old) > 0:
            for i in too_old:
                self.dependents.remove(i)
                self.all.remove(i)
                # запоминаем племя, в котором вырос ребенок, так как tribe_id по жизни может меняться
                i.tribe_origin = self.tribe_id
                i.social_parents.finish_parents_grow_up()
                i.family = Family(i)


    def live(self):
        '''
        Альтернативный метод, двигающий людей по жизни. в отличие от голбального цикла по людям, в
        socium перебираются семьи, а в семье уже перебираются люди.
        К сожалению, этот метод работает некорректно, не знаю, почему.
        '''
        for i in self.all:
            i.live()


    def print_something(self, some):
        some += "\n"
        self.family_log_file.write(some)


    def print_family(self) -> None:
        self.family_log_file.write(self.family_info())


    def family_info(self) -> str:
        strok = f'===========\nСемья: {self.id}\n'
        strok += f'\tГлава:  {self.head.id}| {self.head.name.display()}\n'
        if self.wife:
            strok += f'\tЖена:   {self.wife.id}| {self.wife.name.display()}\n'
        if len(self.dependents)>0:
            strok += f'\tДети:  \n'
            for i in self.dependents:
                strok += f'\t\t{i.id}| {i.name.display()}\n'
        return strok + '\n'


    def get_family_role_sting(self, person:human.Human) -> str:
        '''
        Возвращает роль человека в семье: глава, жена или ребенок
        '''
        if person is self.head:
            s = ' глав'
        elif person is self.wife:
            s = ' жена'
        elif person in self.dependents:
            s = ' чадо'
        else:
            raise Exception('Определение роли человека в семье: неизвестная роль.')
        return s

    def display(self):
        s = '==================================\n'
        s += f'семья:{self.id} племя: {self.tribe_id} статус:{not self.obsolete} \n'
        for nam, person in zip(['head', 'husband', 'wife'], [self.head, self.husband, self.wife]):
            if person is not None:
                s += f'{nam:>7s}: {person.id}| {person.gender.value:6s}| fam:{person.family.id}| orig:{person.tribe_origin}| age: {person.age.display()}\n'
            else:
                s += f'{nam:>7s}: None\n'
        print('---------------------')


        for pers in self.all:
            s += f'{pers.id}| {pers.gender.value:6s}| fam:{pers.family.id}| orig:{pers.tribe_origin}| age: {pers.age.display()}\n'
        return s


class FamilySupplies:
    '''
    Формирует и распределяет семейный бюджет
    '''
    def __init__(self, family:Family):
        self.family = family
        self._supplies = 0.0
        self.budget = 0.0

    def make(self):
        '''
        Пополняем семейный бюджет.
        Каждый член семьи вкладывает в бюджет долю, пропорциональную его альтруизму. Долю от
        имеющихся у него запасов, полученных после первоначальной добычи пищи
        '''
        # возможность переносить запасы на следующий ход пока не делаю
        self._supplies = 0
        give_members:Dict[human.Human, float] = dict()
        for member in self.family.all:
            # каждый член семьи вкладывает в бюджет долю, пропорциональную его альтруизму
            give = member.health.have_food * genetics.ALTRUISM_COEF * member.genes.get_trait(genetics.GN.ALTRUISM)
            member.health.have_food_change(-give)
            self._supplies += give
            give_members[member]=give
        self.make_food_rec(give_members)

    def _calculate_portions(self, fam_list: List[human.Human]) -> Dict[human.Human, float]:
        '''
        fam_list - оставшиеся члены семьи, для которых еще не посчитаны пропорции распределения бюджета
        Считаем распределение еды на всех членов семьи. В какой пропорции нужно поделить еду на
        членов семьи, переданных в переменной fam_list. При распределении еды члены семьи выбывают
        по одному. Функция может быть вызвана повторно: если кому то его доля покажется слишком
        большой и он не будет брать ее целиком.
        '''
        # доля еды из семейного бюджета на каждого человека.
        # Сначала вычисляются абсолютные значения еды, но потом нормализуются по denominator
        portions: Dict[human.Human, float] = dict()
        denominator = 0
        for member in fam_list:
            # нужно учитывать, что старики плохо уствивают пищу и для насыщения им нужно больше, они будут получать, как взрослые, не бльше 1
            age_proportion = min(DIGEST_FOOD_MULTIPLIER[member.age.stage], 1)
            # опасная штука, если EGOISM==0, может статься, что denominator==0 и деление на ноль, поэтому нужно небольшое смещение
            egoism_proportion = 0.1 + member.genes.get_trait(genetics.GN.EGOISM) / genetics.Gene.MAX_VALUE
            #part = age_proportion + egoism_proportion
            part = egoism_proportion
            portions[member] = part
            denominator += part
        for member in fam_list:
            portions[member] = portions[member] / denominator
        return portions


    def old_ones(self)->Set[human.Human]:
        '''
        Возвращаем множество живых стариков, чтобы покормить их
        '''
        family_parents = set()
        for member in [self.family.head, self.family.wife]:
            if member is not None:
                for p in member.social_parents.last_parents:
                    if p.is_alive:
                        family_parents.add(p)
        return family_parents

    def distribute(self):
        # Новая концепция, попробовать кормить детей так, чтобы у всех детей сытость была на одном уровне примерно
        # а потом о родителях думать
        '''
        Распределение пищи между членами семьи
        Если для одного еды слишком много, оставшаяся от него еда перераспределяется между
        оставшимися членами семьи
        Если после всех членов семьи остается еда ...
        '''
        members_list = self.family.all.copy()
        # первоначальный расчет пропорций, как делить общую пайку. Если кому-то из семьи доля будет
        # слишком большой для оставшейся семьи пропорции будут рассчитываться снова
        # и членов семьи будет меньше и пайка будет уменьшена за счет предыдущего человека, забравшего свою долю
        # Доля вычисляется в процентах от пайки, а потом переводится в абсолютную величину сравнивается
        # с идеальной порцией еды.  При окончательном подсчете абсолютные порции у членов семьи опять
        # переводятся в проценты пля показа окончательного соотношения
        portions = self._calculate_portions(members_list)
        # пища, уже отданная из общих запасов кому-то из семьи
        given_away_food = 0.0
        # Выкидываем из списка семьи одного человека и для него рассчитываем порцию
        # и так для каждого человека
        while len(members_list)>0:
            member = members_list.pop()
            supplies_share = self._supplies * portions[member] # доля человека из общих запасов
            # личный запас плюс доля от семейных запасов, то, что положено человеку
            temp_food = member.health.have_food + supplies_share
            ideal_food = member.health.ideal_food_amount()
            # берет, что положено или добивает до идеальной порции
            get_food  = min(supplies_share, ideal_food - member.health.have_food)
            member.health.have_food_change(get_food)
            given_away_food += get_food # общее количество разобранной еды пополняется порцией конкретного человека

            # если положенная порция у человека больше идеальной, он всю ее не съедает
            # а берет из общака ровно столько, чтобы добить до идеальной
            # из-за этого остальные пропорции нарушаются, и надо пересчитывать их заново уже для
            #  поэтому сбрасываем переменную self._supplies и рассчитываем для уменьшенной семьи новые пропорции
            if temp_food > ideal_food and len(members_list) > 0:
                self._supplies -= given_away_food
                given_away_food = 0
                portions = self._calculate_portions(members_list)
        self._supplies -= given_away_food


        if self._supplies > 10: # если цифра меньше, стариков не кормим, просто раскидываем между членами семьи
            family_parents = self.old_ones()
            lfp = len(family_parents)
            if lfp > 0:
                food_per_parent = self._supplies / lfp
                for par in family_parents:
                    par.health.have_food_change(food_per_parent)
                self._supplies = 0

        if self._supplies > 0.1: # распределять микроскопические остатки бессмысленно, согласен на потери
            portions = self._calculate_portions(self.family.all)
            for member in self.family.all:
                member.health.have_food_change(self._supplies * portions[member])




    def distribute_disp(self):
        # Новая концепция, попробовать кормить детей так, чтобы у всех детей сытость была на одном уровне примерно
        # а потом о родителях думать
        '''
        Распределение пищи между членами семьи
        Если для одного еды слишком много, оставшаяся от него еда перераспределяется между
        оставшимися членами семьи
        Если после всех членов семьи остается еда ...
        '''
        members_list = self.family.all.copy()
        # первоначальный расчет пропорций, как делить общую пайку. Если кому-то из семьи доля будет
        # слишком большой для оставшейся семьи пропорции будут рассчитываться снова
        # и членов семьи будет меньше и пайка будет уменьшена за счет предыдущего человека, забравшего свою долю
        # Доля вычисляется в процентах от пайки, а потом переводится в абсолютную величину сравнивается
        # с идеальной порцией еды.  При окончательном подсчете абсолютные порции у членов семьи опять
        # переводятся в проценты пля показа окончательного соотношения
        portions = self._calculate_portions(members_list)

        s = self.display_distr_header(portions)

        # пища, уже отданная из общих запасов кому-то из семьи
        given_away_food = 0.0
        distributed_food: Dict[human.Human, float] = dict()
        display_main_struct: Dict[human.Human, Dict[str, Any]]  = dict()
        # Выкидываем из списка семьи одного человека и для него рассчитываем порцию
        # и так для каждого человека
        while len(members_list)>0:
            member = members_list.pop()
            supplies_share = self._supplies * portions[member] # доля человека из общих запасов
            # личный запас плюс доля от семейных запасов, то, что положено человеку
            temp_food = member.health.have_food + supplies_share
            ideal_food = member.health.ideal_food_amount()
            # берет, что положено или добивает до идеальной порции
            get_food  = min(supplies_share, ideal_food - member.health.have_food)
            member.health.have_food_change(get_food)
            distributed_food[member] = get_food # то, что человек уже взял из общих запасов
            given_away_food += get_food # общее количество разобранной еды пополняется порцией конкретного человека
            rest_of_food =  self._supplies - given_away_food # остаток пайка только в целях вывода на экран

            display_main_struct[member] = {'врем доля':temp_food}
            display_main_struct[member]['идеал доля'] = ideal_food
            display_main_struct[member]['взято еды'] = get_food
            display_main_struct[member]['остаток припасов'] = rest_of_food
            display_main_struct[member]['пересчет пропорций'] = dict()

            # если положенная порция у человека больше идеальной, он всю ее не съедает
            # а берет из общака ровно столько, чтобы добить до идеальной
            # из-за этого остальные пропорции нарушаются, и надо пересчитывать их заново уже для
            #  поэтому сбрасываем переменную self._supplies и рассчитываем для уменьшенной семьи новые пропорции
            if temp_food > ideal_food and len(members_list) > 0:
                self._supplies -= given_away_food
                given_away_food = 0
                portions = self._calculate_portions(members_list)
                display_main_struct[member]['пересчет пропорций'] = portions
        self._supplies -= given_away_food

        s += self.display_distr_main_round(display_main_struct)

        if self._supplies > 10: # если цифра меньше, стариков не кормим, просто раскидываем между членами семьи
            family_parents = self.old_ones()
            lfp = len(family_parents)
            if lfp > 0:
                food_per_parent = self._supplies / lfp
                for par in family_parents:
                    par.health.have_food_change(food_per_parent)
                self._supplies = 0
                s += self.display_feed_olds(food_per_parent, lfp)

        if self._supplies > 0.1: # распределять микроскопические остатки бессмысленно, согласен на потери
            portions = self._calculate_portions(self.family.all)
            for member in self.family.all:
                member.health.have_food_change(self._supplies * portions[member])
                distributed_food[member] += self._supplies * portions[member]

            s += self.display_spend_leftovers(portions)
            self._supplies = 0
        s += self.display_final(distributed_food)
        self.family.family_feeding.write(s)

    @property
    def supplies(self):
        return self._supplies

    def change_supplies(self, amount):
        self._supplies += amount


    def make_food_rec(self, portions ):
        def form_text_body(member, give) ->str:
            s = f'{self.family.get_family_role_sting(member):6s}| {member.id}|'
            s += f' alt={self.family.head.genes.get_trait(genetics.GN.ALTRUISM):2d}| имеет {member.health.have_food_prev:5.1f}| ' \
                 f'вкладывает {give:5.1f}| остается {member.health.have_food:5.1f}\n'
            return s
        pref = f'{self.family.head.socium.anno.year}:{self.family.head.socium.anno.month}| {self.family.id}|'
        s = pref +"-------------\n"
        for member in portions:
            s += pref + form_text_body(member, portions[member])
        s = s + pref + " Всего запас: %6.1f\n" % self._supplies
        Family.family_feeding.write(s)



    def family_food_display(self, message: str=''):
        fam_pref = f'{self.family.id}|'
        pref = f'{fam_pref}================={message}\n'
        Family.family_food_file.write(pref)

        pref = f'{self.family.head.socium.anno.year}:{self.family.head.socium.anno.month}| {fam_pref}'
        self.budget = 0
        budget_prev = 0
        for i in self.family.all:
            self.budget += i.health.have_food
            budget_prev += i.health.have_food_prev
            role = self.family.get_family_role_sting(i)
            s = pref + f'{role}| {i.health.have_food:5.1f}| {i.health.have_food_prev:5.1f}| непонятная фигня {int(i.health.have_food/genetics.FOOD_COEF):2d}\n'

            Family.family_food_file.write(s)
        b = "Бюждет до %6.1f  после %6.1f \n" % (budget_prev, self.budget)
        Family.family_food_file.write(pref + b)

    @property
    def rec_prefix(self):
        return f'{self.family.head.socium.anno.year}:{self.family.head.socium.anno.month}| {self.family.id}|'

    def display_distr_header(self, portions):
        pref = self.rec_prefix
        s ='\n'+ pref +"---- питание ---------\n"
        s = s+ pref +"Запасы: %6.1f\n" % self._supplies
        s +=  pref + f'Первоначальное распределение:\n'
        for member in self.family.all:
            s = s + pref + f'\t{self.family.get_family_role_sting(member):6s}({member.age.year:3d})| {member.id}| {portions[member] * 100:4.1f}% - {self._supplies * portions[member]:5.1f} еды \n'
        return s

    def display_distr_main_round(self, md):
        pref = self.rec_prefix
        s =''
        for member in md:
            mmd = md[member]
            s += pref + f'{self.family.get_family_role_sting(member):6s}| {member.id}|'
            s += f" доля: {mmd['врем доля']:5.1f}| идеально: {mmd['идеал доля']:5.1f}"
            s += f" взято из запасов: {mmd['взято еды']:5.1f}| остаток: {mmd['остаток припасов']:6.1f}|\n"
            l = len(mmd['пересчет пропорций'])
            if l > 0:
                per = mmd['пересчет пропорций']
                s += pref + f'\tПЕРЕРАССЧЕТ ({l} членов семьи):\n'
                for mem in per:
                    s += pref + f'\t{self.family.get_family_role_sting(mem)} {per[mem]:5.3f}\n'
                s += '\n'
        leftovers = self._supplies if self._supplies> 1e-3 else 0.0
        s += f'{self.family.id}| осталось запасов:{leftovers:6.2f}\n'
        return s

    def display_feed_olds(self, food_per_parent:float, lfp:int)->str:
        return self.rec_prefix + f'КОРМИМ СТАРИКОВ: {lfp} человека, каждому по {food_per_parent:5.1f} еды\n'

    def display_spend_leftovers(self, portions) -> str:
        s =  self.rec_prefix + f'\tРАСПРЕДЕЛЯЕМ ОСТАТКИ: \n'
        for member in self.family.all:
            s += self.rec_prefix + f'\t{self.family.get_family_role_sting(member):6s}| {member.id}| ' \
                    f'{portions[member] * 100:4.1f}% - {self._supplies * portions[member]:5.2f} еды \n'
        return s

    def display_final(self, distributed_food) -> str:
        s =  self.rec_prefix + f'окончательное распределение:\n'
        sum_dist_food = sum(distributed_food.values()) # если ребенок остается один, у него может отсутствовать еда
        for member in self.family.all:
            persent = distributed_food[member]/sum_dist_food * 100 if sum_dist_food > 0 else 0
            s += self.rec_prefix + f'\t{self.family.get_family_role_sting(member):6s}({member.age.year:3d})| {member.id}| {persent:4.1f}% - {distributed_food[member]:5.1f} еды \n'
        return s


