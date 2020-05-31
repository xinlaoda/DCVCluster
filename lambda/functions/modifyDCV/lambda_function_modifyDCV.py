import boto3
import json
import logging
from uuid import uuid4

uuidChars = ("a", "b", "c", "d", "e", "f",
             "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s",
             "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5",
             "6", "7", "8", "9", "A", "B", "C", "D", "E", "F", "G", "H", "I",
             "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V",
             "W", "X", "Y", "Z")

print('Loading function')
cfn = boto3.client('cloudformation')
dynamodb = boto3.resource('dynamodb')

with open('create_dcv.yaml', 'r') as f:
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
        
    print("Received event: " + json.dumps(event, indent=2))
    if "POST" == event['httpMethod']:
        print("Post method, create DCV session.")
        body = event["body"]
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
        stackName = 'dcv-cluster-' + dcv_id
        response = cfn.create_stack(
            StackName=stackName,
            #TemplateURL='https://dcvcluster.s3.cn-northwest-1.amazonaws.com.cn/cf-template/create_dcv_host.json',
            TemplateBody=cf_temp,
            Parameters=[
                {
                    'ParameterKey': 'AMI',
                    'ParameterValue': 'ami-09747c609e002b861'
                },
                {
                    'ParameterKey': 'DCVELBListener',
                    'ParameterValue': 'arn:aws-cn:elasticloadbalancing:cn-northwest-1:079671731889:listener/app/dcv-elb/fe4b6334ff912b4e/80e20e242d3d4b73'
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
                    'ParameterValue': 'xinxx-key-nx'
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
                    'ParameterValue': 'subnet-0d2184351e31500df'
                },
                {
                    'ParameterKey': 'VPC',
                    'ParameterValue': 'vpc-00073949a1ea2695e'
                },
                {
                    'ParameterKey': 'SecurityGroupId',
                    'ParameterValue': 'sg-00349e21f93852083'
                }
            ],
        )
    stackId = response["StackId"]
    logging.info("Stack ID = " + stackId)
    print("reponse event: " + json.dumps(response, indent=2))
    
    ''' add this item into dynamodb
    '''
    table = dynamodb.Table('dcvcluster')
    response = table.put_item(
       Item={
            'user': dcv_user,
            'id': dcv_id,
            'attrs': {
                'stackname':stackName,
                'state': 'CREATE_IN_PROGRESS'
            }
        }
    )
    
    print("reponse event: " + json.dumps(response, indent=2))
    
    return respond(None, response);

