from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import tweepy
import json
from configobj import ConfigObj

#from twitter.oauth import write_token_file, read_token_file
#from twitter.oauth_dance import oauth_dance
class twitterSearch():
    def __init__(self):
	config = ConfigObj('wordhound.conf')
        twitterConf = config['Twitter']
        
	
        self.ckey = twitterConf['apikey']
        self.csecret = twitterConf['apisecret']
        self.atoken = twitterConf['accesstoken']
        self.asecret = twitterConf['accesstokensecret']
        if (len(self.ckey) == 0 or len(self.csecret) == 0 or len(self.atoken) == 0 or len(self.asecret) == 0 ):
            print "[x] Error : Have you put in your Twitter API key? Its simple to setup (wordhound.conf)"
            raw_input()
            
    def searchByTerm(self, term, Termscount):
        print "[+] Querying twitter for {0}".format(term)
        print "[-] Authorizing twitter API"
        auth = OAuthHandler(self.ckey, self.csecret)
        auth.set_access_token(self.atoken, self.asecret)
        api = tweepy.API(auth)
        api.verify_credentials()
        print "[-] Twitter auth successful\n[-] Retrieving search data"
        #print "[-] Twitter API requests left for current hour:"
        #print "\t"+str(api.rate_limit_status())
        res = api.search(q=term)
        allTweets = ""
        count = 0
        try:

            for tweet in tweepy.Cursor(api.search,
                                        q=term,
                                        rpp=100,
                                        count = 5,
                                        result_type="recent",
                                        include_entities=True,
                                        lang="en").items(Termscount):
                count+=1
                allTweets += " "+tweet.text
                if (count%100 == 0):
                    print "[-] Downloaded {0} tweets".format(count)
                if count > Termscount:
                    break

        finally:
            results = self.santiseTweets(allTweets)
            print "[-] Extracted ~{0} words for processing and analysis".format(len(results.split(' ')))
            return results

    def santiseTweets(self, bodyText):
        allTweets = bodyText.split(' ')
        results = ""
        for word in allTweets:
            if '@' in word:
                continue
            results += " "+word
        return results

