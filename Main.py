import lexEngine.lexengine as LE
import os
import time
import subprocess
import client as cli
import translate
import expander
subprocess.call('clear')
print '''
                              `                                     
            `'+++++.       '+'+     `'+`+++.   :+    +,++++++'`           
           ''++++++++       .++:    ;++  .+:   ++`  `+  ,+' `++           
          ++++++++++'.      .++'    +'+   ++  `++:  :+  :+:  ;+,          
         '+'+++++++++,      :+++   ;+++   ++  +:++  +;  ;+,  '+.          
        `++'++.   ;+'`      :+,+   +`++   ++  + '+  +   '+. ,++           
        ;++++      ;;  `    ;'`+'`,+ ++   '+ ,' '+`,+   ''+++;            
        ++++    ``     ,`   '; +' +, +'   ;+.+. .+,';   ++ ++.            
        +'+    +++'   ,:`   +: ++`+  +'   ,+:+   +'+`   ++ .++            
        ++    #++'   ,::`   +, .++: `+;   `++'   +++    ++  #+`           
        #   ` `.`   .:::`   +. `'+` .+:    ++    '+'    ++  .'+           
        ,  `:      ,::::    +`  +'  :+,    #+    :+,   `++   +#           
           :::`   ,::::,                                                  
           ::::::::::::`         
           :::::::::::.            
           .:::::::::.               
            `::::::,`              
                `         
Presents : 
                '''

print '''
$$\      $$\                           $$\ $$\   $$\                                     $$\ 
$$ | $\  $$ |                          $$ |$$ |  $$ |                                    $$ |
$$ |$$$\ $$ | $$$$$$\   $$$$$$\   $$$$$$$ |$$ |  $$ | $$$$$$\  $$\   $$\ $$$$$$$\   $$$$$$$ |
$$ $$ $$\$$ |$$  __$$\ $$  __$$\ $$  __$$ |$$$$$$$$ |$$  __$$\ $$ |  $$ |$$  __$$\ $$  __$$ |
$$$$  _$$$$ |$$ /  $$ |$$ |  \__|$$ /  $$ |$$  __$$ |$$ /  $$ |$$ |  $$ |$$ |  $$ |$$ /  $$ |
$$$  / \$$$ |$$ |  $$ |$$ |      $$ |  $$ |$$ |  $$ |$$ |  $$ |$$ |  $$ |$$ |  $$ |$$ |  $$ |
$$  /   \$$ |\$$$$$$  |$$ |      \$$$$$$$ |$$ |  $$ |\$$$$$$  |\$$$$$$  |$$ |  $$ |\$$$$$$$ |
\__/     \__| \______/ \__|       \_______|\__|  \__| \______/  \______/ \__|  \__| \_______|

'''
time.sleep(2)
def main():
	
	while True:
		subprocess.call("clear")
		print '''
=== WELCOME TO WORDHOUND ===

[+] Please select option:
	
	1. Generate Dictionary
	2. Expand or Translate Existing dictionary

	99. Exit
'''	 
		choice = int(raw_input())
		if choice == 1:
			generation()
		elif choice == 2:
			manipulate()
		else:
			return

def manipulate():
	os.system("clear")
	print '''
[+] Please select option:
	
	1. Translate Dictionary
	2. Expand Dictionary (Tries to derive keywords from related terms)

'''	
	choice = int(raw_input())
	if choice == 1:
		translateDict()
	else:
		expand()

def expand():
	print '[+] Please input the location of dictionary'
	loc = raw_input().replace("\'", "").strip()

	while not(os.path.exists(loc)):
		print "[x] {0} doesn't seem to exist, try again.".format(loc)
		loc = raw_input()

	print "[-] Beginning Expansion..."
	e = expander.expand(loc, loc+"-EXPANDED")
	e.expand()

	
def translateDict():
	print '[+] Please input the location of dictionary'
	loc =raw_input().replace("\'", "").replace("\"", "").strip()
	while not(os.path.exists(loc.replace("\'", "".replace("\"", "")))):
		print "[x] That doesn't seem to exist, try again."
		loc = raw_input()
	f = open('languages.data', 'r')
	x = f.readlines()
	choices = x[:]
	f.close()
	
	for i in range(len(x)):
		print "\t{0}. {1}".format(i,x[i].split('\t')[0])
	print "[+] Please select the language to translate to (e.g. 12):"
	choice = int(raw_input())
	lang = choices[choice].split('\t')[1]
	t = translate.Translator(lang.strip())
	f = open(loc, 'r')
	x = f.read()
	f.close()
	
	translated = t.translate(x)
	f = open(loc+"-{0}".format(lang.upper()).strip(), 'w')
	f.write(translated.encode('utf8'))
	f.close()
	print "[+] Dictionary translated, saved to {0}...".format(loc+"-{0}".format(lang.upper()))
	raw_input()
	os.system("clear")


