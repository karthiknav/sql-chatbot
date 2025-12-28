#!/usr/bin/env python3
import aws_cdk as cdk
from iam_stack import IamStack
from vpc_stack import VpcStack
from rds_stack import RdsStack
from eks_stack import EksStack
from cdk_pipeline_stack import SqlChatbotPipelineStack

app = cdk.App()

# Create IAM stack first (contains roles and policies)
iam_stack = IamStack(app, "IamStack")

# Create VPC stack second
vpc_stack = VpcStack(app, "VpcStack")
vpc_stack.add_dependency(iam_stack)

# Create RDS stack that depends on VPC - pass VPC object
rds_stack = RdsStack(app, "RdsStack", vpc=vpc_stack.vpc)
rds_stack.add_dependency(vpc_stack)

# Create EKS stack that depends on VPC and IAM - pass VPC object
eks_stack = EksStack(app, "EksStack", vpc=vpc_stack.vpc)
eks_stack.add_dependency(vpc_stack)
eks_stack.add_dependency(iam_stack)

# Update pipeline stack to depend on IAM, EKS and RDS stacks
pipeline_stack = SqlChatbotPipelineStack(app, "SqlChatbotPipelineStack")
pipeline_stack.add_dependency(iam_stack)
pipeline_stack.add_dependency(eks_stack)
pipeline_stack.add_dependency(rds_stack)

app.synth()