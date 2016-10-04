#This class is here to maintain the occurrance of of two words together and marks this as phrase

class chains:
	def __init__(self, text):
		self.library = {}
		self.text = text

	def addChain(self,index, wordLevel = 3):
		compound = ""
		for i in range(wordLevel):
			if ((i+index) <= len(self.text)-1):
				compound += self.text[index+i].strip()+" "
				#print compound
				if i == 0:
					continue
				curr = self.library.get(compound.strip())
				if curr == None:
					self.library[compound.strip()] = 1
				else:
					self.library[compound.strip()] += 1
		#print self.library

	def compileChains(self):
		significantChains = []
		#print self.library
		for key in self.library:
			#print key
			if self.library[key] > 3 and (len(key.replace(" ", "").strip()) > 5):
				#print "found sig" + str(self.library[key])+ " : "+ str(key)
				significantChains.append(key.strip())
				for i in key.split(" "):
					significantChains.append(i)

		return significantChains