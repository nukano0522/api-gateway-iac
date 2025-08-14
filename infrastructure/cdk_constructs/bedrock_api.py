import os
from aws_cdk import (
    aws_apigateway as apigateway,
    aws_iam as iam,
    aws_lambda as lambda_
)
from constructs import Construct


class BedrockApiConstruct(Construct):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        api: apigateway.RestApi,
        api_key_required: bool = True,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bedrock_base_url = os.getenv("BEDROCK_API_BASE_URL", "https://bedrock-runtime.ap-northeast-1.amazonaws.com")

        bedrock_execution_role = iam.Role(
            self, "BedrockExecutionRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            inline_policies={
                "BedrockPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "bedrock:InvokeModel",
                                "bedrock:InvokeModelWithResponseStream",
                                "bedrock:ListFoundationModels",
                                "bedrock:GetFoundationModel"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )

        bedrock_resource = api.root.add_resource("bedrock")

        models_resource = bedrock_resource.add_resource("models")
        models_resource.add_method(
            "GET",
            apigateway.AwsIntegration(
                service="bedrock",
                action="ListFoundationModels",
                options=apigateway.IntegrationOptions(
                    credentials_role=bedrock_execution_role,
                    integration_responses=[
                        apigateway.IntegrationResponse(
                            status_code="200",
                            response_parameters={
                                "method.response.header.Content-Type": "'application/json'"
                            }
                        )
                    ]
                )
            ),
            api_key_required=api_key_required,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Content-Type": True
                    }
                )
            ]
        )

        invoke_resource = bedrock_resource.add_resource("invoke")
        model_resource = invoke_resource.add_resource("{model}")
        
        model_resource.add_method(
            "POST",
            apigateway.AwsIntegration(
                service="bedrock-runtime",
                action="InvokeModel",
                options=apigateway.IntegrationOptions(
                    credentials_role=bedrock_execution_role,
                    request_parameters={
                        "integration.request.path.model": "method.request.path.model",
                        "integration.request.header.Content-Type": "'application/json'",
                        "integration.request.header.Accept": "'application/json'"
                    },
                    passthrough_behavior=apigateway.PassthroughBehavior.WHEN_NO_TEMPLATES,
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
            api_key_required=api_key_required,
            request_parameters={
                "method.request.path.model": True,
                "method.request.header.Content-Type": True
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

        invoke_stream_resource = bedrock_resource.add_resource("invoke-stream")
        stream_model_resource = invoke_stream_resource.add_resource("{model}")
        
        stream_model_resource.add_method(
            "POST",
            apigateway.AwsIntegration(
                service="bedrock-runtime",
                action="InvokeModelWithResponseStream",
                options=apigateway.IntegrationOptions(
                    credentials_role=bedrock_execution_role,
                    request_parameters={
                        "integration.request.path.model": "method.request.path.model",
                        "integration.request.header.Content-Type": "'application/json'",
                        "integration.request.header.Accept": "'application/json'"
                    },
                    passthrough_behavior=apigateway.PassthroughBehavior.WHEN_NO_TEMPLATES,
                    integration_responses=[
                        apigateway.IntegrationResponse(
                            status_code="200",
                            response_parameters={
                                "method.response.header.Content-Type": "integration.response.header.Content-Type"
                            }
                        )
                    ]
                )
            ),
            api_key_required=api_key_required,
            request_parameters={
                "method.request.path.model": True,
                "method.request.header.Content-Type": True
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Content-Type": True
                    }
                )
            ]
        )

        claude_resource = bedrock_resource.add_resource("claude")
        messages_resource = claude_resource.add_resource("messages")
        
        messages_resource.add_method(
            "POST",
            apigateway.AwsIntegration(
                service="bedrock-runtime",
                action="InvokeModel",
                options=apigateway.IntegrationOptions(
                    credentials_role=bedrock_execution_role,
                    request_templates={
                        "application/json": """
#set($inputRoot = $input.path('$'))
{
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": $inputRoot.max_tokens,
    "messages": $input.json('$.messages'),
    #if($inputRoot.system)
    "system": "$inputRoot.system",
    #end
    #if($inputRoot.temperature)
    "temperature": $inputRoot.temperature,
    #end
    #if($inputRoot.top_p)
    "top_p": $inputRoot.top_p,
    #end
    #if($inputRoot.top_k)
    "top_k": $inputRoot.top_k
    #end
}
"""
                    },
                    passthrough_behavior=apigateway.PassthroughBehavior.NEVER,
                    integration_responses=[
                        apigateway.IntegrationResponse(
                            status_code="200",
                            response_parameters={
                                "method.response.header.Content-Type": "'application/json'"
                            }
                        )
                    ]
                )
            ),
            api_key_required=api_key_required,
            request_parameters={
                "method.request.header.Content-Type": True
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Content-Type": True
                    }
                )
            ]
        )