from tweepy import OAuthHandler, API

import twitter_credentials as tc
import numpy as np
import pandas as pd
from firestore_handler import FirestoreHandler
from firebase_admin import firestore

from datetime import datetime, timedelta
import twitter_credentials as tc

from transformers import pipeline  



##Twitter Client
class TwitterClient():
    _excluded_terms = " -filter:retweets -filter:links -@crypto_bearr -giveaway -cryptohunt -$RSD" \
                            "-doge -$doge -dogecoin -#doge -#NFTGiveaway  -safemoon" \
                            " -#airdrop -#airdrops -airdrop -\"requesting faucet\" -ICONOMI"\
                            "-#freetokens"
    _firebase_handler = FirestoreHandler()
    
    def __init__(self, twitter_user=None):
        self.auth = TwitterAuthenticator().authenticate_twitter_app()
        self.twitter_client = API(self.auth)
        self.twitter_user = twitter_user

    def get_twitter_client_api(self):
        return self.twitter_client

    def last_hour_tweets(self, token_name):
        ticker = self.get_ticker(token_name)
        list_to_return = []
        for name in [token_name, ticker]:
            final_id = self._firebase_handler.get_last_id(token_name)
            if final_id is not None:
                api = self.get_twitter_client_api()

                tweets = api.search(q= name + self._excluded_terms, count = 100,
                                lang = "en", tweet_mode="extended")

                recent_id = tweets[-1].id

                list = self.get_tweet_data(tweets)

                while recent_id > final_id:
                    new_tweets = api.search(q= name + self._excluded_terms, count = 100,
                                    lang = "en", tweet_mode="extended", max_id = recent_id)
                    recent_id = new_tweets[-1].id
                    
                    new_list = self.get_tweet_data(new_tweets)
                    for item in new_list:
                        list.append(item)
                
                count = 1
                for item in reversed(list):
                    if item["tweet_id"]>final_id:
                        break
                    count+=1
                list_to_return.extend(list[:-count])

            else:
                list_to_return = self.get_last_tweet(token_name)

        return list_to_return

    def get_ticker(self, name):
        if name == "ethereum":
            return "$ETH"
        elif name == "bitcoin":
            return "$BTC"
        elif name == "cardano":
            return "$ADA"
        elif name == "polkadot":
            return "$DOT"
        elif name == "chainlink":
            return "$LINK"
        elif name == "uniswap":
            return "$UNI"
        else:
            return None


    def get_tweet_data(self, searchResults):
        """
        Returns dictionary containing full text of tweet, 
                the time it was created,
                 and the username of the entity that posted it.
        Param:
            token_name: String to search for in Twitter (default value: None)
        """

        list = []
        for tweet in searchResults:
            list.append({'full-text': tweet.full_text,
                            "created-at": tweet.created_at,
                            "username": tweet.user.screen_name,
                            "tweet_id": tweet.id})
        return list

    def get_recent_tweets(self, name):
        '''
        Collects single most recent tweet to be sent to front end to be displayed
        '''
        api = self.get_twitter_client_api()

        tweets = api.search(q= name + self._excluded_terms, count = 100,
                        lang = "en", tweet_mode="extended")
        return self.get_tweet_data(tweets)

    def populate_firebase(self, token_name):
        fire = FirestoreHandler()
        classifier = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment", return_all_scores=True)
        tweets = self.get_recent_tweets(token_name)
        fire.add_tweets(tweets, token_name, classifier)

    def tweets_to_firestore(self, name, classifier):
        tweet_list = self.last_hour_tweets(name)
        self._firebase_handler.add_tweets(tweet_list, name, classifier)
    
    def get_daily_sentiment(self, name):
        docs = self._firebase_handler.db.collection(f'tokens/{name}/daily-sentiment').order_by(u'timestamp', direction=firestore.Query.DESCENDING).limit(1).get()
        return round(docs[0].to_dict()['daily-sentiment'],5)

# Twitter Authenticator
class TwitterAuthenticator():

    def authenticate_twitter_app(self):
        """
        Returns authenticated Twitter developer account access
        """
        auth = OAuthHandler(tc.API_KEY, tc.API_SECRET)
        auth.set_access_token(tc.ACCESS_TOKEN, tc.ACCESS_SECRET)
        return auth

# client = TwitterClient()
# names = ["uniswap", "chainlink"]
# for name in names:
#     client.populate_firebase(name)