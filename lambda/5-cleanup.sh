#!/bin/bash
set -eo pipefail
STACK=$(aws cloudformation list-exports --query 'Exports[?Name==`DCVClusterStackName`].Value')-lambda
if [[ $# -eq 1 ]] ; then
    STACK=$1
    echo "Deleting stack $STACK"
fi
FUNCTION_createDCV=$(aws cloudformation describe-stack-resource --stack-name $STACK --logical-resource-id createDCVfunction --query 'StackResourceDetail.PhysicalResourceId' --output text)
FUNCTION_updateDCV=$(aws cloudformation describe-stack-resource --stack-name $STACK --logical-resource-id updateDCVfunction --query 'StackResourceDetail.PhysicalResourceId' --output text)
FUNCTION_modifyDCV=$(aws cloudformation describe-stack-resource --stack-name $STACK --logical-resource-id modifyDCVfunction --query 'StackResourceDetail.PhysicalResourceId' --output text)
FUNCTION_removeDCV=$(aws cloudformation describe-stack-resource --stack-name $STACK --logical-resource-id removeDCVfunction --query 'StackResourceDetail.PhysicalResourceId' --output text)
FUNCTION_openDCV=$(aws cloudformation describe-stack-resource --stack-name $STACK --logical-resource-id openDCVfunction --query 'StackResourceDetail.PhysicalResourceId' --output text)
FUNCTION_listDCV=$(aws cloudformation describe-stack-resource --stack-name $STACK --logical-resource-id listDCVfunction --query 'StackResourceDetail.PhysicalResourceId' --output text)

aws cloudformation delete-stack --stack-name $STACK
echo "Deleted $STACK stack."

if [ -f bucket-name.txt ]; then
    ARTIFACT_BUCKET=$(cat bucket-name.txt)
    while true; do
        read -p "Delete deployment artifacts and bucket ($ARTIFACT_BUCKET)?" response
        case $response in
            [Yy]* ) aws s3 rb --force s3://$ARTIFACT_BUCKET; rm bucket-name.txt; break;;
            [Nn]* ) break;;
            * ) echo "Response must start with y or n.";;
        esac
    done
fi

### delete log group
exec aws logs delete-log-group --log-group-name /aws/lambda/$FUNCTION_createDCV
exec aws logs delete-log-group --log-group-name /aws/lambda/$FUNCTION_updateDCV
exec aws logs delete-log-group --log-group-name /aws/lambda/$FUNCTION_modifyDCV
exec aws logs delete-log-group --log-group-name /aws/lambda/$FUNCTION_removeDCV
exec aws logs delete-log-group --log-group-name /aws/lambda/$FUNCTION_listDCV
exec aws logs delete-log-group --log-group-name /aws/lambda/$FUNCTION_openDCV

rm -f out.yml out.json function/*.pyc
rm -rf package function/__pycache__
