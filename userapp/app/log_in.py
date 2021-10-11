from flask import render_template, request, redirect, url_for, g
from app import webapp
import mysql.connector
from app.db_config import db_config
from app import hash
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


@webapp.route('/main', methods = ['GET'])
# display a web page that allows users to enter their names and passwords to log into the system
def user_login():
    http.record_requests()
    return render_template("main.html", title="Welcome to the System of Face Mask Detection")

@webapp.route('/main', methods = ['POST'])
# determine whether or not to log in the users by checking whether their entered passwords match their registered passwords
def user_login_main():

    http.record_requests()

    name_enter = request.form.get('name', "")
    password_enter = request.form.get('password', "")
    password_enter_hashed = hash.hash_new_password(password_enter)
    print(name_enter)

    if name_enter == '' or password_enter == '':
        return "Error: All fields are required!"

    cnx = get_db()
    cursor = cnx.cursor()

    query = "SELECT user_id, password FROM user WHERE user_name=%s"
    cursor.execute(query, (name_enter,))
    row = cursor.fetchone()
    print(row)

    if row == None:
        return "Wrong user name!"
    else:
        uid = row[0]
        password_real = row[1]
        if password_real == password_enter_hashed:
            print("LOG-IN: ", uid)
            return redirect(url_for('user_pages', id=uid))
        else:
            return "Wrong password!"