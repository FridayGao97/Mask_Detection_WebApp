from flask import render_template, url_for
from app import webapp

import sys

import threading
import time
from app.home import auto_scaling

@webapp.route('/')
def main():
    thread = threading.Thread(target=auto_scaling, args=())
    thread.daemon = True
    thread.start()

    return render_template("login.html")