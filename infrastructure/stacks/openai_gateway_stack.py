import os
from aws_cdk import (
    Stack,
    aws_apigateway as apigateway,
    aws_logs as logs,
    CfnOutput,
    RemovalPolicy,
    Duration
)
from constructs import Construct
from cdk_constructs.openai_api import OpenAIApiConstruct


class OpenAIGatewayStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        api_name = "openai-gw"
        log_group = logs.LogGroup(
            self, "OpenAIApiGatewayLogGroup",
            log_group_name=f"/aws/apigateway/{api_name}",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY
        )

        # OpenAI専用API Gateway
        self.rest_api = apigateway.RestApi(
            self, "OpenAIApiGateway",
            rest_api_name=api_name,
            description="API Gateway for OpenAI services",
            deploy=False,  # ステージを手動で管理
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
                allow_headers=os.getenv("CORS_ALLOW_HEADERS", "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token").split(","),
                allow_methods=os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(","),
                allow_credentials=False,
                max_age=Duration.hours(1)
            ),
            endpoint_types=[apigateway.EndpointType.REGIONAL]
        )

        # OpenAI APIコンストラクトの追加
        openai_construct = OpenAIApiConstruct(
            self, "OpenAIApi",
            api=self.rest_api,
            api_key_required=True
        )

        # デプロイメントの作成
        deployment = apigateway.Deployment(
            self, "OpenAIApiDeployment",
            api=self.rest_api
        )

        # devステージの作成
        dev_stage = apigateway.Stage(
            self, "OpenAIDevStage",
            deployment=deployment,
            stage_name="dev",
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
        )

        # prodステージの作成
        self.prod_stage = apigateway.Stage(
            self, "OpenAIProdStage",
            deployment=deployment,
            stage_name="prod",
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
        )

        # API Gatewayの出力
        CfnOutput(
            self, "OpenAIApiGatewayUrl",
            value=f"https://{self.rest_api.rest_api_id}.execute-api.{self.region}.amazonaws.com",
            description="OpenAI API Gateway base URL"
        )

        CfnOutput(
            self, "OpenAIApiGatewayRestApiId",
            value=self.rest_api.rest_api_id,
            description="OpenAI API Gateway REST API ID"
        )

        CfnOutput(
            self, "OpenAIApiGatewayDevUrl",
            value=dev_stage.url_for_path("/"),
            description="OpenAI API Gateway dev stage URL"
        )

        CfnOutput(
            self, "OpenAIApiGatewayProdUrl",
            value=self.prod_stage.url_for_path("/"),
            description="OpenAI API Gateway prod stage URL"
        )