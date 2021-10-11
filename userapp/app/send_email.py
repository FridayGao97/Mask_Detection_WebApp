from flask_mail import Mail, Message
import random
import string

from flask import render_template, redirect, url_for, request, g
from app import webapp

import mysql.connector

import sys
import os

from werkzeug.utils import secure_filename
from app import hash
from app.db_config import db_config

from app import http

webapp.config['MAIL_SERVER']='smtp.gmail.com'
webapp.config['MAIL_PORT'] = 465
webapp.config['MAIL_USERNAME'] = 'UofT.QXZ.SXG@gmail.com'
webapp.config['MAIL_PASSWORD'] = 'ece17791019'
webapp.config['MAIL_USE_TLS'] = False
webapp.config['MAIL_USE_SSL'] = True

#initialize mail object
mail = Mail(webapp)

#connect to DB
def connect_to_database():
    
    return mysql.connector.connect(user = db_config['user'],
                                   password = db_config['password'],
                                   host = db_config['host'],
                                   database = db_config['database'],
                                   autocommit = True,
                                   auth_plugin='mysql_native_password')

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



def get_random_pswd(length):
    # Random string with the combination of lower and upper case
    letters = string.ascii_letters
    randmstr = ''.join(random.choice(letters) for i in range(length))
    print("Random string is:", randmstr)
    return randmstr

#check the email provided is registered before or not
def checkEmail(uemail):
    cnx = get_db()
    cursor = cnx.cursor()
    query = "SELECT user_id FROM user WHERE email = %s"

    cursor.execute(query,(uemail,))
    #if not registered
    if cursor.fetchone() == None:
        return False
    #if registered
    return True

#upload the random passwords to DB
def updatePswdToDB(uemail, pswd):
    hashed_password = hash.hash_new_password(pswd)
    cnx = get_db()
    cursor = cnx.cursor()

    query = '''SELECT * FROM user WHERE email = %s '''
    cursor.execute(query,(uemail,))

    if cursor.fetchone() != None:
        query = ''' UPDATE user SET password=%s 
                WHERE email = %s '''

        cursor.execute(query,(hashed_password,uemail))
        cnx.commit()

@webapp.route('/recovery')
def recoverByEmail():
    http.record_requests()
    return render_template('recovery.html')

#send emial with password generated randomly
@webapp.route("/email", methods=["POST"])
def send_email():

    http.record_requests()

    #recipient's email
    toEmail = request.form.get('email', "")
    if toEmail == "":
        return "Error: All fields are required!"
    #check registered before
    if(checkEmail(toEmail) == False):
        return "Error: This emial is registered before! Please check again"

    temp_pswd = get_random_pswd(8)
    
    msg = Message(subject="Recoved Passwrods from ECE1779Project1", sender = 'UofT.QXZ.SXG@gmail.com', recipients = [toEmail])
    msg.body = "We have resetted the passwords for you, and The Reset Password is : " + temp_pswd
    
    updatePswdToDB(toEmail,temp_pswd)

    mail.send(msg)
    print("~~~Send!!!")
    temp_mesg = 'The password has been sent to the email (%s), Please check the Inbox or Spam' % (toEmail)
    return render_template('recovery.html', message=temp_mesg)