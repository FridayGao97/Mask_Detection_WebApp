from flask import render_template, request, redirect,jsonify, url_for, g
from app import webapp
import mysql.connector
from app.db_config import db_config
from app import hash
import re 

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


@webapp.route('/register')
# display a web page that allows users to register their names, emails and passwords
def user_register():

    http.record_requests()

    return render_template("register.html",title="Register")


@webapp.route('/register-verify', methods=['POST'])
# create a new user and save them into the database
def user_register_save():

    http.record_requests()

    name = request.form.get('username', "")
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
        return "success: False, This name has already been used!"

    query = "SELECT * FROM user WHERE email=%s"
    cursor.execute(query, (email,))
    if cursor.fetchone() != None:
        return "success: False, This email has already been used!"

    else:
        
        # Make a regular expression 
        # for validating an Email 
        regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
        if (re.search(regex,email)):
            query = "INSERT INTO user (user_name, email, password, admin) VALUES (%s, %s, %s, 1)"
            cursor.execute(query, (name, email, hashed_password))
            cnx.commit()
        else:
            return "success: false, Please enter the email as email format."

    return render_template("register.html",message="true")




webapp.config['JSON_SORT_KEYS'] = False
@webapp.route('/api/register',methods=['POST'])
#Same function as above, but for API testing and does not store test result to Database
def user_register_API():
    name = request.form.get('username', "")
    email = request.form.get('email', "")
    password = request.form.get('password', "")
    hashed_password = hash.hash_new_password(password)

    if email == '':
        email = 'UofT.QXZ.SXG@gmail.com'

    if name == '' or password == '':
        return jsonify(success = "false", error = {"codes" : "if name == '' or password == ''", "message": "All fields are required!"})

    cnx = get_db()
    cursor = cnx.cursor()

    query = "SELECT * FROM user WHERE user_name=%s"
    cursor.execute(query, (name,))
    if cursor.fetchone() != None:
        return jsonify(success = "false", error = {"codes" : "cursor.execute('SELECT * FROM user WHERE user_name=%s', (name,)).fetchone() != None" , "message": "This name has already been used!"})

    # query = "SELECT * FROM user WHERE email=%s"
    # cursor.execute(query, (email,))
    # if cursor.fetchone() != None:
    #     return jsonify(success = "false", error = {"codes" : "cursor.execute('SELECT * FROM user WHERE emial=%s', (emial,)).fetchone() != None" , "message": "This email has already been used!"})
    
    else:
        
        # Make a regular expression 
        # for validating an Email 
        regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
        if (re.search(regex,email)):
            query = "INSERT INTO user (user_name, email, password, admin) VALUES (%s, %s, %s, 1)"
            cursor.execute(query, (name, email, hashed_password))
            cnx.commit()
            return jsonify(success = "true")
        else:
            return jsonify(success = "false", error = {"codes" : "re.search(regex,email)" , "message": "The typing email format is not obey the general email format!"})


