import lexEngine.lexengine as LE
import os
import time
import subprocess
import client as cli
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
	subprocess.call("clear")
	while True:
		
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
			continue
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
	options +=  '\t'+str(count+1) + ". Generate industry dictionary\n"
	print options
	choice = int(raw_input())
	if choice == count:
		createNewClient(industry)
	elif choice == (count+1):
		generateIndustryDictionary(industry)
	else:
		clientSelected(optionsList[choice-1], industry)

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
	print "\n5. Generate aggregate client dictionary."
	choice = 0
	while(choice not in ['1', '2', '3', '4', '5','6']):
		choice = raw_input()
		if choice == '1':
			print "[-] Please enter the URL of website to be crawled:"
			url = raw_input()
			print "[-] Please enter the domain of client (Put a \'.\' for all links):"
			domain = raw_input()
			print "[-] How many levels of recursion should I crawl? (Default=2):"
			client.url = url
			client.domain = domain
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