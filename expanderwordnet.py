#WORD OBJECT

from nltk.corpus import wordnet as wn

class word:
	def __init__(self, text, adj=False, adv=False, noun=False, verb=False, verbose=False):
		#First we lookup the word
		self.text = text
		self.adj = adj
		self.adv = adv
		self.noun = noun
		self.verbose = verbose
		if adj:
			self.synsets = wn.synsets(text, pos=wn.ADJ)
		elif adv:
			self.synsets = wn.synsets(text, pos=wn.ADV)
		elif noun:
			self.synsets = wn.synsets(text, pos=wn.NOUN)
		elif verb:
			self.synsets = wn.synsets(text, pos = wn.VERB)
		elif not adj and not adv and not verb and not noun:
			self.synsets = wn.synsets(text)

	#######
	# PUBLIC FUNCTIONS
	#######

	#Return the textual definition of the word in question
	def definition(self):
		if self.verbose == True:
			pass
		if self.isKnown():
			#print self.synsets[0]
			res = ""
			for i in self.synsets:
				res += i.definition()
			return res
		else:
			return None

	#This will return an antonym
	def antonmys(self):
		#Can only have for adjectives 
		ants = []
		if self.isKnown():
			for i in self.synsets:
				try:
					#print i.lemmas()[0].antonyms()
					ant = i.lemmas()[0].antonyms() 
					#print "ant " + ant
					if len(ant) > 0:
						ants.append(ant)
				except:
					continue
			for i in self.synsets:
				try:
					ant = i.antonyms() 
					#print "ant " + ant
					if len(ant) > 0:
						ants.append(ant)
				except:
					continue
			return ants
		else:
			return None

	def hypernyms(self):
		#Can only have for adjectives 
		hyp = []
		if self.isKnown():
			for i in self.synsets:
				try:
					hyper = i.lemmas()[0].hypernyms() 
					if len(hyper) > 0:
						hyp.append(hyper)
				except:
					continue
			for i in self.synsets:
				try:
					hyper = i.lemmas()[0].hypernyms() 
					if len(hyper) > 0:
						hyp.append(hyper)
				except:
					continue
			return hyp
		else:
			return None

	def hyponyms(self):
		#Can only have for adjectives 
		hyp = []
		if self.isKnown():
			for i in self.synsets:
			#try:
				hypo = i.hyponyms() 
				#print hypo
				if len(hypo) > 0:
					hyp.append(hypo)
			#except:
				continue
			for i in self.synsets:
			#try:
				hypo = i.lemmas()[0].hyponyms() 
				#print hypo
				if len(hypo) > 0:
					hyp.append(hypo)
			#except:
				continue
			return hyp
		else:
			return None


	#Private internal functions
	def isKnown(self):
		if len(self.synsets) == 0:
			return False
		else:
			return True
