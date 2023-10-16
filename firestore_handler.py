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
        senti_list = self.get_daily_sent(name)
        vol_list = self.get_daily_vol(name)
        length = len(docs)
        for doc,i in zip(docs,range(length)):
            data = doc.to_dict()
            d = {}
            d['timestamp'] = data['timestamp'].strftime('%Y-%m-%d')
            d['tweet-volume'] = vol_list[i]
            d['sentiment'] = senti_list[i]
            indicators = data['indicators']
            for x in indicators:
                d[x] = indicators[x]
            list.append(d)
            
        return list

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
            total = 0
            try:
                result_list = classifier(text)[0]
                for result in result_list:
                    if result['label'] == 'LABEL_0':
                        total += (-result['score'])
                    elif result['label'] == 'LABEL_2':
                        total += result['score']
                sentiment = total
                self.db.collection('tokens/'+ name +'/tweets').add({'tweet':tweet, 
                    'sentiment':sentiment, 
                    'timestamp':datetime.now()+timedelta(hours=4)})
            except Exception as e:
                print("Exception caught: ")
                print(getattr(e, 'message', repr(e)))
    
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
        try:
            data = docs[0].to_dict()
            return(data['tweet']['tweet_id'])
        except:
            return None

    def get_percent_change(self, name):
        docs = self.db.collection(f'tokens/{name}/daily-sentiment').order_by(u'timestamp', direction=firestore.Query.DESCENDING).limit(2).get()
        td_senti = docs[0].to_dict()['daily-sentiment']
        y_senti = docs[1].to_dict()['daily-sentiment']
        decimal_change = ((td_senti/y_senti)-1)
        percent_change = round(decimal_change*100,2)
        color = ""

        if percent_change < 0:
            color += "red"
        elif percent_change > 0:
            color = "green"
        else: 
            color="gray"

        return {"percent":percent_change, "color":color}


    
fire = FirestoreHandler()
# fire.get_percent_change("bitcoin")