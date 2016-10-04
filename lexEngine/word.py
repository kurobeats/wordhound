#Word Object

class word:
	confidence = 0
	text = ""
	frequency = 0.0
	occurence = 0
	nextWord = None
	def __init__(self, text, occurence):
		self.text = text
		self.occurence = occurence