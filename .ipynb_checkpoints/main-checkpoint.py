from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Request
import fastapi
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from tweepy.models import SavedSearch
from twitter_handler import TwitterClient
from firestore_handler import FirestoreHandler 

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
def home(request: Request):
    '''
    Displays home page
    '''
    return templates.TemplateResponse(
    "index.html"
    ,{
    "request": request
    }
    )

#Temporary until I know what to do with this request
@app.get("/favicon.ico")
def do_nothing():
    pass

#Add date selection
@app.get("/{link}")
def display(request: Request, link: str, date: Optional[str] = None):
    '''
    Displays information about selected token. 
    '''
    token_name = link[:-5]
    client = TwitterClient()
    fire = FirestoreHandler()
    today_date = datetime.now().strftime("%Y-%m-%d")
    if token_name:
        data = {"tweets":client.get_recent_tweets(token_name),
                "sentiment":client.get_daily_sentiment(token_name)
                }
        percent_change_dict = fire.get_percent_change(token_name)
    else:
        data = "No data"
    return templates.TemplateResponse(
        link,
        {
            "request": request,
            "token_name":token_name.title(),
            "data": data,
            "urls": fire.get_graph_urls(token_name),
            "current_date": today_date,
            "date":date,
            "percent": percent_change_dict['percent'],
            "color":percent_change_dict['color']
        }
    )