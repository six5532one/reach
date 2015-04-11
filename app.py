from flask import Flask, render_template, request, redirect, g 
import json

app = Flask(__name__)

@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route('/currenttrends.html')
def homepage():
    return render_template('homepage.html')

if __name__ == '__main__':
    app.run()

