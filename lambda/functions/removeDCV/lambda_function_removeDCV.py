import boto3
import json
import logging
import os

print('Loading function')
cfn = boto3.client('cloudformation')
dynamodb = boto3.resource('dynamodb')

def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def lambda_handler(event, context):
    '''Invoke cloudformation template to delete DCV instance, target group
    and ALB rule.
    '''
    print("Received event: " + json.dumps(event, indent=2))
     ### get parameters from environment.
    env_DCVDynamoDBTable = os.environ['DCVDynamoDBTable']

    _body = event["body"]
    print(type(_body))
    if isinstance(_body,str):
        body = json.loads(_body)
    else:
        body = _body
    print("post body: " + json.dumps(body))

    if "user" in body.keys():
        dcv_user = body["user"]
    else:
        err = "Can not get user from request body."
        return respond(err)
    if "id" in body.keys():
        dcv_id = body["id"]
    else:
        return respond("Can not get id from request body.")
    
    ''' query stack id from db
    '''
    table = dynamodb.Table(env_DCVDynamoDBTable)
    dcv_item = table.get_item(
       Key={
            'User': dcv_user,
            'Id': dcv_id
        }
    )
    if "Item" in dcv_item.keys():
        stackName = dcv_item["Item"]["CFStackName"]
        print("db query reponse stack Name: " + stackName)
        
        # delete template
        response = cfn.delete_stack(
            StackName=stackName
        )
        
        # udpate db
        response = table.update_item(
           Key={
                'User': dcv_user,
                'Id': dcv_id
            },
            UpdateExpression='SET CFState = :val1, DCVState = :val2',
            ExpressionAttributeValues={
                ':val1': "DELETE_IN_PROGRESS",
                ':val2': "DELETE_IN_PROGRESS"
            }
        )    
        reponse_body = {
            'User': dcv_user,
            'Id': dcv_id,
            'DCVState': 'DELETE_IN_PROGRESS'
        }
    else:
        err = {
            'errMsg': 'Can not find DCV instance.'
        }
        return respond(err, None)
        
    print("reponse event: " + json.dumps(reponse_body, indent=2))
    return respond(None, reponse_body);

