from flask import render_template, url_for
from app import webapp

import mysql.connector

#from app.config import db_config
import sys

@webapp.route('/')
def main():
    return render_template("main.html")