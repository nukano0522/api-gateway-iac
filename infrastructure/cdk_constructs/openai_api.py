import os
from aws_cdk import (
    aws_apigateway as apigateway,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager
)
from constructs import Construct


class OpenAIApiConstruct(Construct):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        api: apigateway.RestApi,
        api_key_required: bool = True,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        openai_base_url = os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
        openai_api_key_name = os.getenv("OPENAI_API_KEY_NAME", "openai-api-key")

        openai_resource = api.root.add_resource("openai")
        openai_proxy_resource = openai_resource.add_proxy(
            default_integration=apigateway.HttpIntegration(
                f"{openai_base_url}/{{proxy}}",
                proxy=True,
                http_method="ANY",
                options=apigateway.IntegrationOptions(
                    passthrough_behavior=apigateway.PassthroughBehavior.WHEN_NO_TEMPLATES,
                    request_parameters={
                        "integration.request.path.proxy": "method.request.path.proxy",
                        "integration.request.header.Authorization": f"'Bearer {os.getenv('OPENAI_API_KEY')}'"
                    },
                    integration_responses=[
                        apigateway.IntegrationResponse(
                            status_code="200",
                            response_parameters={
                                "method.response.header.Content-Type": "integration.response.header.Content-Type"
                            }
                        ),
                        apigateway.IntegrationResponse(
                            status_code="400",
                            selection_pattern="4\\d{2}",
                            response_parameters={
                                "method.response.header.Content-Type": "integration.response.header.Content-Type"
                            }
                        ),
                        apigateway.IntegrationResponse(
                            status_code="500",
                            selection_pattern="5\\d{2}",
                            response_parameters={
                                "method.response.header.Content-Type": "integration.response.header.Content-Type"
                            }
                        )
                    ]
                )
            ),
            any_method=True,
            default_method_options=apigateway.MethodOptions(
                api_key_required=api_key_required,
                request_parameters={
                    "method.request.path.proxy": True,
                    # "method.request.header.Content-Type": False,
                    # "method.request.header.Accept": False
                },
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Content-Type": True
                        }
                    ),
                    apigateway.MethodResponse(
                        status_code="400",
                        response_parameters={
                            "method.response.header.Content-Type": True
                        }
                    ),
                    apigateway.MethodResponse(
                        status_code="500",
                        response_parameters={
                            "method.response.header.Content-Type": True
                        }
                    )
                ]
            )
        )