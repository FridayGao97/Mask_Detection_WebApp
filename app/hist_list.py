from flask import render_template, redirect, url_for, request, g
from app import webapp
import os
import mysql.connector

#import urllib.request

#from app.config import db_config
import sys
import os
from app.db_config import db_config

from werkzeug.utils import secure_filename
maskclass = {0: 'No Face', 1: 'No Mask', 2: 'All faces with Masks', 3: 'Some faces with Mask'}

def connect_to_database():
    # return mysql.connector.connect(user = db_config['user'],
    #                                password = db_config['password'],
    #                                host = db_config['host'],
    #                                database = db_config['database'],
    #                                autocommit = True)
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


'''
<form action="{{url_for('user_pages',id=row[0])}}" method='get'>
    <input type='submit' value='Details' />
</form>
'''
@webapp.route('/user-page/<int:id>',methods=['GET'])
def user_pages(id):
    #check admin
    cnx = get_db()
    cursor = cnx.cursor()

    query = "SELECT user_id, user_name, admin FROM user WHERE user_id = %s"

    cursor.execute(query,(id,))
    row = cursor.fetchone()
    print("user row:", row)
    uid = row[0]
    uname = row[1]
    admin = row[2]

    query = '''SELECT photo_id, category
               FROM photo 
               WHERE user_id= %s'''

    NFphotos = []
    NMphotos = []
    SMphotos = []
    AMphotos = []

    cursor.execute(query,(uid,))
    
    for row in cursor:
        print("photo DB row:",row)
        if(int(row[1]) == 0):
            head, tail = os.path.split(row[0]) 
            NFphotos.append(tail)
        elif(int(row[1]) == 1):
            head, tail = os.path.split(row[0]) 
            NMphotos.append(tail)
        elif(int(row[1]) == 2):
            head, tail = os.path.split(row[0]) 
            AMphotos.append(tail)
            print("RIGHTHERE")
        elif(int(row[1]) == 3):
            head, tail = os.path.split(row[0]) 
            SMphotos.append(tail)
        else:
            return "Error: No categoty fitted"
    if admin == '0\x00':
        return render_template("admin.html",title="Upload history",
                           id=uid,
                           username=uname,
                           NFphotos=NFphotos,
                           NMphotos=NMphotos,
                           AMphotos=AMphotos, SMphotos=SMphotos)
    else:
        return render_template("users.html", title="Upload history",
                           username=uname,
                           NFphotos=NFphotos,
                           NMphotos=NMphotos,
                           AMphotos=AMphotos, SMphotos=SMphotos)


@webapp.route('/history/<filename>')
def display_history(filename): 
    print("history image:",filename) 
    return redirect(url_for('static', filename='solutions/' + filename), code=301)



    
    







    
    

