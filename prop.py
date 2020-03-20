# приближенное распределение гауса 0 - много; +-1 меньше; +-2 еще меньше
# итого 9 значений в диапазоне от -4 до 4
import random
import math
from typing import Dict


def gauss(sigma) -> int:
	x = random.gauss(0, sigma)
	s = 1 if x >= 0 else -1
	y = abs(x)
	y = math.floor(y)
	return y * s


def gauss_sigma_1() -> int:
	return gauss(1)


def gauss_sigma_2()-> int:
	return gauss(2)


def gauss_sigma_4()-> int:
	return gauss(4)


def gauss_sigma_8()-> int:
	return gauss(8)


def gauss_sigma_16()-> int:
	return gauss(16)


if __name__ == '__main__':

	dist_dict: Dict[int, int]= {}
	for i in range(3000):
		y = gauss_sigma_1()
		if dist_dict.get(y) is None:
			dist_dict[y] = 0
		else:
			dist_dict[y] += 1

	for i in sorted(dist_dict.keys()):
		print(i, dist_dict[i])
