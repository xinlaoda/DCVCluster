import boto3
import json
import logging
import os
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

print('Loading function')
cfn = boto3.client('cloudformation')
dynamodb = boto3.resource('dynamodb')
ec2 = boto3.client('ec2')

### get parameters from environment.
env_DCVDynamoDBTable = os.environ['DCVDynamoDBTable']

def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))
    
    query_id = event["pathParameters"]["proxy"]
    print("Received id: " + query_id)
    
    ### query id
    table = dynamodb.Table(env_DCVDynamoDBTable)
    _response = table.scan(
        FilterExpression=Attr('Id').eq(query_id)
    )
    response = _response["Items"]
    queryStringParameters = event["queryStringParameters"]
    if queryStringParameters is not None:
        if "action" in queryStringParameters.keys():
            action = event["queryStringParameters"]["action"]
            print("Received action: " + action)
            
            ## get ec2 instance id
            ec2_id = response[0]["EC2instanceId"]
            print(ec2_id)
            
            ### execute action 
            if action == 'start':
                # Do a dryrun first to verify permissions
                try:
                    ec2.start_instances(InstanceIds=[ec2_id], DryRun=True)
                except ClientError as e:
                    if 'DryRunOperation' not in str(e):
                        raise
            
                # Dry run succeeded, run start_instances without dryrun
                try:
                    response = ec2.start_instances(InstanceIds=[ec2_id], DryRun=False)
                    print(response)
                except ClientError as e:
                    print(e)
            if action == 'stop':
                # Do a dryrun first to verify permissions
                try:
                    ec2.stop_instances(InstanceIds=[ec2_id], DryRun=True)
                except ClientError as e:
                    if 'DryRunOperation' not in str(e):
                        raise
            
                # Dry run succeeded, call stop_instances without dryrun
                try:
                    _response = ec2.stop_instances(InstanceIds=[ec2_id], DryRun=False)
                    print(_response)
                    response = _response["StoppingInstances"]
                except ClientError as e:
                    print(e)
        
    

    
    
    return respond(None, response)

