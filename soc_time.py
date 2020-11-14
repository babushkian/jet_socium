
"""
Модуль, определяющий формат даты а так же параметры времени по которому живет социум живет.
А так же всякие сложение-вычитание дат, вычисление периодов времени

"""

class Date:
    MONTHS_IN_YEAR =4
    DAYS_IN_MONTH = 1
    DAYS_IN_YEAR = MONTHS_IN_YEAR * DAYS_IN_MONTH
    def __init__(self, year=0, month=0, day=0):
        """
        месяцы и дни начинаются с нуля. Просьба писать на один меньше
        если в переменной указано, что в месяце 30 дней, то последняя цифра: 29
        """
        self.day = day
        self.month = month
        self.year  = year
        self.nornalize()

    def display(self, date=True):
        if date:
            d = "Год: %d" % self.year
            if self.MONTHS_IN_YEAR>1:
                d += "  мес: %d" % self.month
            if self.DAYS_IN_MONTH>1:
                d += "  день: %d" % self.day
        else:
            d = "%d лет" % self.year
            if self.MONTHS_IN_YEAR>1:
                d += ", %d мес" % self.month
            if self.DAYS_IN_MONTH>1:
                d += ", %d дней" % self.day
        return d


    def	years_float(self):
        return self.len() / self.MONTHS_IN_YEAR / self.DAYS_IN_MONTH


    def len(self):
        years_score = self.year * self.MONTHS_IN_YEAR * self.DAYS_IN_MONTH
        months_score = self.month * self.DAYS_IN_MONTH
        return self.day + months_score + years_score


    def nornalize(self):
        day = self.day
        month = self.month
        year = self.year
        self.day = day % self.DAYS_IN_MONTH
        self.month = day // self.DAYS_IN_MONTH + month
        self.year  = self.month // self.MONTHS_IN_YEAR + year
        self.month %= self.MONTHS_IN_YEAR


    def create(self):
        """
        Создает новый объект даты с теми же числами. Это просто копирование даты
        в ноавй объект.
        """
        return Date(self.year, self.month, self.day)


    def __hash__(self):
        return self.len()

    def __eq__(self, other):
        return self.len() == other.len()

    def __gt__(self, other):
        return self.len()> other.len()

    def __lt__(self, other):
        return self.len() < other.len()

    def __add__(self, other):
        x = self.day + other.day
        y = self.month + other.month
        z = self.year + other.year
        return Date(z, y, x)


    def __sub__(self, other):
        x = self.day - other.day
        y = self.month - other.month
        z = self.year - other.year
        return Date(z, y, x)

    def year_starts(self):
        if self.month % self.MONTHS_IN_YEAR == 0 and self.day % self.DAYS_IN_MONTH ==0 :
            return True
        else:
            return False

class Anno(Date):
    def time_pass(self):
        self.day +=1
        self.nornalize()



ZERO_DATE = Date()
YEAR = Date(1,0,0)
TIK = Date(0,0,1)
FAR_FUTURE = Date(100000,0,0)

if __name__ == '__main__':
    Date.MONTHS_IN_YEAR =1
    Date.DAYS_IN_MONTH = 1
    print("В году 1 месяц а в месяце 1 день")

    a = Date(1800, 0, 0)
    c  = a.create()
    d = Date(1801, 0, 0)
    print(a.display())
    print(c.display())
    print("Равны ли две даты?")
    print(c == a)
    print("Равны ли даты A и D?")
    print("A =", a.display())
    print("D =", d.display())
    print(a == d)
    s= a<d
    print("A меньше D? %s" % s)
    s= d > a
    print("D больше A? %s" % s)

    print("Сумма дат A и D:")
    x= a+d
    print(x.display())
    print("Прибавляем к A 1 год")
    x = a+ Date(1)
    print(x.display())
    print("прибавим 1 день, что должно быть идентично прибавлению 1 года")
    x = x + Date(0, 0, 1)
    print(x.display())
    print("Нормализуем:")
    x.nornalize()
    print(x.display())
    Date.MONTHS_IN_YEAR = 12
    Date.DAYS_IN_MONTH = 30
    print("Изменяе мпараметры года с упрощенных на человеческие")
    print("В году 12 месяцев, а в месяце 30 дней")
    print("прибавляем к дате 16 месяцев")
    x += Date(0, 16, 0)
    print(x.display())
    print("16 месяцев будет у нас")
    print(Date(0,16,0).display())
    print("Отнимем от A C")
    x -= d
    print(x.display())
    print("Еще отнимем год и 3 дня")
    x -= Date(1, 0, 3)
    print(x.display())
    print("Отнимаем полный ноль от ", a.display())
    x = a- Date(0,0,0)
    print(x.display())
    print("И ничего не онимается")
    print("Создадим адское количество дней: 1456")
    y = Date(0, 23, 30 )
    print(y.display())

    print("Отрицаиельное количество дней и месяцев Date(50, -1, -29)")
    y = Date(50, -1, -29)
    print(y.display())

    print("Отнимание двух дат")
    print(x.display())
    print(y.display())
    t = x-y
    print("Результат:")

    print(t.display())
    for i in range(Date.DAYS_IN_MONTH+1):
        t+=Date(0,0,1)
        print(i, " - ",t.display())

    print("========")

    for i in range(Date.DAYS_IN_MONTH+1):
        t-=Date(0,0,1)
        print(i, " - ",t.display())
    print((t+x).display())
    print((Date(1820, 5,17)).display())

