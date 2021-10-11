from flask import render_template, redirect, url_for, jsonify,request, g
from app import webapp

import mysql.connector

import sys
import os
import urllib

from werkzeug.utils import secure_filename

from app.pytorch_infer import runDetection
from app import hash
from app.db_config import db_config

from app import http

#photo extension
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#mask category
maskclass = {0: 'No Face', 1: 'No Mask', 2: 'All faces with Masks', 3: 'Some faces with Mask'}

#mask detection from pytorch_infer.py
def mask_detection(imgPath):
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

#check user is vaild or not
def checkUsers(username,password):
    hashed_password = hash.hash_new_password(password)
    cnx = get_db()
    cursor = cnx.cursor()
    query = "SELECT user_id, password FROM user WHERE user_name = %s"

    cursor.execute(query,(username,))
    
    row = cursor.fetchone()
    if(row):
        user_id = row[0]
        dbpassword = row[1]

        if hashed_password == dbpassword:
            return user_id
    return -1

    
#upload the relative path of image to table photo as photo_id in database
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

import boto3
def upload_file_S3(file_name):
    """
    Function to upload a file to an S3 bucket
    """
    object_name = file_name

    s3_client = boto3.client('s3')
    #s3_client = boto3.client('s3',
    #               aws_access_key_id='ASIAZ4DEBL2APNQGQTHS',
    #               aws_secret_access_key='TUjqJpEl5NB4ctgcv9kmTqdP7zjOSRavCwha0q5D',
    #               aws_session_token='FwoGZXIvYXdzEFUaDPf62MHe2V6lGR8ctyLMAYuaGBke6VTC44p/vEi7/kiHlzFe/TREBgG5D1UXNvAVb3eP383WBJkaKvO4JdeLIjJmA2rtV1gaeXgH0+hY7lKJOlA99IvxmLa6FUosfZ21EkLJeDg6pgC9Un4mhycB5ra+gEcRWF8R54+kXQuNzeN8VK5HpIfiaT5ikEo63TzBfm98CGNXnEUVm0fj7y37GN2cVwHK7LmJCx3V0twv0+fbrbciLGsvYe4WcOpZju/TazWYLd6Rw3fAYfPWmgYn5lcAFKa8MkcwAFfgRyi3oLb9BTItbSAnBJ90K8nDZYTDKfJxKGKa/tvNBOueA0alJTcvwh3Vxuo52QEnAh/iR7fbs'
    #               )

    response = s3_client.upload_file(
                    Bucket='ece1779-a2',
                    Filename=object_name,
                    Key=object_name
                )

    return response


@webapp.route('/upload')
def upload_image():
    http.record_requests()
    return render_template("upload_photos.html")

#get the user name, passwords and photos from website and check validation 
@webapp.route('/get-image', methods=["POST"])
def get_image():

    http.record_requests()

    username = request.form.get('username', "")
    password = request.form.get('password', "")
    imgurl = request.form.get('imgurl', "")
    if username == "" or password == "":
        return "Error: All fields are required!"
    
    #connect to db to verfity users
    uid = -1
    uid = checkUsers(username,password)
    print("userid is ",uid)
    if uid < 0:
        return "Error: Please input the correct username & passwords"
    
    filename = ''
    print("imgurl", imgurl)

    file = request.files['file']
    #check if image uploaded
    #if 'file' not in request.files:
    if file.filename == '':
        if imgurl == "":
            return "Error1: Missing uploading image!"
        else:
            filename = os.path.basename( os.path.realpath(imgurl) )
            if allowed_file(filename):
                #add user id as a tag to every image filename
                name, ext = os.path.splitext(filename)
                filename = name+"--"+ str(uid) + ext
                req = urllib.request.Request(imgurl)
                try:
                    response = urllib.request.urlopen(req)
                    with open(os.path.join(webapp.config['UPLOAD_FOLDER'], filename), 'wb' ) as fo:
                        fo.write( response.read() )

                except urllib.error.URLError as e:
                    if hasattr( e, 'reason' ):
                        print( 'Fail in reaching the server -> ', e.reason )
                        return "Error: Failed to save url image!"
                    elif hasattr( e, 'code' ):
                        print( 'The server couldn\'t fulfill the request -> ', e.code )
                        return "Error: Failed to save url image!"
            else:
                return "Error: Uploading a wrong type, please uploading image again!"

    else:
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            #add user id as a tag to every image filename
            name, ext = os.path.splitext(filename)
            filename = name+"--"+ str(uid) + ext
            print("FileNameWithUID: ",filename)

            #save file to folder
            file.save(os.path.join(webapp.config['UPLOAD_FOLDER'], filename))
        else:
            return "Error: Uploading a wrong type, please uploading image again!"


    #check size
    size = os.stat(os.path.join(webapp.config['UPLOAD_FOLDER'], filename)).st_size
    #byte to mB
    size = size / (1024*1024)
    #set the threshold image size 8MB
    if(size > 8):
        #delete images in temp folder
        if os.path.exists("app/static/uploads/"+filename):
            os.remove("app/static/uploads/"+filename)
        return "Error: Image is too big!"

    #to run detection
    tempres = mask_detection(os.path.join(webapp.config['UPLOAD_FOLDER'], filename))
    
    #information for display
    outputfile = tempres[0]
    tempmesg = tempres[1]
    num_face = tempres[2]
    num_maksed = tempres[3]
    num_unmasked = tempres[4]
    
    
    #upload to db
    uploadImgToDB(uid,outputfile,tempmesg)

    #upload to S3
    imgpath = os.path.join(webapp.config['SOLUTION_FOLDER'],outputfile)
    print('OUT ', imgpath)
    upload_file_S3(imgpath)


        
    return render_template('upload_photos.html', filename=outputfile, uid=uid, message = 'Image successfully uploaded and displayed!  ||  The Result: ' + maskclass[tempmesg],num_face=num_face,num_maksed=num_maksed,num_unmasked=num_unmasked)
	


