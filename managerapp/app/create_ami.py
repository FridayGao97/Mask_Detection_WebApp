import boto3
import datetime

# get the date
date = datetime.datetime.utcnow().strftime('%Y%m%d')

instance = boto3.client('ec2', region_name='us-east-1')

# create a backup AMI of the base EC2 instance with userapp pre-uploaded
instance_id = 'i-0730467153074d6de'
name = f"ece1997a2_base_instance_ami_{date}"
image = instance.create_image(InstanceId=instance_id, Name=name)
print(image['ImageId'])