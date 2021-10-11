from flask import render_template, request, redirect,jsonify, url_for, g
from app import webapp
import mysql.connector
from app.db_config import db_config
from app import hash
import re 

from app import http
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


@webapp.route('/delete')
# display a web page that allows users to register their names, emails and passwords
def user_delete():
    http.record_requests()
    return render_template("delete.html",title="Delete")


@webapp.route('/delete-verify', methods=['POST'])
# create a new user and save them into the database
def user_delete_save():
    name = request.form.get('username', "")
    password = request.form.get('password', "")
    hashed_password = hash.hash_new_password(password)
    http.record_requests()

    if name == '' or password == '':
        return "Error: All fields are required!"

    cnx = get_db()
    cursor = cnx.cursor()

    query = "SELECT user_id, password FROM user WHERE user_name=%s"
    
    cursor.execute(query, (name,))
    row = cursor.fetchone()
    if(row):
        user_id = row[0]
        dbpassword = row[1]
        if hashed_password == dbpassword:
            print("123")
            query = "DELETE FROM user WHERE user_id=%s"
            cursor.execute(query, (user_id,))
            cnx.commit()
            return render_template("delete.html",message="true")
        else:
            return "Error: Deleting Failed"
    else:
        return "Error: Deleting Failed"