@webapp.route('/display/<filename>')
def display_image(filename):

    http.record_requests()

    #print('display_image filename: ' + filename)
    return redirect(url_for('static', filename='solutions/' + filename), code=301)




webapp.config['JSON_SORT_KEYS'] = False
#Same function as above, but for API testing and does not store test result to Database
@webapp.route('/api/upload',methods=["POST"])
def get_image_API():
    username = request.form.get('username', "")
    password = request.form.get('password', "")
    imgurl = request.form.get('imgurl', "")
    if username == "" or password == "":
        return "Error: All fields are required!"
    
    #connect to db to verfity users
    uid = -1
    uid = checkUsers(username,password)
    print("userid is ",uid)
    if uid < 0:
        return "Error: Please input the correct username & passwords"
    filename = ''
    print("imgurl", imgurl)

    file = request.files['file']

    #check if image uploaded
    #if 'file' not in request.files:
    if file.filename == '':
        if imgurl == "":
            return "Error1: Missing uploading image!"
        else:
            filename = os.path.basename( os.path.realpath(imgurl) )
            if allowed_file(filename):
                #add user id as a tag to every image filename
                name, ext = os.path.splitext(filename)
                filename = name+"--"+ str(uid) + ext
                req = urllib.request.Request(imgurl)
                try:
                    response = urllib.request.urlopen(req)
                    with open(os.path.join(webapp.config['UPLOAD_FOLDER'], filename), 'wb' ) as fo:
                        fo.write( response.read() )

                except urllib.error.URLError as e:
                    if hasattr( e, 'reason' ):
                        print( 'Fail in reaching the server -> ', e.reason )
                        return "Error: Failed to save url image!"
                    elif hasattr( e, 'code' ):
                        print( 'The server couldn\'t fulfill the request -> ', e.code )
                        return "Error: Failed to save url image!"
            else:
                return "Error: Uploading a wrong type, please uploading image again!"

    else:
       
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            #add user id as a tag to every image filename
            name, ext = os.path.splitext(filename)
            filename = name+"--"+ str(uid) + ext
            print("FileNameWithUID: ",filename)

            #save file to folder
            file.save(os.path.join(webapp.config['UPLOAD_FOLDER'], filename))
        else:
            return "Error: Uploading a wrong type, please uploading image again!"


    #check size
    size = os.stat(os.path.join(webapp.config['UPLOAD_FOLDER'], filename)).st_size
    #byte to mB
    size = size / (1024*1024)
    #set the threshold image size 8MB
    if(size > 8):
        #delete images in temp folder
        if os.path.exists("app/static/uploads/"+filename):
            os.remove("app/static/uploads/"+filename)
        return "Error: Image is too big!"

    #to run detection
    tempres = mask_detection(os.path.join(webapp.config['UPLOAD_FOLDER'], filename))
    
    #information for display
    outputfile = tempres[0]
    tempmesg = tempres[1]
    num_face = tempres[2]
    num_maksed = tempres[3]
    num_unmasked = tempres[4]
    
    
    #upload to db
    uploadImgToDB(uid,outputfile,tempmesg)

    
    return render_template('upload_photos.html', filename=outputfile, uid=uid, message = 'Image successfully uploaded and displayed!  ||  The Result: ' + maskclass[tempmesg],num_face=num_face,num_maksed=num_maksed,num_unmasked=num_unmasked)



