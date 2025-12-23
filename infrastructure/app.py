#!/usr/bin/env python3
import aws_cdk as cdk
from vpc_stack import VpcStack
from rds_stack import RdsStack
from eks_stack import EksStack
from cdk_pipeline_stack import SqlChatbotPipelineStack

app = cdk.App()

# Create VPC stack first
vpc_stack = VpcStack(app, "VpcStack")

# Create RDS stack that depends on VPC - pass VPC object
rds_stack = RdsStack(app, "RdsStack", vpc=vpc_stack.vpc)
rds_stack.add_dependency(vpc_stack)

# Create EKS stack that depends on VPC - pass VPC object
eks_stack = EksStack(app, "EksStack", vpc=vpc_stack.vpc)
eks_stack.add_dependency(vpc_stack)

# Keep existing pipeline stack
SqlChatbotPipelineStack(app, "SqlChatbotPipelineStack")

app.synth()