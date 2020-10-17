from flask import render_template, redirect, url_for, request, g
from app import webapp

import mysql.connector

import sys
import os

from werkzeug.utils import secure_filename


from app.pytorch_infer import runDetection
from app import hash
#from app import db_config
from app.db_config import db_config

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

maskclass = {0: 'No Face', 1: 'No Mask', 2: 'All faces with Masks', 3: 'Some faces with Mask'}


def mask_detection(imgPath):
    print("Panth:", imgPath)
    res = runDetection(imgPath)
    return res


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


def checkUsers(username,password):
    hashed_password = hash.hash_new_password(password)
    cnx = get_db()
    cursor = cnx.cursor()
    query = "SELECT user_id, password FROM user WHERE user_name = %s"

    cursor.execute(query,(username,))
    
    row = cursor.fetchone()
    user_id = row[0]
    dbpassword = row[1]

    if hashed_password == dbpassword:
        return user_id
    return -1

    

def uploadImgToDB(uid,fileName,category):
    print("UPTODB: uid ",uid)
    imgpath = os.path.join(webapp.config['SOLUTION_FOLDER'],fileName)
    cnx = get_db()
    cursor = cnx.cursor()
    query = '''SELECT photo_id FROM photo WHERE photo_id = %s '''
    cursor.execute(query,(imgpath,))
    if cursor.fetchone() == None:
        query = ''' INSERT INTO photo (photo_id,category,user_id)
                        VALUES (%s,%s,%s)
        '''
        cursor.execute(query,(imgpath,category,uid))
        cnx.commit()


@webapp.route('/upload-image')
def upload_image():
    return render_template("upload_photos.html")

@webapp.route('/get-image', methods=["POST"])
def get_image():
    username = request.form.get('username', "")
    password = request.form.get('password', "")
    if username == "" or password == "":
        return "Error: All fields are required!"
    
    #connect to db to verfity users
    uid = -1
    uid = checkUsers(username,password)
    print("userid is ",uid)
    if uid < 0:
        return "Error: Please input the correct username & passwords"

    #check if image uploaded
    if 'myFile' not in request.files: return redirect(request.url)
    file = request.files['myFile']

    if file.filename == '': return redirect(request.url)
	
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        #add user id tag to every image
        name, ext = os.path.splitext(filename)
        filename = name+"--"+ str(uid) + ext
        print("FileNameWithUID: ",filename)

        #save file to folder
        file.save(os.path.join(webapp.config['UPLOAD_FOLDER'], filename))

        #to run detection
        tempres = mask_detection(os.path.join(webapp.config['UPLOAD_FOLDER'], filename))
        tempmesg = tempres[1]
        outputfile = tempres[0]
        
        
        #upload to db
        uploadImgToDB(uid,outputfile,tempmesg)

        
        return render_template('upload_photos.html', filename=outputfile, uid=uid, message = 'Image successfully uploaded and displayed!  ||  The Result: ' + maskclass[tempmesg] )
	
    else:
        return redirect(request.url)



@webapp.route('/display/<filename>')
def display_image(filename):
	#print('display_image filename: ' + filename)
	return redirect(url_for('static', filename='solutions/' + filename), code=301)

