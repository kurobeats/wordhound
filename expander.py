#EXPAND CLASS
import expanderwordnet as word
from sys import stdout

class expand:
	def __init__(self, locationofdic, locationofoutput):
		self.inputdic = locationofdic
		self.outputdic = locationofoutput
		self.allWords = {}

	def expand(self):
		f = open(self.inputdic, 'r')
		r = f.readlines()
		f.close()

		#Iterate through the dictionary and expand each word
		for w in r:
			#print w
			w = w.strip()
			self.allWords[w] = 1
			w = word.word(w)
			definition = w.definition()
			hyper = w.hypernyms()
			hypo = w.hyponyms()
			ants = w.antonmys()
			process = []
			if hyper != None:
				process.append(hyper)
			if hypo != None:
				process.append(hypo)
			if ants != None:
				process.append(ants)
			if definition != None:
				process+ [definition]
			self.addWords(process)
		self.write()
		print "\n[+] Dictionary expanded..."
		raw_input()

	def write(self):
	 	items = ""
		for i in self.allWords.keys():
			i = i.lower()
			if "-" in i:
				splitword = i.split('-')
			else:
				splitword = [i]
			final = ""
			#Extract only a-z
			for w in splitword:
				for c in i:
					if len(c) >1:
						continue
					if ord(c) > 95 and ord(c) < 123:
						final += c 
			items += final + '\n'
		w = open(self.outputdic, 'w')
		w.write(items)
		w.close()

	def addWords(self, lists):
		stdout.write("\r[-] {0}{1} words added...".format(len(self.allWords), ' '*(6-len(str(self.allWords)))))
		for l in lists:
			for sub in l:
				#print sub
				for wd in sub:
					#print type(wd)
					if type(wd) == str or type(wd) == unicode:
						#print wd
						self.allWords[wd] = 1
					else:
						#print wd.name().split('.')[0].replace("_"," ").split(" ")
						for i in wd.name().split('.')[0].replace("_"," ").split(" "):
							self.allWords[i] = 1
