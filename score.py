class Score:
	LIVE_SCORE = 1
	STARVE_SCORE = 1
	HEDONIC_SCORE = 1
	LOVE_FAIL_SCORE = 5
	MARRY_SCORE = 20
	DIVORSE_ACTIVE_SCORE = 20
	DIVORSE_PASSIVE_SCORE = 10
	MAKE_CHILD = 30
	GET_GENE_UPGRADE = {1: 20, 2: 200, 3: 600, 4: 2000}

	def __init__(self):
		self.score = 0

	def update(self, sc: int) -> None:
		self.score += sc

	def update_gene(self, index: int) -> None:
		index = 4 if index > 4 else index
		sc = Score.GET_GENE_UPGRADE[index]
		self.score += sc