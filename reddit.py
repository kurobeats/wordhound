#reddit
import requests
import json
import time
class Reddit:
	"""Class to handle the crawling of subreddits for lexengine processing"""
	def __init__(self, listSubreddits):
		self.subreddits = listSubreddits
		self.rawText = ""
		self.usedReddits = ""
	def crawl(self):
		for i in self.subreddits:
			self.fetchsubreddit(i)

	def fetchsubreddit(self, subreddit):
		try:
			headers = {'User-Agent' : 'WordHound'}
			print ("http://www.reddit.com/r/{0}/.json".format(subreddit))
			r = requests.get("http://www.reddit.com/r/{0}/.json".format(subreddit), headers=headers)
			jsonData = json.loads(r.content)
			#print jsonData
			jsonData = jsonData['data']['children']
		except:
			return
		comments = []
		articleLinks = []
		for thread in jsonData:
			thread = thread['data']
			comments.append(thread['permalink'])
			articleLinks.append(thread['url'])
		for com in comments:
			time.sleep(1.75)
			try:
				print "[-] Fetching thread {1} from: {0}".format(unicode(com).split("/")[2],unicode(com).split("/")[5])
			#raw_input()
				r = requests.get("http://www.reddit.com{0}/.json".format(com), headers=headers)
			except UnicodeError:
				continue
			try:
				jsonData = json.loads(r.content)
			except:
				continue
			flag = True
			for i in jsonData:
				if flag:
					flag = False
					continue
				comment = i['data']['children']
				for x in comment:
					try:
						sentence = x['data']['body']
					except:
						continue
					#print sentence
					#raw_input()
					if len(sentence) > 0:
						self.rawText+= self.clean(sentence) + " "
				#print comment
		self.usedReddits += subreddit +", "
		print "[+] Fetched {0} words from {1}\n".format(len(self.rawText.split(' ')), self.usedReddits)
		

	def clean(self, sentence):
		w = ""
		for word in sentence.split(' '):
			if "http" in word or "https" in word:
				continue
			w += " "
			word = word.lower()
			for c in word:
				v = ord(c)
				#print c
				if c == ' ' or (v > 95 and v < 127):
					w+=c
		return w
		#Now we need to iterate through each of the threads and pull comments

