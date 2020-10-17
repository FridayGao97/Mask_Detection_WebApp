from flask import render_template, request, redirect, url_for, g
from app import webapp
import mysql.connector
from app.db_config import db_config
from app import hash

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

@webapp.route('/register/<int:id>', methods=['GET'])
# display a web page that allows users to register their names, emails and passwords
def user_register(id):
    return render_template("register.html", id=id,title="Register")

@webapp.route('/register-verify/<int:id>', methods=['POST'])
# create a new user and save them into the database
def user_register_save(id):
    adminID = id
    name = request.form.get('name', "")
    email = request.form.get('email', "")
    password = request.form.get('password', "")
    hashed_password = hash.hash_new_password(password)

    if name == '' or email == '' or password == '':
        return "Error: All fields are required!"

    cnx = get_db()
    cursor = cnx.cursor()

    query = "SELECT * FROM user WHERE user_name=%s"
    cursor.execute(query, (name,))
    if cursor.fetchone() != None:
        return "This name has already been used!"

    query = "SELECT * FROM user WHERE email=%s"
    cursor.execute(query, (email,))
    if cursor.fetchone() != None:
        return "This email has already been used!"

    else:
        query = "INSERT INTO user (user_name, email, password, admin) VALUES (%s, %s, %s, 1)"
        cursor.execute(query, (name, email, hashed_password))
        cnx.commit()

    return redirect(url_for('user_pages', id=adminID))