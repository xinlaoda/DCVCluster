# DCVCluster
DCV Cluster on AWS

INSTALL：
1. Create basic services, include VPC, API Gateway, ELB via dcv_cluster_vpc.yaml in Cloudformation；
2. Run createALB_HTTPS_Listeners.sh to create SSL certification and ALB liteners
3. Under lambda directory, run 1-create-bucket.sh, 2-build-layer.sh, 3-deploy.sh to create lambda function and register it as REST Api in Api Gateway

Usage:
1. create DCV, for example
curl -X POST -H "content-type: application/json" -d '{"user": "user1", "bundle":"ALinux2", "instanceSize": "c4.2xlarge"}' https://{api-gw-id}.execute-api.cn-northwest-1.amazonaws.com.cn/v1/dcv

2. list DCV sessions, for example
curl https://lha8f5a0ed.execute-api.cn-northwest-1.amazonaws.com.cn/v1/dcv

3. remove DCV session, for example
 curl -X DELETE -H "content-type: application/json" -d '{"user": "user1", "id":"{id}" }' https://{api-gw-id}.execute-api.cn-northwest-1.amazonaws.com.cn/v1/dcv

Endpoint request URI: https://lambda.cn-northwest-1.amazonaws.com.cn/2015-03-31/functions/arn:aws-cn:lambda:cn-northwest-1:079671731889:function:CreateDCV/invocations
