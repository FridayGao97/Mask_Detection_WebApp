import boto3
import time
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class awsClient:
    def __init__(self):
        self.ec2 = boto3.client('ec2')
        self.elb = boto3.client('elbv2') # 'elbv2' is for application load balancer, 'elb' is for classic load balancer
        self.cloudwatch = boto3.client('cloudwatch')
        self.s3 = boto3.client('s3')
        self.bucket = 'ece1779-a2'
        self.TargetGroupArn = 'arn:aws:elasticloadbalancing:us-east-1:678814637696:targetgroup/ECE1779-Assignment2/ac5be37a415164c2'
        self.user_app_tag = 'User_app'
        self.manager_app_tag = 'Manager_app'
        self.ami_id = 'ami-054b7dff464af8ab6'
        self.instance_type = 't2.small'
        self.keypair_name = 'keypair'
        self.security_group_id = ['sg-0fef18e8c5f05065f']
        self.subnet_id = 'subnet-0afac8ced93d3ac9f'
        self.tag_specification = [{
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': self.user_app_tag
                }
            ]
        }]

        self.monitoring = {
            'Enabled': True
        }
        self.placement = {
            'AvailabilityZone': 'us-east-1a'
        }
        self.IamInstanceProfile = {
            'Arn': 'arn:aws:iam::678814637696:instance-profile/ECE1779-A2'
        }
        #with open(basedir + '/Userdata.txt', 'r') as myfile:
        #    data = myfile.read()
        self.userdata = "#!/bin/bash \npip3 install mysql-connector-python \npip3 install Flask-Mail \ncd home/ubuntu/Desktop/userapp \npython3.8 run.py > out.txt 2> err.txt"
        self.availabilityzone = 'us-east-1a'
        self.targetgroup = 'targetgroup/ECE1779-Assignment2/ac5be37a415164c2'
        self.loadbalancer = 'app/ECE1779-A2-ELB/42868c4091d6bf9d'

    def create_ec2_instance(self):
        # create an EC2 instance from the backup AMI
        response = self.ec2.run_instances(ImageId=self.ami_id,
                                          InstanceType=self.instance_type,
                                          MinCount=1,
                                          MaxCount=1,
                                          KeyName=self.keypair_name,
                                          NetworkInterfaces=[
                                              {
                                                  'DeviceIndex': 0,
                                                  'SubnetId': self.subnet_id,
                                                  'AssociatePublicIpAddress': True,
                                                  'Groups': self.security_group_id
                                              },
                                          ],
                                          #SecurityGroupIds=self.security_group_id,
                                          #SubnetId=self.subnet_id,
                                          Monitoring=self.monitoring,
                                          IamInstanceProfile=self.IamInstanceProfile,
                                          TagSpecifications=self.tag_specification,
                                          Placement=self.placement,
                                          UserData=self.userdata)
        print(self.userdata)
        return response

    # get the instance that runs the manager app
    def get_manager(self):
        response = self.ec2.describe_instances(Filters=[
            {
                'Name': 'tag:Name',
                'Values': [self.manager_app_tag]
            }
        ])
        instance_id = response['Reservations'][0]['Instances'][0]['InstanceId']
        return instance_id

    # get all instances (workers) in the target group (worker pool) of ELB
    def get_workers(self):
        response = self.elb.describe_target_health(
            TargetGroupArn=self.TargetGroupArn,
        )
        worker_pool = []
        if response['TargetHealthDescriptions']:
            for worker in response['TargetHealthDescriptions']:
                worker_pool.append({
                    'Id': worker['Target']['Id'],
                    'Port': worker['Target']['Port'],
                    'State': worker['TargetHealth']['State']
                })
        return worker_pool

    # get the usable (not draining) workers in the worker pool
    def get_usable_workers(self):
        workers = self.get_workers()
        usable_workers_id = []
        for worker in workers:
            if worker['State'] != 'draining':
                usable_workers_id.append(worker['Id'])
        return usable_workers_id

    # count the number of workers for the past 30 minutes
    def count_workers(self, start_time, end_time):
        response1 = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/ApplicationELB',
            MetricName='HealthyHostCount',
            Dimensions=[
                {
                    'Name': 'TargetGroup',
                    'Value': self.targetgroup,
                },
                {
                    'Name': 'LoadBalancer',
                    'Value': self.loadbalancer,
                },
                {
                    'Name': 'AvailabilityZone',
                    'Value': self.availabilityzone,
                },
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=60,
            Statistics=['Maximum'],
            Unit='Count'
        )
        response2 = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/ApplicationELB',
            MetricName='UnHealthyHostCount',
            Dimensions=[
                {
                    'Name': 'TargetGroup',
                    'Value': self.targetgroup,
                },
                {
                    'Name': 'LoadBalancer',
                    'Value': self.loadbalancer,
                },
                {
                    'Name': 'AvailabilityZone',
                    'Value': self.availabilityzone,
                },
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=60,
            Statistics=['Maximum'],
            Unit='Count'
        )
        datapoints = []
        if response1['Datapoints']:
            for datapoint in response1['Datapoints']:
                datapoints.append(
                    [
                        datapoint['Timestamp'].timestamp()*1000,
                        datapoint['Maximum']
                    ]
                )
        if response2['Datapoints']:
            for i in range(len(datapoints)):
                datapoints[i][1] += response2['Datapoints'][i]['Maximum']
        return datapoints

    # get CPU utilization for the past 30 minutes
    def get_cpu(self, instance_id, start_time, end_time):
        response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[
                {
                    'Name': 'InstanceId',
                    'Value': instance_id,
                },
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=60,
            Statistics=['Maximum'],
            Unit='Percent'
        )
        datapoints = []
        if response['Datapoints']:
            for datapoint in response['Datapoints']:
                datapoints.append(
                    [
                        datapoint['Timestamp'].timestamp()*1000,
                        datapoint['Maximum']
                    ]
                )
        return datapoints

    # get http request for the past 30 minutes
    '''
    def get_http(self, instance_id, start_time, end_time):

        response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='HTTPRequest',
            Dimensions=[
                {
                    'Name': 'InstanceId',
                    'Value': instance_id,
                },
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=60,
            Statistics=['Maximum'],
            Unit='Count'
        )
        datapoints = []
        if response['Datapoints']:
            for datapoint in response['Datapoints']:
                datapoints.append(
                    [
                        datapoint['Timestamp'].timestamp()*1000,
                        datapoint['Maximum']
                    ]
                )
        return datapoints
    '''


    def grow_worker_by_one(self):
        # create connection to ec2
        # ec2 = boto3.resource('ec2')

        # get all instance
        allinstances = self.get_workers()

        # make sure not exceed the maximum number of workers
        if len(allinstances) <= 7:
            response = self.create_ec2_instance()
            time.sleep(10)
            new_instance_id = response['Instances'][0]['InstanceId']
        else:
            return 'Maximum number of Workers reached'

        # check to see if the status of new instance changes to running
        specfic_state = self.ec2.describe_instance_status(InstanceIds=[new_instance_id])
        while len(specfic_state['InstanceStatuses']) < 1:
            time.sleep(10)
            specfic_state = self.ec2.describe_instance_status(InstanceIds=[new_instance_id])
        while specfic_state['InstanceStatuses'][0]['InstanceState']['Name'] != 'running':
            time.sleep(10)
            specfic_state = self.ec2.describe_instance_status(InstanceIds=[new_instance_id])
            print(specfic_state)

        '''
        # publish a custom metric in cloud watch to measure the HTTP request rate for each worker
        self.cloudwatch.put_metric_data(
            Namespace='AWS/EC2',
            MetricData=[
                {
                    'MetricName': 'HTTPRequest',
                    'Dimensions': [
                        {
                            'Name': 'InstanceId',
                            'Value': new_instance_id
                        },
                    ],
                    'Value': 0,
                    'Unit': 'Count',
                },
            ]
        )
        '''

        # register new instance after it finishes initialization
        time.sleep(10)
        response = self.elb.register_targets(
            TargetGroupArn=self.TargetGroupArn,
            Targets=[
                {
                    'Id': new_instance_id,
                    'Port': 5000
                }, ])
        if response and 'ResponseMetadata' in response and \
                'HTTPStatusCode' in response['ResponseMetadata']:
            return response['ResponseMetadata']['HTTPStatusCode']
        # return whether successful or not
        # return "200"
        else:
            return -1

    def grow_worker_by_ratio(self, ratio):
        # create connection to ec2
        if ratio < 1:
            return 'The growing ratio must be exceed 1'

        # get all instance
        allinstances = self.get_workers()

        increase = round(len(allinstances) * ratio)
        if increase > 8:
            delta = 8 - len(allinstances)
        else:
            delta = increase - len(allinstances)

        # grow worker by iteratively applying grow grow_worker_by_one()
        # upper limit of 10 is enforced within grow_worker_by_one()
        count = 0
        for i in range(delta):
            res = self.grow_worker_by_one()
            # if res == 200:
            if int(res) == 200:
                count = count + 1
            # responses.append(self.grow_worker_by_one())

        # return how many worker added
        return count

    def shrink_worker_by_one(self, stop=True):
        if (stop):
            min_number = 1
        else:
            min_number = 0

        target_instances_id = self.get_workers()
        flag, msg = True, ''

        if len(target_instances_id) > min_number:

            unregister_instance_id = target_instances_id[-1]['Id']
            # unregister instance from target group
            deregister_instance_response = self.elb.deregister_targets(
                TargetGroupArn=self.TargetGroupArn,
                Targets=[
                    {
                        'Id': unregister_instance_id
                    }, ])
            deregister_instance_status = -1

            # check successful
            if deregister_instance_response and 'ResponseMetadata' in deregister_instance_response and \
                    'HTTPStatusCode' in deregister_instance_response['ResponseMetadata']:
                deregister_instance_status = deregister_instance_response['ResponseMetadata']['HTTPStatusCode']

            if int(deregister_instance_status) == 200:

                # after successful deregister, try to terminate instance
                terminate_instance_status = -1
                terminate_instance_response = self.ec2.terminate_instances(InstanceIds=[unregister_instance_id])

                # check whether successful
                if terminate_instance_response and 'ResponseMetadata' in terminate_instance_response and \
                        'HTTPStatusCode' in terminate_instance_response['ResponseMetadata']:
                    terminate_instance_status = terminate_instance_response['ResponseMetadata']['HTTPStatusCode']

                    if int(terminate_instance_status) != 200:
                        flag = False
                        msg = "Unable to terminate the instance"
            else:
                flag = False
                msg = "Unable to unregister from target group"
        else:
            flag = False
            msg = "No workers to unregister"
        if flag == True:
            msg = "Worker was successfully unregistered"
        return [flag, msg]

    # shrink worker by ratio
    # ratio is the percentage of instances to be suspended
    def shrink_worker_by_ratio(self, ratio):

        # create connection to ec2
        if ratio > 1:
            return 'The shrink ratio must be less than 1'

        # get all instance
        allinstances = self.get_workers()

        shrink = round(len(allinstances) * ratio)

        if shrink < 1:
            delta = len(allinstances) - 1
        else:
            delta = len(allinstances) - shrink

        # grow worker by iteratively applying grow grow_worker_by_one()
        # upper limit of 10 is enforced within grow_worker_by_one()
        count = 0
        for i in range(delta):
            res = self.shrink_worker_by_one()
            if res[0] == True:
                count = count + 1
            # responses.append(self.grow_worker_by_one())

        # return how many worker added
        return count

    def stop_manager(self):
        flag, msg = True, ''
        # initialize
        stop_manager_instance_status = -1

        manager_instance_id = self.get_manager()

        if len(manager_instance_id) == 1:

            stop_manager_instance_response = self.ec2.stop_instances(
                InstanceIds=[manager_instance_id, ],
                Hibernate=False,
                Force=False
            )

            # check
            if stop_manager_instance_response and 'ResponseMetadata' in stop_manager_instance_response and \
                    'HTTPStatusCode' in stop_manager_instance_response['ResponseMetadata']:
                stop_manager_instance_status = stop_manager_instance_response['ResponseMetadata']['HTTPStatusCode']
            if int(stop_manager_instance_status) != 200:
                flag = False
                msg = "Unable to stop the manager app instance"
        else:
            flag = False
            msg = "No manager instance available"
        return [flag, msg]

    # terminate all workers and stop manager
    def stop_all_instances(self):

        # get all instances
        target_instances_id = self.get_workers()
        # initialize
        response_list = []

        if len(target_instances_id) < 1:
            response_list.append(self.stop_manager())
            return [True, "Success", response_list]
        else:
            shrink_targets_num = len(target_instances_id)
            for i in range(shrink_targets_num):
                # try to terminate instance when tag for shrink_worker_by_one() is false
                temp = self.shrink_worker_by_one(False)
                response_list.append(temp)
            # response_list would store all return message
            temp1 = self.stop_manager()
            response_list.append(temp1)

        return [True, "Success", response_list]

    def clear_s3(self):
        for key in self.s3.list_objects(Bucket=self.bucket)['Contents']:
            self.s3.delete_objects(
                Bucket=self.bucket,
                Delete={
                    'Objects': [
                        {
                            'Key': key['Key'],
                        }, ],
                    'Quiet': True
                },
            )