#import expander
#import reddit
import translate

t = translate.Translator('jp')
print t.translate("Test Hitler over everything")
f = open('/home/matt/Documents/Code/wordhound/data/industries/Anime/Mangatraders/RedditDictionary.txt')
x = t.translate(f.read())
f.close()

f = open('/home/matt/Desktop/testtranslate.txt', 'w')
f.write(x)
f.close()
#e = expander.expand('/home/matt/Desktop/wordDictCat.txt', '/home/matt/Desktop/expanded.txt')
#e.expand()
#x = reddit.Reddit(["battlefield", "battlefield_4", "battlefield3" ])
#x.crawl()