def generation():
		string, options = createJob()
		print '''
=== WELCOME TO WORDHOUND ===

[+] Please select industry:
'''			
		print string
		
		print "\t99. Exit"
		choice = int(raw_input())-1
		if choice == 98:
			subprocess.call('clear')
			print "[-] Thanks for using *WordHound*.\n\t@tehnlulz"
			return
		if choice >= len(options):
			createNewIndustry()
		else:
			industrySelected(options[choice])
		print "Press enter to continue..."
		raw_input()
	
def industrySelected(industry):
	subprocess.call("clear")
	count = 1
	options = ""
	print'''
=== {0} ==='''.format(industry)
	optionsList = []
	#print(returnDirs("data/industries/"+industry+'/'))
	for dirname in returnDirs("data/industries/"+industry+'/'):
		options += '\t'+str(count) + ". " + dirname + '\n'
		optionsList.append(dirname)
		count+=1
	options += '\n\t'+str(count) + ". Create new client\n"
	options +=  '\t'+str(count+1) + ". Generate industry correlated dictionary\n"
	options +=  '\t'+str(count+2) + ". Generate concatenated industry dictionary\n"
	print options
	choice = int(raw_input())
	if choice == count:
		createNewClient(industry)
	elif choice == (count+1):
		generateIndustryDictionary(industry)
	elif choice == (count+2):
		generateCollatedDictionary(industry)
	else:
		clientSelected(optionsList[choice-1], industry)

def generateCollatedDictionary(industry):
	currInds = []
	for dirname in returnDirs("data/industries/"+industry+'/'):
		if os.path.exists("data/industries/"+industry+'/'+dirname+'/'+"PdfDictionary.txt"):
			currInds.append("data/industries/"+industry+'/'+dirname+'/'+"PdfDictionary.txt")
		if os.path.exists("data/industries/"+industry+'/'+dirname+'/'+"WebsiteDictionary.txt"):
			currInds.append("data/industries/"+industry+'/'+dirname+'/'+"WebsiteDictionary.txt")
		if os.path.exists("data/industries/"+industry+'/'+dirname+'/'+"TxtDictionary.txt"):
			currInds.append("data/industries/"+industry+'/'+dirname+'/'+"TxtDictionary.txt")
		if os.path.exists("data/industries/"+industry+'/'+dirname+'/'+"TwitterSearchTermDictionary.txt"):
			currInds.append("data/industries/"+industry+'/'+dirname+'/'+"TwitterSearchTermDictionary.txt")
		if os.path.exists("data/industries/"+industry+'/'+dirname+'/'+"TwitterHandleDictionary.txt"):
			currInds.append("data/industries/"+industry+'/'+dirname+'/'+"TwitterHandleDictionary.txt")
	lex = LE.lexengine("", "data/industries/"+industry+'/'+"CollatedDictionary.txt", False)
	print "[+] Beginning dictionary collation..."
	lex.collateDicts(currInds)
	print ""

def generateIndustryDictionary(industry):
	currInds = []
	for dirname in returnDirs("data/industries/"+industry+'/'):
		if os.path.exists("data/industries/"+industry+'/'+dirname+'/'+"PdfDictionary.txt"):
			currInds.append("data/industries/"+industry+'/'+dirname+'/'+"PdfDictionary.txt")
		if os.path.exists("data/industries/"+industry+'/'+dirname+'/'+"WebsiteDictionary.txt"):
			currInds.append("data/industries/"+industry+'/'+dirname+'/'+"WebsiteDictionary.txt")
		if os.path.exists("data/industries/"+industry+'/'+dirname+'/'+"TxtDictionary.txt"):
			currInds.append("data/industries/"+industry+'/'+dirname+'/'+"TxtDictionary.txt")
		if os.path.exists("data/industries/"+industry+'/'+dirname+'/'+"TwitterSearchTermDictionary.txt"):
			currInds.append("data/industries/"+industry+'/'+dirname+'/'+"TwitterSearchTermDictionary.txt")
		if os.path.exists("data/industries/"+industry+'/'+dirname+'/'+"TwitterHandleDictionary.txt"):
			currInds.append("data/industries/"+industry+'/'+dirname+'/'+"TwitterHandleDictionary.txt")
	lex = LE.lexengine("", "data/industries/"+industry+'/'+"IndustryDictionary.txt", False)
	print "[+] Beginning dictionary aggregation..."
	lex.aggregateDict(currInds)
	print ""

