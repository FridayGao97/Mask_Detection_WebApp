from flask import render_template, url_for, session, redirect, request
from app import webapp

from datetime import datetime, timedelta

import collections

from app.aws import awsClient

import threading
from pytz import timezone,utc
import time
from datetime import datetime, timedelta


import requests
from app import webapp
import mysql.connector
from flask import g
from pytz import timezone
import time
from datetime import datetime, timedelta
from app.db_config import db_config
import collections


ZONE = 'Canada/Eastern'

global default_CPU_grow
global default_CPU_shrink
global default_ratio_grow
global default_ratio_shrink
default_CPU_grow = 40
default_CPU_shrink = 20
default_ratio_grow = 2.0
default_ratio_shrink = 0.5

global client
client = awsClient()

@webapp.route('/home', methods = ['GET'])
# display a web page that allows users to enter their names and passwords to log into the system
def main_pages():
    valid_workers = client.get_workers()
    try:
        valid_workers=client.get_workers()
        if len(valid_workers)<1:
            client.grow_worker_by_one()
    except Exception as e:
        return "Error: Cannot initialize the manager app"
    
    #table
    worker_pool = client.get_workers()

    worker_data = {}
    worker_data['ID'] = []
    worker_data['port'] = []
    worker_data['state'] = []

    for item in worker_pool:
        worker_data['ID'].append(item['Id'])
        worker_data['port'].append(item['Port'])
        worker_data['state'].append(item['State'])

    worker_data = zip(worker_data['ID'], worker_data['port'], worker_data['state'])

    #number of workers' chart, x:time, y:#workers
    numlabels = []
    numvalues = []
    end_time = datetime.now(timezone(ZONE))
    start_time = end_time - timedelta(seconds=1800)

    datapoints = client.count_workers(start_time,end_time)
    temp = map(lambda x: [int(int(x[0])/1000),float(x[1])], datapoints)
    temp = list(temp)
    temp = sorted(temp, key=lambda x: x[0])

    for workeritem in temp:
        #only higher than python3.3
        dt_object = datetime.fromtimestamp(workeritem[0])
        date_zone = dt_object.astimezone(timezone(ZONE))
        
        numlabels.append("%s:%s"%(date_zone.hour, date_zone.minute))
        numvalues.append(workeritem[1])

    #numlabels = [ '17:10', '17:20', '17:30','17:40','17:50','17:60' ]
    #numvalues = [967.67, 1190.89, 1079.75, 1349.19, 2328.91, 2504.28]


    return render_template('mainpage.html', worker_data=worker_data, max=10, numlabels=numlabels, numvalues=numvalues)
    

@webapp.route('/instance-chhart/<instance_id>')
def instance_charts(instance_id):
    instance_id = instance_id
    
    #CPU utilization chart, x:time, y:CPU 
    CPUlabels = []
    CPUvalues = []
    end_time = datetime.now(timezone(ZONE))
    start_time = end_time - timedelta(seconds=1800)

    datapoints = client.get_cpu(instance_id, start_time,end_time)
    temp = map(lambda x: [int(int(x[0])/1000),float(x[1])], datapoints)
    temp = list(temp)
    temp = sorted(temp, key=lambda x: x[0])

    for CPUitem in temp:
        #only higher than python3.3
        dt_object = datetime.fromtimestamp(CPUitem[0])
        date_zone = dt_object.astimezone(timezone(ZONE))
        
        CPUlabels.append("%s:%s"%(date_zone.hour, date_zone.minute))
        CPUvalues.append(CPUitem[1])

    #CPUlabels = [ '17:10', '17:20', '17:30','17:40','17:50','17:60' ]
    #CPUvalues = [967.67, 1190.89, 1079.75, 1349.19, 2328.91, 2504.28]
    #HTTP request chart, x:time, y:CPU

    
    Reqlabels = []
    Reqvalues = []
    Reqend_time = datetime.now(timezone(ZONE))
    Reqstart_time = Reqend_time - timedelta(seconds=1800)

    Reqdatapoints = fetch_reqeusts_rate(instance_id, Reqstart_time,Reqend_time)
    #Reqdatapoints = client.get_http(instance_id, Reqstart_time,Reqend_time)
    Reqtemp = map(lambda x: [int(int(x[0])/1000),float(x[1])], Reqdatapoints)
    Reqtemp = list(Reqtemp)
    Reqtemp = sorted(Reqtemp, key=lambda x: x[0])

    for Reqitem in Reqtemp:
        #only higher than python3.3
        dt_object = datetime.fromtimestamp(Reqitem[0])
        date_zone = dt_object.astimezone(timezone(ZONE))
        
        Reqlabels.append("%s:%s"%(date_zone.hour, date_zone.minute))
        Reqvalues.append(Reqitem[1])
    

    #Reqlabels = ['17:10', '17:20', '17:30', '17:40', '17:50', '17:60']
    #Reqvalues = [967.67, 1190.89, 1079.75, 1349.19, 2328.91, 2504.28]



    return render_template('instance_charts.html', id=instance_id, max=100, CPUlabels=CPUlabels, CPUvalues=CPUvalues, Reqlabels=Reqlabels, Reqvalues=Reqvalues )

@webapp.route('/home')
def refresh_page():
    return main_pages()

