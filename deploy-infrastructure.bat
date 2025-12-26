@echo off
echo Deploying SQL Chatbot Infrastructure...

echo.
echo 1. Deploying VPC Stack...
cdk deploy VpcStack --require-approval never

if %ERRORLEVEL% neq 0 (
    echo VPC deployment failed!
    exit /b 1
)

echo.
echo 2. Deploying RDS Stack...
cdk deploy RdsStack --require-approval never

if %ERRORLEVEL% neq 0 (
    echo RDS deployment failed!
    exit /b 1
)

echo.
echo 3. Deploying EKS Stack (includes AWS Load Balancer Controller)...
cdk deploy EksStack --require-approval never

if %ERRORLEVEL% neq 0 (
    echo EKS deployment failed!
    exit /b 1
)

echo.
echo 4. Deploying Pipeline Stack...
cdk deploy SqlChatbotPipelineStack --require-approval never

if %ERRORLEVEL% neq 0 (
    echo Pipeline deployment failed!
    exit /b 1
)

echo.
echo All infrastructure stacks deployed successfully!
echo.
echo Next steps:
echo   1. Configure kubectl: aws eks update-kubeconfig --region us-east-1 --name eks-cdk-sqlchatbot
echo   2. Deploy application: kubectl apply -f deploy-k8s.yml
echo   3. Get ALB URL: kubectl get ingress sql-chatbot-ingress