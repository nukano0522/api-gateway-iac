import os
from aws_cdk import (
    Stack,
    aws_apigateway as apigateway,
    CfnOutput
)
from constructs import Construct


class UsagePlanStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        openai_api: apigateway.RestApi,
        openai_prod_stage: apigateway.Stage,
        firecrawl_api: apigateway.RestApi,
        firecrawl_prod_stage: apigateway.Stage,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Basic Usage Plan - OpenAI prodステージのみアクセス可能
        basic_usage_plan = apigateway.UsagePlan(
            self, "BasicUsagePlan",
            name="basic",
            description="Basic usage plan - OpenAI prod stage only",
            throttle=apigateway.ThrottleSettings(
                rate_limit=int(os.getenv("BASIC_PLAN_THROTTLE_RATE_LIMIT", "100")),
                burst_limit=int(os.getenv("BASIC_PLAN_THROTTLE_BURST_LIMIT", "200"))
            ),
            quota=apigateway.QuotaSettings(
                limit=int(os.getenv("BASIC_PLAN_QUOTA_LIMIT", "1000")),
                period=getattr(apigateway.Period, os.getenv("BASIC_PLAN_QUOTA_PERIOD", "DAY"))
            )
        )

        # Basic プランにOpenAI prodステージを追加
        basic_usage_plan.add_api_stage(
            api=openai_api,
            stage=openai_prod_stage
        )

        # Developer Usage Plan - OpenAI & Firecrawl prodステージにアクセス可能
        developer_usage_plan = apigateway.UsagePlan(
            self, "DeveloperUsagePlan",
            name="developer",
            description="Developer usage plan - All services prod stages",
            throttle=apigateway.ThrottleSettings(
                rate_limit=int(os.getenv("DEVELOPER_PLAN_THROTTLE_RATE_LIMIT", "1000")),
                burst_limit=int(os.getenv("DEVELOPER_PLAN_THROTTLE_BURST_LIMIT", "2000"))
            ),
            quota=apigateway.QuotaSettings(
                limit=int(os.getenv("DEVELOPER_PLAN_QUOTA_LIMIT", "100000")),
                period=getattr(apigateway.Period, os.getenv("DEVELOPER_PLAN_QUOTA_PERIOD", "DAY"))
            )
        )

        # Developer プランにOpenAI prodステージを追加
        developer_usage_plan.add_api_stage(
            api=openai_api,
            stage=openai_prod_stage
        )

        # Developer プランにFirecrawl prodステージを追加
        developer_usage_plan.add_api_stage(
            api=firecrawl_api,
            stage=firecrawl_prod_stage
        )

        # Basic プラン用のAPIキー
        basic_api_key_dev = apigateway.ApiKey(
            self, "BasicDevApiKey",
            api_key_name="basic-dev-key",
            description="API key for Basic plan - development"
        )
        basic_usage_plan.add_api_key(basic_api_key_dev)

        basic_api_key_prod = apigateway.ApiKey(
            self, "BasicProdApiKey",
            api_key_name="basic-prod-key",
            description="API key for Basic plan - production"
        )
        basic_usage_plan.add_api_key(basic_api_key_prod)

        # Developer プラン用のAPIキー
        developer_api_key_dev = apigateway.ApiKey(
            self, "DeveloperDevApiKey",
            api_key_name="developer-dev-key",
            description="API key for Developer plan - development"
        )
        developer_usage_plan.add_api_key(developer_api_key_dev)

        developer_api_key_prod = apigateway.ApiKey(
            self, "DeveloperProdApiKey",
            api_key_name="developer-prod-key",
            description="API key for Developer plan - production"
        )
        developer_usage_plan.add_api_key(developer_api_key_prod)

        # 出力
        CfnOutput(
            self, "BasicDevApiKeyId",
            value=basic_api_key_dev.key_id,
            description="Basic plan development API Key ID"
        )

        CfnOutput(
            self, "BasicProdApiKeyId",
            value=basic_api_key_prod.key_id,
            description="Basic plan production API Key ID"
        )

        CfnOutput(
            self, "DeveloperDevApiKeyId",
            value=developer_api_key_dev.key_id,
            description="Developer plan development API Key ID"
        )

        CfnOutput(
            self, "DeveloperProdApiKeyId",
            value=developer_api_key_prod.key_id,
            description="Developer plan production API Key ID"
        )

        CfnOutput(
            self, "BasicUsagePlanId",
            value=basic_usage_plan.usage_plan_id,
            description="Basic Usage Plan ID"
        )

        CfnOutput(
            self, "DeveloperUsagePlanId",
            value=developer_usage_plan.usage_plan_id,
            description="Developer Usage Plan ID"
        )