def generateClientDictionary(clientName):
	currDicts = []
	if os.path.exists(client.workingDirectory + 'PdfDictionary.txt'):
			currDicts.append("data/industries/"+industry+'/'+dirname+'/'+"PdfDictionary.txt")
	if os.path.exists(client.workingDirectory + 'TxtDictionary.txt'):
			currDicts.append("data/industries/"+industry+'/'+dirname+'/'+"TxtDictionary.txt")
	if os.path.exists(client.workingDirectory + 'WebsiteDictionary.txt'):
			currDicts.append("data/industries/"+industry+'/'+dirname+'/'+"WebsiteDictionary.txt")
	if os.path.exists(client.workingDirectory + 'TwitterHandleDictionary.txt'):
			currDicts.append("data/industries/"+industry+'/'+dirname+'/'+"TwitterHandleDictionary.txt")
	if os.path.exists(client.workingDirectory + 'TwitterSearchTermDictionary.txt'):
			currDicts.append("data/industries/"+industry+'/'+dirname+'/'+"TwitterSearchTermDictionary.txt")
def returnDirs(path):
	results = []
	for (dirpath, dirnames, filenames) in os.walk(path):
		results.extend(dirnames)
		return results

def clientSelected(clientName, industry):
	subprocess.call("clear")
	c = cli.client(industry, "", clientName, "", "data/industries/" + industry +'/' + clientName +'/')
	newClientOptions(c)
	pass
def createNewClient(industry):
	subprocess.call("clear")
	print'''
=== CREATE NEW CLIENT ===

'''	
	name = ""
	while len(name) == 0:
		print "[+] Please enter client name (can be pseudonym):"
		name = raw_input()
	c = cli.client(industry, "", name, "", "data/industries/" + industry +'/' + name +'/')
	print "[-] New client added..."
	time.sleep(1)
	newClientOptions(c)

def newClientOptions(client):
	subprocess.call("clear")
	print'''
=== CLIENT OPTIONS ===

[+] Please choose an option:
'''	
	print "1. Generate Dictionary from website."
	print "2. Generate Dictionary from Text file."
	print "3. Generate Dictionary from pdf."
	#print "4. Generate Dictionary from twitter handle."
	print "4. Generate Dictionary from twitter search term."
	print "5. Generate Dictionary from Reddit"
	print "\n6. Generate aggregate client dictionary."
	choice = 0
	while(choice not in ['1', '2', '3', '4', '5','6']):
		choice = raw_input()
		if choice == '1':
			print "[-] Please enter the URL of website to be crawled:"
			url = raw_input()
			#print "[-] Please enter the domain of client (Put a \'.\' for all links):"
			#domain = raw_input()
			print "[-] How many levels of recursion should I crawl? (Default=2):"
			client.url = url
			client.domain = ""
			recursionLevel = raw_input()
			client.buildDictionary(int(recursionLevel))
			break
		elif choice == '2':
			print "[-] Please give the path of the text file to process:"
			path = raw_input()
			client.buildDictionaryText(path)
			break
		elif choice == '3':
			print "[-] Please give the path of the pdf to process:"
			path = raw_input()
			client.buildDictionaryPdf(path)
			break
		#elif choice == '4':
		#	print "[-] Please enter the user's handle(without the '@'):"
		#	handle = raw_input()
		#	client.buildDictionaryFromTwitterUsername(handle)
		elif choice == '4':
			print "[-] Please enter the search term:"
			term = raw_input()
			client.buildDictionaryFromTwitterSearchTerm(term)
			break
		elif choice == '5':
			print "[-] Please enter any number of subreddits, seperated by a comma\n(e.g. battlefield, netsec, til)"
			subs = raw_input().replace(" ","")
			subs = subs.split(',')
			print ""
			subprocess.call("clear")
			client.buildDictionaryReddit(subs)
		elif choice == '6':
			print "[-] Beginning dictionary aggregation"
			client.buildAggregate()
			break
def createNewIndustry():
	subprocess.call("clear")
	print'''
=== CREATE NEW INDUSTRY ===

'''	
	name = ""
	while len(name)==0:
		print "[+] Please enter industry name:"
		name = raw_input()
	if not os.path.exists("data/industries/"+name): os.makedirs("data/industries/"+name)
	print "[-] New Industry added..."
	time.sleep(1)
	subprocess.call("clear")

def createJob():
	subprocess.call("clear")
	count = 1
	options = ""
	optionsList = []
	for (dirpath, dirnames, filenames) in os.walk("data/industries"):
		optionsList.extend(dirnames)
		break
	for i in optionsList:
		
		options += '\t'+str(count) + ". {0}\n".format(i)
		count +=1
	options += '\n\t'+str(count) + ". Create new industry\n"
	#print optionsList
	return options, optionsList
main()
