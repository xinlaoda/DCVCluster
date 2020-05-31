import boto3
import json
import logging
import os
from uuid import uuid4

uuidChars = ("a", "b", "c", "d", "e", "f",
             "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s",
             "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5",
             "6", "7", "8", "9", "A", "B", "C", "D", "E", "F", "G", "H", "I",
             "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V",
             "W", "X", "Y", "Z")

print('Loading function...')
cfn = boto3.client('cloudformation')
dynamodb = boto3.resource('dynamodb')

with open('createDCV.yml', 'r') as f:
    cf_temp = f.read()

def short_uuid():
    uuid = str(uuid4()).replace('-', '')
    result = ''
    for i in range(0,8):
        sub = uuid[i * 4: i * 4 + 4]
        x = int(sub,16)
        result += uuidChars[x % 0x3E]
    return result

def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def lambda_handler(event, context):
    '''Invoke cloudformation template to create DCV instance, target group
    and ALB rule.
    '''
    if not cf_temp:
        return respond("Failed to get CloudFormation template file.")

    ### get parameters from environment.
    env_KeyPair = os.environ['KeyPair']
    env_PublicSubnet = os.environ['PublicSubnetId']
    env_VPCId = os.environ['VPCId']
    env_SecurityGroupId = os.environ['DCVSecurityGroupId']
    env_DCVELBListener = os.environ['DCVELBListener']
    env_DCVDynamoDBTable = os.environ['DCVDynamoDBTable']
        
    print("Received event: " + json.dumps(event, indent=2))
    ''' post body format:
        {
            user: <user>
            bundle: <bundle>
            instanceSize: <instanceSize>
        }
    '''
        
    print("Post method, create DCV session.")
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
    if "bundle" in body.keys():
        dcv_bundle = body["bundle"]
    else:
        return respond("Can not get bundle from request body.")
    if "instanceSize" in body.keys():
        dcv_instanceSize = body["instanceSize"]
    else:
        return respond("Can not get instanceSize from request body.")
    dcv_id = short_uuid()
    stackName = 'dcv-node-' + dcv_id
    response = cfn.create_stack(
        StackName=stackName,
        TemplateBody=cf_temp,
        Parameters=[
            {
                'ParameterKey': 'AMI',
                'ParameterValue': 'ami-058c6c4192619f214'
            },
            {
                'ParameterKey': 'DCVELBListener',
                'ParameterValue': env_DCVELBListener
            },
            {
                'ParameterKey': 'DCVUser',
                'ParameterValue': dcv_user
            },
            {
                'ParameterKey': 'InstanceType',
                'ParameterValue': dcv_instanceSize
            },
            {
                'ParameterKey': 'KeyPair',
                'ParameterValue': env_KeyPair
            },
            {
                'ParameterKey': 'NISDomainname',
                'ParameterValue': 'hpc'
            },
            {
                'ParameterKey': 'NISServer',
                'ParameterValue': '10.0.10.49'
            },
            {
                'ParameterKey': 'PublicSubnet',
                'ParameterValue': env_PublicSubnet
            },
            {
                'ParameterKey': 'VPC',
                'ParameterValue': env_VPCId
            },
            {
                'ParameterKey': 'SecurityGroupId',
                'ParameterValue': env_SecurityGroupId
            }
        ],
    )
    stackId = response["StackId"]
    logging.info("Stack ID = " + stackId)
    print("reponse event: " + json.dumps(response, indent=2))
    
    ''' add this item into dynamodb, formation:
        {
            User: // user name
            Id: // uuid session id
            DCVState: // overall state, which will map stack state and instance state
            Bundle: // bundle name
            CFStackName: //CloudFormation stack name
            EC2instanceId: //DCV EC2 instance Id
            CFState: //CF stack state
            EC2State: //DCV EC2 instance state
        }
    '''
    table = dynamodb.Table(env_DCVDynamoDBTable)
    response = table.put_item(
       Item={
            'User': dcv_user,
            'Id': dcv_id,
            'CFStackName': stackName,
            'DCVState': 'Proversioning',
            'CFState': 'CREATE_IN_PROGRESS',
            'Bundle': 'ALinux2',
            'InstanceSize': dcv_instanceSize
            }
    )
    reponse_body = {
        'User': dcv_user,
        'Id': dcv_id,
        'DCVState': 'CREATE_IN_PROGRESS'
    }
    print("reponse event: " + json.dumps(reponse_body, indent=2))
    
    return respond(None, reponse_body)

