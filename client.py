import os
import lexEngine.lexengine as LE
import subprocess
import random
import urllib2
import reddit
import twitterDicts
import crawler
import re
import threading
import bs4
class client:
	industry = ""
	url = ""
	clientName = ""
	industryWords = []
	domain = ""
	workingDirectory = ""
	htmlText = ""
	pdfsDownloaded = 0
	def __init__(self, industry, url, clientName, domain, directory):
		self.industry = industry
		self.url = url
		self.clientName = clientName
		if not os.path.exists("data/industries/"+industry+'/'+clientName): os.makedirs("data/industries/"+industry+'/'+clientName)
		if not os.path.exists("data/industries/"+industry+'/'+clientName+'/html'): os.makedirs("data/industries/"+industry+'/'+clientName+'/html')
		self.domain = domain
		self.workingDirectory = directory
		self.recursionLevels = 2
		self.crawledText = ""
		self.pdfLocations = []
		self.pdfsDownloaded = 0
		self.count = 0

	def visible(self,element):
	    try:
		    if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
			return False
		    elif re.match('<!--.*-->', str(element)):
			return False
		    return True
	    except:
		    return False


	def crawl(self, recursionLevels):
		print "[+] Beginning crawl... (Ctrl+C to cancel at any time)"
		webcrawler = crawler.Spider()
		self.crawledText  =  webcrawler.urlreport(b=self.url, d=recursionLevels, t=1)
		#print x
		print "[+] Done Crawling..."
		

		#print "[-] Done crawling"
		
		#TODO
				#This is misleading, but at the moment it saves all the visible text to file and returns list of pdfs to download
		if len(self.pdfLocations)>0:
			print "[-] Found {0} PDF's to download.".format(len(self.pdfLocations))
			for i in self.pdfLocations:
				self.extractInfoFromPdf(i)



		
	def santise(self, text):
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

		
	def extractInfoFromPdf(self, url):
		try:
			print "[-] Found PDF for text extraction\n[-] Downloading..."
			filename = str(random.randint(0,1500000))
			outputFileName = self.workingDirectory + filename + ".pdf"
			f = urllib2.urlopen(url)
			with open(outputFileName, "wb") as code:
				code.write(f.read())
			#Now we have downloaded the pdf. Yay. Now we need to extract the text from it.
			x = subprocess.Popen(['ps2ascii', outputFileName], stdout=subprocess.PIPE)
			print "[-] Downloaded pdf. Will only download {0} more".format(5 - self.pdfsDownloaded)
			return x.stdout.read()
		except Exception, e:
			print "[-] PDF not successfully downloaded"
			print e
			return ""

	def buildDictionaryReddit(self, subredditList):
		print "[+] Beginning to Crawl Reddit\n"
		x = reddit.Reddit(subredditList)
		x.crawl()
		try:
			lex = LE.lexengine(x.rawText, self.workingDirectory+"RedditDictionary.txt")
			print "[+] Beginning analysis..."
			lex.trimPercentage()
		except:
			print "[-] Could not process file."

	def buildDictionaryText(self, fileLoc):
		fileLoc = fileLoc.strip()
		if fileLoc[0] == '\'' and fileLoc[len(fileLoc)-1] == '\'':
			fileLoc = fileLoc[1:len(fileLoc)-1]
		while(not(os.path.exists(fileLoc))):
			print "[-] The file location entered does not seem to exist:\n{0}.\nTry again.".format(fileLoc)
			fileLoc = raw_input()
		try:
			f = open(fileLoc)
			text = f.read()
			f.close()
		except:
			print "[-] Could not read file."
		try:
			lex = LE.lexengine(text, self.workingDirectory+"TxtDictionary.txt")
			print "[+] Beginning analysis..."
			lex.trimPercentage()
		except:
			print "[-] Could not process file."


	def buildDictionaryPdf(self, fileLoc):
		fileLoc = fileLoc.strip()
		
		if fileLoc[0] == '\'' and fileLoc[len(fileLoc)-1] == '\'':
			fileLoc = fileLoc[1:len(fileLoc)-1]
		while(not (os.path.exists(fileLoc))):
			print "[-] The file location entered does not seem to exist:\n{0}.\nPlease reenter the path.".format(fileLoc)
			fileLoc = raw_input()
	#try:
		x = subprocess.Popen(['ps2ascii', fileLoc], stdout=subprocess.PIPE)
		print "[-] Extracting text from pdf."
		lex = LE.lexengine(x.stdout.read(), self.workingDirectory+"PdfDictionary.txt")
		
		print "[+] Beginning analysis..."
		lex.trimPercentage()
	#except:
		#print "[-] Could not process file."


	def buildDictionary(self, rLevels):
		self.recursionLevels = rLevels
		self.crawl(rLevels)
		lex = LE.lexengine(self.crawledText, self.workingDirectory+"WebsiteDictionary.txt")
		print "[+] Beginning trim..."
		lex.trimPercentage()
	
	def buildDumbWebscrape(self, rLevels):
		self.recursionLevels = rLevels
		self.crawl(rLevels)
		lex = LE.lexengine(self.crawledText, self.workingDirectory+"WebsiteDictionary.txt")
		print "[+] Beginning trim..."
		lex.trimPercentage()
		
	def buildAggregate(self):
		lex = LE.lexengine("", self.workingDirectory+"AggregateDictionary.txt", False)
		
		dirname = self.workingDirectory
		currDicts = []
		if os.path.exists(self.workingDirectory + 'PdfDictionary.txt'):
			currDicts.append(self.workingDirectory+"PdfDictionary.txt")
		if os.path.exists(self.workingDirectory + 'TxtDictionary.txt'):
				currDicts.append(self.workingDirectory+"TxtDictionary.txt")
		if os.path.exists(self.workingDirectory + 'WebsiteDictionary.txt'):
				currDicts.append(self.workingDirectory+"WebsiteDictionary.txt")
		if os.path.exists(self.workingDirectory + 'TwitterHandleDictionary.txt'):
			currDicts.append(self.workingDirectory+"TwitterHandleDictionary.txt")
		if os.path.exists(self.workingDirectory + 'TwitterSearchTermDictionary.txt'):
			currDicts.append(self.workingDirectory+"TwitterSearchTermDictionary.txt")
		lex.aggregateDict(currDicts)

	def buildDictionaryFromTwitterUsername(self, handle):
		t = twitterDicts.twitterSearch()
		lex = LE.lexengine(t.searchByUser(handle), self.workingDirectory+"TwitterHandleDictionary.txt")
		print "[+] Beginning trim..."
		lex.trimPercentage()
	def buildDictionaryFromTwitterSearchTerm(self, term):
		t = twitterDicts.twitterSearch()
		print "How many tweets would you like to analyse?:(Default = 700) (Max = 700)"
		count = int(raw_input())
		lex = LE.lexengine(t.searchByTerm(term, count), self.workingDirectory+"TwitterSearchTermDictionary.txt")
		print "[+] Beginning trim..."
		lex.trimPercentage()
