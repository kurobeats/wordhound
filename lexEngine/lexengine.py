#Lexical Analysis Engine
import numpy as np
import word as wd
import chains
from configobj import ConfigObj
class lexengine:
	
	wordCountDictMean = 0
	wordCountDictTotal = 0 
	wordCountDictCount = 0
	wordCountDictstdDev = 0
	wordCountDictMedian = 0
	wordObjectList = []
	wordCountDict = {}
	corpusDict = {}
	verbose = False
	blacklistedWords = []
	resultFilelocation = ""
	chains = None

	def __init__(self, crawledText, outputFile):
		self.chainList = []
		self.loadBlackList()
		self.resultFilelocation = outputFile
		self.loadCorpus("data/corpus/wordFrequency.txt")
		self.crawledText = crawledText.lower()
		config = ConfigObj('wordhound.conf')
		lexConf = config['Lexengine']
		self.percentage = lexConf['threshold']
		ans = ""
		while (ans != "y" and ans != "n"):
			print "[+] Would you like additional analysis to be done on gathered data in an attempt to build passphrases? (This can take a long time with big data sets 1> hour)\ny or n:"
			ans = raw_input()
		if ans == "y":
			analyse = True
		if ans == "n":
			analyse = False
		if analyse:
			self.buildChains(self.crawledText)
		self.wordCount(self.crawledText)
		self.recursionLevel = 2
	def reset(self):
		global wordObjectList, wordCountDict,corpusDict, verbose
		self.chainList = []
		wordObjectList = []
		wordCountDict = {}
		corpusDict = {}
		verbose = False

	def loadBlackList(self):
		f = open('data/corpus/blacklist.txt', 'r')
		re = f.readlines()
		sanitisedRe = []
		for line in re:
			line = self.sanitise(line)
			sanitisedRe.append(line.strip())
		f.close()
		self.blacklistedWords = sanitisedRe
		print "[-] Loaded blacklist"

	def loadCorpus(self, location):
		#Loads the corpus into corpusDict and saves the word + the % frequency
		f = open(location, 'r')
		read = f.read()
		f.close()
		read = read.split('\n')
		count = 0
		for i in read:
			if len(i) < 3:
				continue
			i = i.replace('\n', "")
			i = i.split(' ')

			if count <= 100:
				self.blacklistedWords.append(i[2].lower())
			count +=1
			self.corpusDict[i[2].lower()] = (float(i[1])/1000000)
		print ("[-] Loaded corpus")

	def checkAgainstCorpus(self, word, percentageWordOccurs):
		#This returns a value indicating how much more/less the word appears compared with the corpus
		# 1 = just as often
		# 2 = twice as often
		# .5 = half as often
		try:
			return percentageWordOccurs/(self.corpusDict[word])
		except Exception, e:
			return "EMPTY"

	def sortWordList(self, wlist):

	    for i in range(1,len(wlist)):
	    	temp = wlist[i]
	    	k = i
	    	while k > 0 and temp.confidence < wlist[k-1].confidence:
	    		wlist[k] = wlist[k-1]
	    		k-=1
	    	wlist[k] = temp
	    return wlist
	def wordCount(self, text):
		#THis function returns a dictionary with each word in the text and the number of times it occurs
		print "[-] Preparing datastructures for analysis"
		text = self.sanitise(text)
		text = text.split(' ')
		for word in text:
			word = word.replace(' ', "").strip()
			try:
				self.wordCountDict[word] = self.wordCountDict[word] + 1
			except:
				self.wordCountDict[word] = 1
		for w in self.wordCountDict:
			wordOb = wd.word(w,int(self.wordCountDict[w]))
			self.wordObjectList.append(wordOb)
		
		self.stats()

	def sanitise(self, text):
		#Removes any weird noise from the text
		sanitised = ""
		text = text.replace("\n", " ")
		text = text.replace("\t", " ")
		text = text.replace("-", " ")
		for c in text:
			v = ord(c)
			if (v > 64 and v < 123) or c == ' ':
				sanitised += c
			else:
				sanitised += " "
		return sanitised
		print " - text sanitised"

	def stats(self):
		count = 0
		mean = 0 
		total = 0
		stdDev = 0
		median = 0
		numberArray = []
		for key in self.wordCountDict:
			count+=1
			total+=self.wordCountDict[key]
			numberArray.append(self.wordCountDict[key])
		#Now for mean and stdDev
		self.wordCountDictTotal  = total
		x = np.array(numberArray)
		self.wordCountDictstdDev = np.std(x)
		self.wordCountDictMean = np.mean(x)
		self.wordCountDictMedian =  np.median(x)
		for w in self.wordObjectList:
			w.frequency = float(w.occurence)/float(self.wordCountDictTotal)
		#print " - mean {0}\n - median {1}\n - standard deviation {2}\n - total unique words {3}".format(self.wordCountDictMean,median,self.wordCountDictstdDev,total)
		print "[-] Done analysing text"
	
	def buildChains(self, text):
		print "[-] Building Chains"
		
		#PARSE 1: Build word objects
		text = self.sanitise(text)
		text = text.replace('\n', " ")
		text = text.split(' ')
		chainObject = chains.chains(text)
		for i in range(len(text)):
			chainObject.addChain(i)

		#Until I build some more intelligence into it, its going to discount a phrase if it contains words in blacklist
		print "[-] Compiling chains"
		temp = chainObject.compileChains()
		for chain in temp:
			add = True
			for word in chain.split(" "):
				if word in self.blacklistedWords:
					add = False
					break
			if add:
				self.chainList.append(chain)


		print "[-] Done analysing chains"


	def trimPercentage(self):
		#This should trim the word based on it appearing more or less frequently than its corresponding word in the corpus.
		
		results = []
		maybe = []
		print "[-] {0} unique words about to be processed".format(len(self.wordObjectList))
		for word in self.wordObjectList:

			correlation = self.checkAgainstCorpus(word.text, (word.frequency))
			word.confidence = correlation
			if not(len(word.text)>3):
				continue
			if (correlation == "EMPTY"):
				maybe.append(word)
				continue
			if (correlation > self.percentage):
				#print "good correlation"
				if word.text not in self.blacklistedWords:
					results.append(word)
					
				else:
					#print "Did not add {0} because it is common".format(word.text)
					pass
			else:
				pass

				#print ("Assuming that {0} is not that relevant".format(word.text))
		#Sort result list
		results = self.sortWordList(results)
		r = open(self.resultFilelocation, 'w')
		resultsString = ""

		for w in results:
			try:
				resultsString+=w.text+"\n"
			except:
				pass
		
		if len(maybe) > 1:
			print "[+] Clarification needed:\nI'm not sure if these words should be added to the dictionary. Press :\n\t\'0\' to skip all\n\t\'1\' to add all\n\t\'y\' to add word\n\t\'n\' to skip word."
			addAll = False
			for w in maybe:
				if len(w.text) > 3 and w.text.strip() not in self.blacklistedWords:
					try:
						
						if (not addAll):
							print w.text
							choice = (raw_input())
							if(choice == '0'):
								break
							if (choice == '1'):
								addAll = True
							if (choice == 'n'):
								print " - Word not added -"
								continue
							if (choice == 'y'):
								print " - Word added - "

						resultsString+=(w.text+"\n")
					except:
						pass
		
		
		print "[+] Clarification needed:\nI'm not sure if these are relevant phrases and should be added to the dictionary. Press :\n\t\'0\' to skip all\n\t\'1\' to add all\n\t\'y\' to add word\n\t\'n\' to skip word."
		addAll = False
		for line in self.chainList:
			if len(line.split(" ")) > 1:
				try:
					
					if (not addAll):
						print line
						choice = (raw_input())
						if(choice == '0'):
							break
						if (choice == '1'):
							addAll = True
						if (choice == 'n'):
							print " - Phrase not added -"
							continue
						if (choice == 'y'):
							print " - Phrase added - "

					resultsString+=(line+"\n")
					resultsString+=(line.replace(" ", "").strip()+"\n")
				except:
					pass

		r.write(resultsString)
		r.close()
		if len(resultsString) > 5:
			#os.system("open {0}".format(self.resultFilelocation))
			print "[=] DICTIONARY GENERATED [=]\nDictionary was successfully generated and saved to "+self.resultFilelocation

		else:
			print "[=] DICTIONARY GENERATION FAILED [=]\nNot enough text could be extracted from site. Make sure you specified domain and url correctly"
		self.reset()
	def aggregateDict(self, dictList):
		words ={}
		totalDicts = float(len(dictList))
		count = 0
		for i in dictList:
			count+=1
			print"[-] Processing {0}".format(i)
			print "[-] Processed {0} dictionary".format(count)
			f = open(i)
			currDict = f.readlines()
			f.close()
			processedWords = []
			for word in currDict:
				if word not in processedWords:
					processedWords.append(word)
					word=word.replace('\n', "")
					w = words.get(word)
					if w == None:
						words[word.strip()] = 1.0
					elif words[word.strip()] < count:
						words[word.strip()] +=1.0
		#Done Reading them in. Now we process
		
		finalWords = {}
		# percentage of how often a word must occur throughout the dicts 0.25 = 1/4 of dicts must have it

		for key in words:
			#print float(float(words[key]) / float(totalDicts))
			if (float(float(words[key]) / float(totalDicts)) >= 0.5):
				
				x = finalWords.get(key)
				if (x == None):
					finalWords[key] = 1.0
				else:
					finalWords[key] += 1.0

	
		finalSortedList = sorted(finalWords, key=finalWords.get)
		f = open(self.resultFilelocation, 'w')
		for key in finalSortedList:

			f.write(key + '\n')
		
		f.close()
		if len(finalWords) > 5:
			#os.system("open {0}".format(self.resultFilelocation))
			print "[=] DICTIONARY GENERATED [=]\nDictionary was successfully generated and saved to "+self.resultFilelocation
		else:
			print "[=] DICTIONARY GENERATION FAILED [=]\nNot enough text for aggregation. Are you sure that you have built dictionaries yet?"

	def collateDicts(self, dictList):
		words ={}
		totalDicts = float(len(dictList))
		count = 0
		finalWords = {}
		for i in dictList:
			count+=1
			print"[-] Processing {0}".format(i)
			print "[-] Processed {0} dictionary".format(count)
			f = open(i)
			currDict = f.readlines()
			f.close()
			for j in currDict:
				finalWords[j.strip()] = 0
		
		f = open(self.resultFilelocation, 'w')
		for key in finalWords.keys():

			f.write(key + '\n')
		
		f.close()
		if len(finalWords) > 5:
			#os.system("open {0}".format(self.resultFilelocation))
			print "[=] DICTIONARY GENERATED [=]\nDictionary was successfully generated and saved to "+self.resultFilelocation
		else:
			print "[=] DICTIONARY GENERATION FAILED [=]\nNot enough text for aggregation. Are you sure that you have built dictionaries yet?"


