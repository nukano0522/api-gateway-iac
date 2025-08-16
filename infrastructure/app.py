#!/usr/bin/env python3
import os
from aws_cdk import App, Environment
from dotenv import load_dotenv
from stacks.openai_gateway_stack import OpenAIGatewayStack
from stacks.firecrawl_gateway_stack import FirecrawlGatewayStack
from stacks.usage_plan_stack import UsagePlanStack

load_dotenv()

app = App()

env = Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT", os.environ.get("CDK_DEFAULT_ACCOUNT")),
    region=os.getenv("CDK_DEFAULT_REGION", os.environ.get("CDK_DEFAULT_REGION", "ap-northeast-1"))
)

# OpenAI Gateway Stack
openai_stack = OpenAIGatewayStack(
    app,
    "OpenAIGatewayStack",
    env=env,
    stack_name="openai-gateway-stack",
    description="API Gateway for OpenAI services"
)

# Firecrawl Gateway Stack
firecrawl_stack = FirecrawlGatewayStack(
    app,
    "FirecrawlGatewayStack",
    env=env,
    stack_name="firecrawl-gateway-stack",
    description="API Gateway for Firecrawl services"
)

# Usage Plan Stack (依存関係: OpenAI & Firecrawl スタック)
usage_plan_stack = UsagePlanStack(
    app,
    "UsagePlanStack",
    openai_api=openai_stack.rest_api,
    openai_prod_stage=openai_stack.prod_stage,
    firecrawl_api=firecrawl_stack.rest_api,
    firecrawl_prod_stage=firecrawl_stack.prod_stage,
    env=env,
    stack_name="usage-plan-stack",
    description="Usage plans and API keys management"
)

# スタック間の依存関係を設定
usage_plan_stack.add_dependency(openai_stack)
usage_plan_stack.add_dependency(firecrawl_stack)

app.synth()