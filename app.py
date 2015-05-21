import time
import boto.sqs
import tweepy
import threading
import json
import requests

from rauth import OAuth2Service
from flask.ext.login import LoginManager, UserMixin, login_user, logout_user, current_user
from oauth import OAuthSignIn
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.socketio import SocketIO, emit
from flask import Flask, render_template, request, redirect, g, url_for
from threading import Thread
from boto.sqs.message import Message
from boto.dynamodb2.table import Table

app = Flask(__name__)

socketio = SocketIO(app)
db = SQLAlchemy(app)

with open("config") as f:
    content = f.readlines()
consumer_key = content[0].rstrip()
consumer_secret = content[1].rstrip()
access_token = content[2].rstrip()
access_token_secret = content[3].rstrip()
aws_access= content[4].rstrip()
aws_secret = content[5].rstrip()

conn = boto.sqs.connect_to_region("us-east-1", aws_access_key_id=aws_access, aws_secret_access_key=aws_secret)
reachqueue = conn.create_queue('Reachv1')
spark_notifications = conn.get_queue('spark_output_events')

app.config['SECRET_KEY'] = 'top secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['OAUTH_CREDENTIALS'] = {
    'facebook': {
        'id': '470154729788964',
        'secret': '010cc08bd4f51e34f3f3e684fbdea8a7'
    },
    'twitter': {
        'id': '3qZbl5CEuWn6urdczMJctMUof',
        'secret': 'JNaIHzBUMYiNFlQMbMo65QPBopuoos7uMoxRBX0mk5TlemBDee'
    }
}


lm = LoginManager(app)
lm.login_view = 'index'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    social_id = db.Column(db.String(64), nullable=False, unique=True)
    nickname = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=True)

@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous():
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, nickname=username, email=email)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('homepage'))

@app.route('/authorize/<provider>')
def oauth_authorize(provider):	
    if not current_user.is_anonymous():
        return redirect(url_for('currenttrends'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('homepage'))


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/hashtagtrend', methods = ['POST'])
def hashtagtrends():
    keyword = request.form['keyword']
    keyword = keyword.lower()
    trend_timebucket_table = Table('trend_geo')
    all_results = trend_timebucket_table.query_2(hashtag__eq=keyword)
    data = [{"timebucket":int(res["timebucket"]), "lat":float(res["lat"]), "lng":float(res["lng"])} for res in list(all_results)]
    print data
    oldest_timebucket = int(list(trend_timebucket_table.query_2(hashtag__eq=keyword, limit=1))[0]['timebucket'])
    newest_timebucket = int(list(trend_timebucket_table.query_2(hashtag__eq=keyword, reverse=True, limit=1))[0]['timebucket'])
    return render_template('hashtagtrend.html', keyword=keyword, data=json.dumps(data), oldest_timebucket=oldest_timebucket, newest_timebucket=newest_timebucket)


@app.route('/currenttrends')
def currenttrends():
    return render_template('currenttrends.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/favorites')
def favorites():
    return render_template('favorites.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/user', methods = ['POST'])
def user():
    print "here?"
    #getting stuff about user bc i am a STALKER~
    user_handle = request.form['user_handle']
    # request user analytics from backend service
    params = {"uname": user_handle, "stat": 0}
    r = requests.get('http://reach-backend.elasticbeanstalk.com:2678/data', params=params)
    if r.text == unicode("OK"):
        params = {"uname": user_handle, "stat": 1}
        r = requests.get('http://reach-backend.elasticbeanstalk.com:2678/data', params=params)
        user_analytics = json.loads(r.text)
    else:
        #TODO handle case when backend service response has non-200 status
        pass
    user_handle = user_handle.lower()
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret) 
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    user = api.get_user(user_handle)
    
    short = user.profile_image_url
    description = user.description
    followers_count = user.followers_count
    following_count = user.friends_count
    big_url  = short.split("_normal.jpg")
    big_url = big_url[0]+"_400x400.jpg"
    print big_url
    return render_template('user.html', 
        big_url=big_url,
        user_handle=user_handle, 
        followers_count =followers_count,
        following_count = following_count,
        description=description)

@app.route('/login')
def login():
    return render_template('login.html')


