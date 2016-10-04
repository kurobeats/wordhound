#Download PDF from link

import requests
import random
import shutil
import urllib2
import subprocess
def extractInfoFromPdf(self, url):
		filename = random.randint(0,1500000)
		outputFileName = self.workingDirectory + "html/" + filename + ".pdf"
		f = urllib2.urlopen(theurl)
		with open("output.pdf", "wb") as code:
			code.write(f.read())
		#Now we have downloaded the pdf. Yay. Now we need to extract the text from it.
		x = subprocess.Popen(['ps2ascii', "output.pdf"], stdout=subprocess.PIPE)
		return x.stdout.read()