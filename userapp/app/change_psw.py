from flask import render_template, request, g
from app import webapp
import mysql.connector
from app.db_config import db_config
from app import hash
import sys

from app import http

#functions for database, those are similar across all py file who need to connect with DB
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

@webapp.route('/new_psw', methods = ['GET'])
# display a web page that allows users to change their passwords after their old passwords are confirmed
def change_psw():
    http.record_requests()
    return render_template("new_psw.html", title="Change Password")

@webapp.route('/new_psw', methods = ['POST'])
# save the new password into the database after the old password is confirmed
def change_psw_save():
    #get input
    name = request.form.get('name', "")
    old_psw = request.form.get('oldpassword', "")
    new_psw_1 = request.form.get('new1password', "")
    new_psw_2 = request.form.get('new2password', "")

    #check
    if name == '' or old_psw == '' or new_psw_1 == '' or new_psw_2 == '':
        return "Error: All fields are required!"

    #connect to DB
    cnx = get_db()
    cursor = cnx.cursor()
    cnx.start_transaction()

    query = "SELECT password FROM user WHERE user_name = %s"
    cursor.execute(query, (name,))
    row = cursor.fetchone()
    http.record_requests()

    if row == None:
        return "Wrong username!"

    else:
        real_psw = row[0]
        old_psw_hashed = hash.hash_new_password(old_psw)
        #if old passwords matches, salt and has new password and go back to login page
        if old_psw_hashed == real_psw:
            if new_psw_1 == new_psw_2:
                new_psw_hashed = hash.hash_new_password(new_psw_1)
                query = "UPDATE user SET password = %s WHERE user_name = %s"
                cursor.execute(query, (new_psw_hashed, name))
                cnx.commit()
                return render_template("main.html", title="Welcome to the System of Face Mask Detection")
            else:
                cnx.rollback()
                return "New passwords don't match!"
        else:
            cnx.rollback()
            return "Wrong old password!"