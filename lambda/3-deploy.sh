#!/bin/bash
set -eo pipefail

### get parameter from cloudformation
Stack_Name=$(aws cloudformation list-exports --query 'Exports[?Name==`DCVClusterStackName`].Value')
ARTIFACT_BUCKET=$(cat bucket-name.txt)
ALB_DNS_NAME=$(aws cloudformation describe-stacks --stack-name $Stack_Name --query 'Stacks[0].Outputs[?OutputKey==`ALBDNSName`].OutputValue' --output text)
ALB_ARN=$(aws cloudformation describe-stacks --stack-name $Stack_Name --query 'Stacks[0].Outputs[?OutputKey==`ALB`].OutputValue' --output text)
ALB_Target_Group=$(aws cloudformation describe-stacks --stack-name $Stack_Name --query 'Stacks[0].Outputs[?OutputKey==`DefaultTargetGroup`].OutputValue' --output text)
DCVKeyPair=$(aws cloudformation describe-stacks --stack-name $Stack_Name --query 'Stacks[0].Outputs[?OutputKey==`DCVKeyPair`].OutputValue' --output text)
Public0SubnetId=$(aws cloudformation describe-stacks --stack-name $Stack_Name --query 'Stacks[0].Outputs[?OutputKey==`Public0SubnetId`].OutputValue' --output text)
DCVEC2SG=$(aws cloudformation describe-stacks --stack-name $Stack_Name --query 'Stacks[0].Outputs[?OutputKey==`DCVEC2SG`].OutputValue' --output text)
VPCId=$(aws cloudformation describe-stacks --stack-name $Stack_Name --query 'Stacks[0].Outputs[?OutputKey==`VPCId`].OutputValue' --output text)
DCVDynamoDBTable=$(aws cloudformation describe-stacks --stack-name $Stack_Name --query 'Stacks[0].Outputs[?OutputKey==`DCVDynamoDBTable`].OutputValue' --output text)
DCVELBListener=$(cat ../ALB_LISTENER_ARN.txt)

DCVApiGW=$(aws cloudformation describe-stacks --stack-name $Stack_Name --query 'Stacks[0].Outputs[?OutputKey==`DCVApiGW`].OutputValue' --output text)
DCVApiGWResource=$(aws cloudformation describe-stacks --stack-name $Stack_Name --query 'Stacks[0].Outputs[?OutputKey==`DCVApiGWResource`].OutputValue' --output text)

### replace parameter 
cat template.temp.yml | sed -e "s|__ALB_DNS_NAME__|$ALB_DNS_NAME|g" \
    -e "s|__ALB_ARN__|$ALB_ARN|g" \
    -e "s|__ALB_Target_Group__|$ALB_Target_Group|g" \
    -e "s|__DCVKeyPair__|$DCVKeyPair|g" \
    -e "s|__PublicSubnetId__|$Public0SubnetId|g" \
    -e "s|__DCVEC2SG__|$DCVEC2SG|g" \
    -e "s|__VPCId__|$VPCId|g" \
    -e "s|__DCVELBListener__|$DCVELBListener|g" \
    -e "s|__DCVDynamoDBTable__|$DCVDynamoDBTable|g" \
    -e "s|__DCVApiGW__|$DCVApiGW|g" \
    -e "s|__DCVApiGWResource__|$DCVApiGWResource|g" \
    -e "s|__ALB_DNS_NAME__|$ALB_DNS_NAME|g" \
    -e "s|__Stack_Name__|$Stack_Name|g" \
    > template.yml

aws cloudformation package --template-file template.yml --s3-bucket $ARTIFACT_BUCKET --output-template-file out.yml
aws cloudformation deploy --template-file out.yml --stack-name "$Stack_Name-lambda" --capabilities CAPABILITY_NAMED_IAM
