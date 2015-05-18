from flask import Flask, render_template, request, redirect, g, url_for
import json
from rauth import OAuth2Service
from flask.ext.login import LoginManager, UserMixin, login_user, logout_user, current_user
from oauth import OAuthSignIn
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.socketio import SocketIO, emit
import boto.sqs
import tweepy
import threading 
from threading import Thread
from boto.sqs.message import Message

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
    #db= []
    #db.append([lat, lng, timebucket])
    #return render_template('hashtagtrend.html', db=db)
    # TODO send `keyword` to template so client can
    # register an event handler for that specific keyword
    return render_template('hashtagtrend.html', keyword=keyword)


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
                tags = "#".join([htag['text'].encode('ascii', 'ignore') for htag in hashtags])
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
    l = StdOutListener()
    stream = tweepy.Stream(auth, l)
    stream.filter(locations=[-179.9,-89.9,179.9,89.9])

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

def runThreads():
    # run thread to listen to Twitter Streaming API
    enqueue_worker = threading.Thread(target=enqueue_tweets)
    enqueue_worker.start()
    # TODO change to higher number later
    num_sqs_consumers = 2
    for cons in range(num_sqs_consumers):
        dequeue_worker = threading.Thread(target=dequeue_tweets)
        dequeue_worker.start()

if __name__ == '__main__':
    db.create_all() 
    app.before_first_request(runThreads)
    print "debug 1"
    socketio.run(app)