class StdOutListener(tweepy.StreamListener,):
    def __init__(self):
        self.max=100000

    def on_data(self, data):
        decoded = json.loads(data)
        lat = None
        lng = None
        if 'user' in decoded:
            if decoded["coordinates"] is None:
                #print "no coordinates"
                if decoded['place'] is None:
                    print "no place"
                else:
                    corner = decoded['place']['bounding_box']['coordinates'][0][0]
                    lat = corner[1]
                    lng = corner[0]
            else:
                lat= decoded['coordinates']['coordinates'][1]
                lng = decoded['coordinates']['coordinates'][0]
            #print "lat: {lt}, lng: {lg}".format(lt=lat,lg=lng)
            hashtags = decoded['entities']['hashtags']
            if (lat is not None) and (lng is not None) and (len(hashtags) > 0):
                # enqueue 
                tags = "#".join([htag['text'].encode('utf-8', 'ignore') for htag in hashtags])
                m = Message()
                body = str(lat) + "|" + str(lng) + "|" + tags
                m.set_body(body)
                reachqueue.write(m)
        return True

    def on_error(self, status):
        print status


def enqueue_tweets():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret) 
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    l = StdOutListener()
    while True:
        try:
            stream = tweepy.Stream(auth, l)
            stream.filter(locations=[-179.9,-89.9,179.9,89.9])
        except:
            time.sleep(120)
            continue

def dequeue_tweets():
    while True: 
        # dequeue
        msg = reachqueue.get_messages()
        while len(msg) > 0:
            msg_body = msg[0].get_body()
            #after we get the body, delete the message
            reachqueue.delete_message(msg[0])
            #body looks like: lng|lat|text
            tweet_arr = msg_body.split("|")
            lat = tweet_arr[0]
            lng = tweet_arr[1]
            tags = tweet_arr[2]
            hashtags = tags.split('#') 
            for htag in hashtags:
                geodata = {'lat': lat, 'lng': lng}
                socketio.emit(htag.lower(), geodata, namespace = '/test')
            msg = reachqueue.get_messages()

@socketio.on('my event', namespace='/test')
def test_message(message):
    session['recieve_count'] = session.get('receive_count', 0) + 1

def process_spark_output():
    trend_timebucket_table = Table('trend_geo')
    print "process_spark_output"
    s3conn = boto.connect_s3()
    while True:
        # dequeue
        fetched_messages = spark_notifications.get_messages()
        if len(fetched_messages) > 0:
            msg = fetched_messages[0]
            notification = json.loads(msg.get_body().encode("utf-8"))
            spark_notifications.delete_message(msg)
            bucket_name = notification['Records'][0]['s3']['bucket']['name']
            object_name = notification['Records'][0]['s3']['object']['key'] 
            if "SUCCESS" in object_name:
                continue
            else:
                # extract timebucket from object name
                timebucket = int(object_name.split(".")[0][1:-3])
                # read contents of S3 object
                bucket = s3conn.get_bucket(bucket_name)
                s3_object = bucket.get_key(object_name)
                events = [s.strip() for s in s3_object.get_contents_as_string().split(")))") if s.strip()]
                for event in events:
                    tmp = event.split(",ArrayBuffer")
                    hashtag = tmp[0][1:].lower()
                    parse_for_entries = tmp[1].split("UTC 2015")
                    for entry in parse_for_entries:
                        if "," in entry:
                            lat = entry.split(",")[1].replace("(","").replace(")","")
                            lng = entry.split(",")[2].replace("(","").replace(")","")
                    """
                    print "hashtag: {}".format(hashtag)
                    print "timebucket: {}".format(timebucket)
                    print "lat: {}".format(lat)
                    print "lng: {}".format(lng)
                    """
                    if (hashtag and timebucket and lat and lng):
                        item = {'hashtag': hashtag,
                            'timebucket': timebucket,
                            'lat': lat,
                            'lng': lng}
                        try:
                            trend_timebucket_table.put_item(data=item)
                        except Exception as inst:
                            print inst.args
                        except:
                            print "Unexpected error:", sys.exc_info()[0]
        else:
            time.sleep(300)

def runThreads():
    # run thread to listen to Twitter Streaming API
    spark_output_processor = threading.Thread(target=process_spark_output)
    spark_output_processor.start()
    enqueue_worker = threading.Thread(target=enqueue_tweets)
    enqueue_worker.start()
    num_sqs_consumers = 6
    for cons in range(num_sqs_consumers):
        dequeue_worker = threading.Thread(target=dequeue_tweets)
        dequeue_worker.start()

if __name__ == '__main__':
    db.create_all() 
    app.before_first_request(runThreads)
    print "debug 1"
    socketio.run(app)

