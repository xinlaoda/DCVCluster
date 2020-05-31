import boto3
import json
import logging
import os
from boto3.dynamodb.conditions import Key, Attr

print('Loading function')

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

    _body = event["queryStringParameters"]
    print(type(_body))
    if isinstance(_body,str):
        body = json.loads(_body)
    else:
        body = _body
    print("post body: " + json.dumps(body))
    table = dynamodb.Table(env_DCVDynamoDBTable)
    
    if body is None:
        response = table.scan(
        )
    else:
        ''' query stack id from db
        '''
        if "user" in body.keys():
            dcv_user = body["user"]
            response = table.query(
                KeyConditionExpression=Key('User').eq(dcv_user)
            )
        else:
            response = table.scan(
            )

    items = response['Items']
    reponse_body = {
        'Items': items
    }
    print("reponse event: " + json.dumps(reponse_body, indent=2))
    return respond(None, reponse_body);

