#!/usr/bin/env python3
import os
from aws_cdk import App, Environment
from dotenv import load_dotenv
from stacks.api_gateway_stack import ApiGatewayStack

load_dotenv()

app = App()

env = Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT", os.environ.get("CDK_DEFAULT_ACCOUNT")),
    region=os.getenv("CDK_DEFAULT_REGION", os.environ.get("CDK_DEFAULT_REGION", "ap-northeast-1"))
)

ApiGatewayStack(
    app,
    "ApiGatewayStack",
    env=env,
    stack_name=os.getenv("STACK_NAME", "api-gateway-integration-stack"),
    description="API Gateway integration stack for multiple API services"
)

app.synth()