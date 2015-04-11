from flask import Flask, render_template, request, redirect, g, url_for
import json
from rauth import OAuth2Service
from flask.ext.login import LoginManager, UserMixin, login_user, logout_user, current_user
from oauth import OAuthSignIn
from flask.ext.login import LoginManager, UserMixin
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)


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



if __name__ == '__main__':
	db.create_all()
	app.run(debug=True)

