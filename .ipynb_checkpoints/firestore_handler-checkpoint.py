import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime, timedelta


class FirestoreHandler():
    # Setup
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

    db = firestore.client()

    def get_indicators(self, name):
        docs = self.db.collection(f"tokens/{name}/indicators").order_by(u'timestamp',
                             direction=firestore.Query.DESCENDING).get()
        list = []
        for doc in docs:
            data = doc.to_dict()
            list.append(data)

    def add_indicators(self, name, indicators):
        self.db.collection(f"tokens/{name}/indicators").add({"indicators":indicators,
                                                            "timestamp":datetime.now()})

    def set_graph_urls(self, name, urls):
        self.db.collection(f"tokens/{name}/urls").add({"Price":urls["Price"],
                                                        "Volume": urls["Volume"],
                                                        "timestamp":datetime.now()})
    
    def get_graph_urls(self, name):
        docs = self.db.collection("tokens/"+name+"/urls").order_by(u'timestamp', 
                        direction=firestore.Query.DESCENDING).limit(1).get()
        url_price = docs[0].to_dict()['Price']
        url_vol = docs[0].to_dict()['Volume']
        return (url_price, url_vol)

    def add_tweets(self, tweet_list, name, classifier):
        '''
        Adds tweets to firestore database, along with calculated sentiment and timestamp
        '''
        
        for tweet in tweet_list:
            text = tweet['full-text']
            result_list = classifier(text)[0]
            total = 0
            for result in result_list:
                if result['label'] == 'LABEL_0':
                    total += (-result['score'])
                elif result['label'] == 'LABEL_2':
                    total += result['score']
            sentiment = total
            self.db.collection('tokens/'+ name +'/tweets').add({'tweet':tweet, 
                'sentiment':sentiment, 
                'timestamp':datetime.now()+timedelta(hours=4)})
    
    def get_daily_sent(self, name):
        list = []
        docs = self.db.collection(f"tokens/{name}/daily-sentiment").order_by(u'timestamp', direction=firestore.Query.DESCENDING).get()
        for doc in docs:
           list.append(doc.to_dict()['daily-sentiment'])
        return list
    
    def get_daily_vol(self, name):
        list = []
        docs = self.db.collection(f"tokens/{name}/daily-sentiment").order_by(u'timestamp', direction=firestore.Query.DESCENDING).get()
        for doc in docs:
           list.append(doc.to_dict()['tweet-count'])
        return list

    def set_daily_sentiment(self):
        last_24_hrs = datetime.now() - timedelta(days=1)
        names = ["ethereum", "bitcoin", "cardano", "uniswap", "chainlink", "polkadot"]

        for name in names:
            docs = self.db.collection(f"tokens/{name}/tweets").where("timestamp", ">", last_24_hrs).get()
            total = 0
            count = 0
            for doc in docs:
                total += doc.to_dict()['sentiment']
                count+=1
            daily_sentiment= total/count if count>0 else "not-available"
            self.db.collection('tokens/' + name + '/daily-sentiment').add(
                                                    {'daily-sentiment':daily_sentiment, 
                                                    'day':last_24_hrs.strftime("%x"),
                                                    'timestamp':datetime.now(),
                                                    'tweet-count':count})

    def get_last_id(self, name):
        last_hr = datetime.now() - timedelta(minutes=70)
        docs = self.db.collection('tokens/' + name + '/tweets').where("timestamp", ">", 
                last_hr).order_by(u'timestamp', direction=firestore.Query.ASCENDING).limit(1).get()
        data = docs[0].to_dict()
        return(data['tweet']['tweet_id'])

    
