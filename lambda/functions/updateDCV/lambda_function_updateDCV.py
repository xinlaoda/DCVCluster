import boto3
import botocore
import json
import logging
import os

print('Loading function')
cfn = boto3.client('cloudformation')
dynamodb = boto3.resource('dynamodb')
ec2 = boto3.client('ec2')

def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def lambda_handler(event, context):
    ### get parameters from environment.
    env_DCVDynamoDBTable = os.environ['DCVDynamoDBTable']
    env_ALB_DNS_Name = os.environ['ALB_DNS_Name']

    print("Received event: " + json.dumps(event, indent=2))

    table = dynamodb.Table(env_DCVDynamoDBTable)
    
    ### scan db
    dcv_items = table.scan()
    for item in dcv_items["Items"]:
        print(json.dumps(item))
        stackName = item["CFStackName"]
        stackState = item["CFState"]
        dcv_user = item["User"]
        dcv_id = item["Id"]
        
        print("db query reponse stack Name: State " + stackName + " : " + stackState)
        
        # get stack state if it is not complete
        _newState=""
        if stackState not in ["UPDATE_COMPLETE", "CREATE_COMPLETE"]:
            ### update cloudformation state
            print("update cloudformation state ...")
            try:
                response = cfn.describe_stacks(
                    StackName=stackName
                )
            except botocore.exceptions.ClientError as error:
                if stackState == "DELETE_IN_PROGRESS":
                    _newState = "DELETE_COMPLETE"
            else:
                _newState = response["Stacks"][0]["StackStatus"]
            print("new state: " + _newState)
            if '' == _newState:
                reponse = table.delete_item(
                    Key={
                        'User': dcv_user,
                        'Id': dcv_id
                    }
                )
            else:
                ### update CF state 
                response = table.update_item(
                    Key={
                        'User': dcv_user,
                        'Id': dcv_id
                    },
                    UpdateExpression='SET CFState = :val1, DCVState = :val2, EC2State = :val3, ALBUrl = :val3',
                    ExpressionAttributeValues={
                        ':val1': _newState,
                        ':val2': _newState,
                        ':val3': ''
                    }
                )
        else:
            ### update instance state
            print("Update instance state ...")
            ### get ec2 instance
            if "EC2instanceId" in item.keys():
                ec2_instanceId = item["EC2instanceId"]
            else:
                ### get ec2 id from cloudformation
                response = cfn.describe_stack_resource(
                    StackName=stackName,
                    LogicalResourceId='myEC2InstanceDCV'
                )
                ec2_instanceId = response['StackResourceDetail']['PhysicalResourceId']
            print("instance ID: " + ec2_instanceId)
            ###query ec2 instance state
            response = ec2.describe_instances(
                InstanceIds=[
                ec2_instanceId
            ])
            EC2State = response['Reservations'][0]['Instances'][0]['State']['Name']
            ec2StateCode = response['Reservations'][0]['Instances'][0]['State']['Code']
            print("state : " + EC2State)
            EC2PrivateDNSName = response['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['PrivateDnsName'].split(".")[0]
            print("dns name: " + EC2PrivateDNSName)
            ### update ALB access url when state is running
            ALB_Url = ''
            if 16 == ec2StateCode:
                ALB_Url = 'https://' + env_ALB_DNS_Name + ':8443/' + EC2PrivateDNSName + "/#default"
            DCVState = EC2State
            response = table.update_item(
                Key={
                    'User': dcv_user,
                    'Id': dcv_id
                },
                UpdateExpression='SET EC2State = :val1, DCVState = :val2, EC2instanceId = :val3, ALBUrl = :val4',
                ExpressionAttributeValues={
                    ':val1': EC2State,
                    ':val2': DCVState,
                    ':val3': ec2_instanceId,
                    ':val4': ALB_Url
                }
            )
    return respond(None, dcv_items);

