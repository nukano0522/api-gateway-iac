import os
from aws_cdk import (
    Stack,
    aws_apigateway as apigateway,
    aws_logs as logs,
    aws_iam as iam,
    CfnOutput,
    RemovalPolicy,
    Duration
)
from constructs import Construct
from cdk_constructs.openai_api import OpenAIApiConstruct
# from cdk_constructs.bedrock_api import BedrockApiConstruct
# from cdk_constructs.firecrawl_api import FirecrawlApiConstruct
# from cdk_constructs.dify_api import DifyApiConstruct


class ApiGatewayStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        api_name = os.getenv("API_GATEWAY_NAME", "multi-api-gateway")
        stage_name = os.getenv("API_GATEWAY_STAGE", "prod")
        log_group = logs.LogGroup(
            self, "ApiGatewayLogGroup",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY
        )

        rest_api = apigateway.RestApi(
            self, "MultiApiGateway",
            rest_api_name=api_name,
            description="Unified API Gateway for multiple API services",
            deploy_options=apigateway.StageOptions(
                stage_name=stage_name,
                logging_level=apigateway.MethodLoggingLevel.INFO if os.getenv("ENABLE_CLOUDWATCH_LOGS", "true").lower() == "true" else apigateway.MethodLoggingLevel.OFF,
                data_trace_enabled=os.getenv("ENABLE_DETAILED_METRICS", "true").lower() == "true",
                tracing_enabled=os.getenv("ENABLE_XRAY_TRACING", "true").lower() == "true",
                access_log_destination=apigateway.LogGroupLogDestination(log_group),
                access_log_format=apigateway.AccessLogFormat.json_with_standard_fields(
                    caller=True,
                    http_method=True,
                    ip=True,
                    protocol=True,
                    request_time=True,
                    resource_path=True,
                    response_length=True,
                    status=True,
                    user=True
                )
            ),
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
                allow_headers=os.getenv("CORS_ALLOW_HEADERS", "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token").split(","),
                allow_methods=os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(","),
                allow_credentials=False,
                max_age=Duration.hours(1)
            ),
            endpoint_types=[apigateway.EndpointType.REGIONAL]
        )

        usage_plan = rest_api.add_usage_plan(
            "UsagePlan",
            name=os.getenv("USAGE_PLAN_NAME", "standard-plan"),
            description="Standard usage plan for API access",
            throttle=apigateway.ThrottleSettings(
                rate_limit=int(os.getenv("USAGE_PLAN_THROTTLE_RATE_LIMIT", "1000")),
                burst_limit=int(os.getenv("USAGE_PLAN_THROTTLE_BURST_LIMIT", "2000"))
            ),
            quota=apigateway.QuotaSettings(
                limit=int(os.getenv("USAGE_PLAN_QUOTA_LIMIT", "10000")),
                period=getattr(apigateway.Period, os.getenv("USAGE_PLAN_QUOTA_PERIOD", "DAY"))
            )
        )

        dev_api_key = apigateway.ApiKey(
            self, "DevApiKey",
            api_key_name=os.getenv("DEV_API_KEY_NAME", "dev-api-key"),
            description="API key for development environment"
        )
        usage_plan.add_api_key(dev_api_key)

        prod_api_key = apigateway.ApiKey(
            self, "ProdApiKey",
            api_key_name=os.getenv("PROD_API_KEY_NAME", "prod-api-key"),
            description="API key for production environment"
        )
        usage_plan.add_api_key(prod_api_key)

        api_key_required = True

        openai_construct = OpenAIApiConstruct(
            self, "OpenAIApi",
            api=rest_api,
            api_key_required=api_key_required
        )

        # bedrock_construct = BedrockApiConstruct(
        #     self, "BedrockApi",
        #     api=rest_api,
        #     api_key_required=api_key_required
        # )

        # firecrawl_construct = FirecrawlApiConstruct(
        #     self, "FirecrawlApi",
        #     api=rest_api,
        #     api_key_required=api_key_required
        # )

        # dify_construct = DifyApiConstruct(
        #     self, "DifyApi",
        #     api=rest_api,
        #     api_key_required=api_key_required
        # )

        usage_plan.add_api_stage(
            api=rest_api,
            stage=rest_api.deployment_stage
        )

        CfnOutput(
            self, "ApiGatewayUrl",
            value=rest_api.url,
            description="API Gateway endpoint URL"
        )

        CfnOutput(
            self, "ApiGatewayRestApiId",
            value=rest_api.rest_api_id,
            description="API Gateway REST API ID"
        )

        CfnOutput(
            self, "DevApiKeyId",
            value=dev_api_key.key_id,
            description="Development API Key ID"
        )

        CfnOutput(
            self, "ProdApiKeyId",
            value=prod_api_key.key_id,
            description="Production API Key ID"
        )