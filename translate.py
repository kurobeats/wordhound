#dictionary Translater
import goslate
from goslate import WRITING_NATIVE_AND_ROMAN, WRITING_ROMAN, WRITING_NATIVE
class Translator:
	def __init__(self, language):
		self.gs = goslate.Goslate(WRITING_ROMAN,timeout = 8)
		self.language = language
	def translate(self, text):
		#First split dictionary into words
		text = text.split('\n')
		#Now we build text into set size chunks
		chunks = []
		tempChunk =""

		for i in text:
			#print i
			if len(tempChunk) > 20000:
				chunks.append(tempChunk)
				tempChunk = i + '\n'
				continue
			else:
				tempChunk += i + '\n'

		translation = ""
		print "[-] Translating dictionary to {0}...".format(self.language)
		count = 0
		for i in chunks:
			count += 1
			print "[-] Translating part {0} of {1}".format(count,len(chunks))
			translation += self.gs.translate(i, self.language)


		
		return translation
