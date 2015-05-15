from flask import Flask, render_template, request, redirect, g, url_for
import json
from rauth import OAuth2Service
from flask.ext.login import LoginManager, UserMixin, login_user, logout_user, current_user
from oauth import OAuthSignIn
from flask.ext.login import LoginManager, UserMixin
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.socketio import SocketIO, emit

app = Flask(__name__)

socketio = SocketIO(app)
db = SQLAlchemy(app)

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
    print "test1"
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
    print keyword
    #db= []
    #db.append([lat, lng, timebucket])
    #return render_template('hashtagtrend.html', db=db)
    # TODO send `keyword` to template so client can
    # register an event handler for that specific keyword
    return render_template('hashtagtrend.html')


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

def enqueue_tweets():
    # enqueue all tweets
    pass

def dequeue_tweets():
    # TODO enclose in while loop
    # pick up message from SQS
    hashtags = []
    # extract any hashtags from tweet text
    for word in [tweettext].split(" "):
        if word.startswith("#"):
            hashtags.append(word)
    for each hashtag:
        geodata = {'lat': tweet.lat, 'lng': tweet.lng}
        socketio.emit(hashtag, geodata)

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
	socketio.run(app, host='0.0.0.0', port=5004)

