#!/bin/sh

Stack_Name=$(aws cloudformation list-exports --query 'Exports[?Name==`DCVClusterStackName`].Value')
echo "Stack_Name=$Stack_Name"

ALB_DNS_NAME=$(aws cloudformation describe-stacks --stack-name $Stack_Name --query 'Stacks[0].Outputs[?OutputKey==`ALBDNSName`].OutputValue' --output text)
ALB_ARN=$(aws cloudformation describe-stacks --stack-name $Stack_Name --query 'Stacks[0].Outputs[?OutputKey==`ALB`].OutputValue' --output text)
ALB_Target_Group=$(aws cloudformation describe-stacks --stack-name $Stack_Name --query 'Stacks[0].Outputs[?OutputKey==`DefaultTargetGroup`].OutputValue' --output text)

echo "ALB DNS Name: $ALB_DNS_NAME"

cat openssl.cnf | sed "s/__ALB_DNS_NAME__/$ALB_DNS_NAME/g" > openssl_alb.cnf

openssl req -new -x509 -nodes -sha256 -newkey rsa:2048 -days 3650 -keyout ./ALBkey.pem -out ./ALBcrt.pem -config ./openssl_alb.cnf

acm_cert_arn=$(aws acm import-certificate --certificate file://ALBcrt.pem --private-key file://ALBkey.pem)

echo "$acm_cert_arn" > ALB_CERT_ARN.txt

aws acm  add-tags-to-certificate --certificate-arn $acm_cert_arn --tags Key=Name,Value=$Stack_Name

ALB_LISTENER_ARN=$(aws elbv2 create-listener --load-balancer-arn $ALB_ARN --protocol HTTPS --port 8443 --certificates CertificateArn=$acm_cert_arn --default-actions Type=forward,TargetGroupArn=$ALB_Target_Group --query 'Listeners[0].ListenerArn')
echo "ALB_LISTENER_ARN = $ALB_LISTENER_ARN"
echo "$ALB_LISTENER_ARN" > ALB_LISTENER_ARN.txt
