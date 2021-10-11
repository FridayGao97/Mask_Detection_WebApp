import requests
from app import webapp
import mysql.connector
from flask import g
from pytz import timezone
import time
from datetime import datetime, timedelta
from app.db_config import db_config

def connect_to_database():
    return mysql.connector.connect(user = db_config['user'],
                                   password = db_config['password'],
                                   host = db_config['host'],
                                   database = db_config['database'],
                                   autocommit = True)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db

@webapp.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def record_requests():


    response = requests.get('http://169.254.169.254/latest/meta-data/instance-id')
    instance_id = ''+ response.text

    cnx = get_db()
    cursor = cnx.cursor()
    timestamp = datetime.now(timezone('Canada/Eastern'))

    query = "INSERT INTO http_req (instanceID, timestamp) VALUES (%s, %s)"
    cursor.execute(query, (instance_id, timestamp))
    cnx.commit()

