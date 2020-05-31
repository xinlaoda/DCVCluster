#!/bin/bash
set -eo pipefail
STACK=$(aws cloudformation list-exports --query 'Exports[?Name==`DCVClusterStackName`].Value')
FUNCTION=$(aws cloudformation describe-stack-resource --stack-name $STACK --logical-resource-id function --query 'StackResourceDetail.PhysicalResourceId' --output text)

while true; do
  aws lambda invoke --function-name $FUNCTION --payload file://event.json out.json
  cat out.json
  echo ""
  sleep 2
done
