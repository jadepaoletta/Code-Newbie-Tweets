import json
import time
import re
import oauth2 as oauth
from secret import keys
from flask import (Flask, jsonify, render_template)
from model import (connect_to_db, db, Tweet)
#import pprint    pp = pprint.PrettyPrinter(indent=4) pp.pprint(stufftoprint)



app = Flask(__name__)
app.secret_key = "miau"

link = re.compile(r'(http(s)?://\w+(\.\w+)+/(\w)*)')

def authorize():
    """authorize w/ twitter api and fetch recent codenewbie tweets, return a json"""

    consumer = oauth.Consumer(key=keys["consumer_key"], secret=keys["consumer_secret"])
    access_token = oauth.Token(key=keys["access_token"], secret=keys["access_secret"])
    client = oauth.Client(consumer, access_token)
    test_url = "https://api.twitter.com/1.1/search/tweets.json?q=%23codenewbie&result_type=mixed&count=100&include_entities=false"
    response, data = client.request(test_url)

    return jsonify(data)#json.loads(data)


def format_tweets():
    """return a list of tuples of recent codenewbie tweets"""

    tweet = None
    time_created = None
    retweets = None
    results = authorize()["statuses"]
    output = []

    for result in results:
        if result['text'][0:2] != 'RT':
            tweet = linkyfy(result['text']) # embeds link in anchor tag 
            time_created =  time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(result['created_at'], '%a %b %d %H:%M:%S +0000 %Y'))
            handle = result['user']['screen_name']
            if 'retweeted_status' in result:
                retweets = result['retweeted_status']['retweet_count']
            output.append((handle, time_created, tweet, retweets))

    return output


def tweet_to_db():
    """Add tweets into db"""


    output = format_tweets()
    text_list = [a.text for a in Tweet.query.all()]
    print output
    print text_list


    for tweet in output:
        if tweet not in text_list: #need to edit this 
            tweet = Tweet(handle = tweet[0],
                            time_created =tweet[1],
                            text = tweet[2],
                            retweets = tweet[3])
            db.session.add(tweet)

    db.session.commit()

def linkyfy(text):
    """ Embeds links in anchor tag"""
    links = link.findall(text)
    for l in links:
        text = text.replace(l[0], r"<a href='%s'>%s</a>" % (l[0], l[0]))
    return text

@app.route("/")
def homepage():
    """Display tweets"""
    
    output = [a for a in Tweet.query.all()]
   

    return render_template("home.html", output = output)


@app.route("/about")
def display_about():
    """Diplay about page"""

    return render_template("about.html")


@app.route("/friends")
def display_friends():
    """Diplay list of contributors to open source code practice project"""

    return render_template("friends.html")

    

@app.route("/api/tweets")
def create_api_endpoint():
    """Using ingested dsta from twitter create an API endpoint"""

    tweedict = {}
    tweets = Tweet.query.all()

    for tweet in tweets:
        tweedict[tweet.handle] = tweet.text

    return jsonify(tweedict)


if __name__ == "__main__":
    app.debug = True
    connect_to_db(app, "postgresql:///newb")
    app.run(port=5000)



