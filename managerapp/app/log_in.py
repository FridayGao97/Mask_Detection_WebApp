from flask import render_template, request, redirect, url_for, g
from app import webapp

from app.aws import awsClient
client = awsClient()

@webapp.route('/login', methods = ['GET'])
# display a web page that allows users to enter their names and passwords to log into the system
def user_login():
    
    # res = client.shrink_worker_by_one()
    # while (res[0] == True ):
    #     res = client.shrink_worker_by_one()

    return render_template("login.html", title="Welcome to the Manager System")

@webapp.route('/login-check', methods = ['POST'])
# determine whether or not to log in the users by checking whether their entered passwords match their registered passwords
def user_login_main():
    name_enter = request.form.get('name', "")
    password_enter = request.form.get('password', "")
    print(name_enter)

    res = client.shrink_worker_by_one()
    while (res[0] == True ):
        print(res)
        res = client.shrink_worker_by_one()

    if name_enter == '' or password_enter == '':
        return "Error: All fields are required!"
    else:
        if name_enter == 'admin' or name_enter == 'Admin':
            if password_enter == 'admin':
                return redirect(url_for('main_pages'))
            else:
                return "Error: password is wrong"
        else:
            return "Error: name is wrong"