@webapp.route('/grow-worker-pool', methods = ['POST'])
def grow_pool():
    print("grow")
    res = client.grow_worker_by_one()
    if int(res) == 200:
        return render_template('message.html',message = 'Sucessfully growing the worker pool by 1')
    else:
        return render_template('message.html',message = 'Failed: Growing the worker pool by 1')


@webapp.route('/shrink-worker-pool', methods = ['POST'])
def shrink_pool():
    print("shrink")
    res = client.shrink_worker_by_one()
    if res[0]:
        return render_template('message.html',message = 'Sucessfully shrinking the worker pool by 1')
    else:
        return render_template('message.html',message = 'Failed: Shrinking the worker pool by 1')



@webapp.route('/stop')
def stop_manager():
    print("stop")
    res = client.stop_all_instances()
    #stop all instance should rewirte
    if res[0]:
        return render_template('message.html',message = 'Sucessfully stopping all instance')
    else:
        return render_template('message.html',message = 'Failed: stopping all instance')


@webapp.route('/delete')
def delete_data():
    print("delete")

    client.clear_s3()
    return render_template('message.html',message = 'Sucessfully Deleting all application data')


@webapp.route('/configure', methods = ['POST'])
def configure():
    global default_CPU_grow
    global default_CPU_shrink
    global default_ratio_grow
    global default_ratio_shrink

    default_CPU_grow = request.form.get('CPU_grow', "")
    default_CPU_shrink = request.form.get('CPU_shrink', "")
    default_ratio_grow = request.form.get('ratio_expend', "")
    default_ratio_shrink= request.form.get('ratio_shrink', "")
    if default_CPU_grow == "":
        default_CPU_grow = 40
    else:
        default_CPU_grow = float(default_CPU_grow)

    if default_CPU_shrink == "":
        default_CPU_shrink = 20
    else:
        default_CPU_shrink = float(default_CPU_shrink)

    if default_ratio_grow == "":
        default_ratio_grow = 2.0
    else:
        default_ratio_grow = float(default_ratio_grow)

    if default_ratio_shrink == "":
        default_ratio_shrink = 0.5
    else:
        default_ratio_shrink = float(default_ratio_shrink)

    
    data = "Configure: "+ str(default_CPU_grow ) + str(default_CPU_shrink) + str(default_ratio_grow) + str(default_ratio_shrink)

    print('Configure:', data)

    return render_template('message.html',message = 'Sucessfully configure the auto policy with data: '+ data)



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

def fetch_reqeusts_rate(instance_id, start_time, end_time):
    cnx = get_db()
    cursor = cnx.cursor()
    query = "SELECT timestamp FROM http_req WHERE instanceID=%s"
    cursor.execute(query, (instance_id,))

    row = [item[0] for item in cursor.fetchall()]

    localtime = timezone(ZONE)
    timestamps = list(map(lambda x: int(round(datetime.timestamp\
                (localtime.localize(x,is_dst=None).astimezone(utc)))), row))

    requests_record = []
    timestamp_counter = collections.Counter(timestamps)

    start_timestamp = int(round(datetime.timestamp(start_time)))
    end_timestamp = int(round(datetime.timestamp(end_time)))

    for i in range(start_timestamp, end_timestamp, 60):
        count = 0
        for j in range(i, i + 60):
            count += timestamp_counter[j]

        requests_record.append([i*1000, count])

    return requests_record



'''

# def ThreadingExample():
#     thread = threading.Thread(target= werun, args=())
#     thread.daemon = True                            # Daemonize thread
#     thread.start()                                  # Start the execution
    

def werun():
    global default_CPU_grow
    global default_CPU_shrink
    global default_ratio_grow
    global default_ratio_shrink
    """ Method that runs forever """
    while True:
        # Do something
        print(datetime.now().__str__() + ' : Start task in the background')
        print("Param: ",default_CPU_grow,default_CPU_shrink,default_ratio_grow,default_ratio_shrink)

        time.sleep(2)

'''


# get start_time and end_time of latest 2 minute
def get_time_span(latest):
    end_time = datetime.now(timezone(ZONE))
    start_time = end_time - timedelta(seconds=latest)
    return start_time, end_time

def average_cpu_utils_2min():
    global client
    valid_instances_id = client.get_workers()
    num_worker = len(valid_instances_id)

    start_time, end_time = get_time_span(120)
    cpu_sum = 0
    for i in range(num_worker):
        response = client.get_cpu(valid_instances_id[i]['Id'], start_time, end_time)
        #logging.warning(response)
        #response = json.loads(response)
        if response and response[0]:
            cpu_sum += response[0][1]
    
    if num_worker > 0:
        return float(cpu_sum / num_worker)
    else:
        return -1


def auto_scaling():

    global default_CPU_grow
    global default_CPU_shrink
    global default_ratio_grow
    global default_ratio_shrink
    global client

    current_time = datetime.now(timezone(ZONE))
    cpu_utils = average_cpu_utils_2min()
    if(cpu_utils == -1):
        return False
    
    if cpu_utils > default_CPU_grow:
        response = client.grow_worker_by_ratio(default_ratio_grow)
    elif cpu_utils < default_CPU_shrink:
        response = client.shrink_worker_by_ratio(default_ratio_shrink)
    time.sleep(60)

    return True
