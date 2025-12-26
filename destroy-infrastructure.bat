@echo off
echo Destroying SQL Chatbot Infrastructure...

echo.
echo WARNING: This will destroy all infrastructure including databases!
set /p confirm="Are you sure you want to continue? (y/N): "
if /i not "%confirm%"=="y" (
    echo Cancelled.
    exit /b 0
)

echo.
echo 1. Destroying Pipeline Stack...
cdk destroy SqlChatbotPipelineStack --force

echo.
echo 2. Destroying EKS Stack...
cdk destroy EksStack --force

echo.
echo 3. Destroying RDS Stack...
cdk destroy RdsStack --force

echo.
echo 4. Destroying VPC Stack...
cdk destroy VpcStack --force

echo.
echo Infrastructure cleanup completed!