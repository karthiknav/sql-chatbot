#!/usr/bin/env python3
import aws_cdk as cdk
from cdk_pipeline_stack import SqlChatbotPipelineStack

app = cdk.App()
SqlChatbotPipelineStack(app, "SqlChatbotPipelineStack")
app.synth()