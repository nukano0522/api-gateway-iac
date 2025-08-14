import os
from aws_cdk import (
    aws_apigateway as apigateway,
    aws_iam as iam
)
from constructs import Construct


class DifyApiConstruct(Construct):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        api: apigateway.RestApi,
        api_key_required: bool = True,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        dify_base_url = os.getenv("DIFY_API_BASE_URL", "https://api.dify.ai/v1")
        dify_api_key_name = os.getenv("DIFY_API_KEY_NAME", "dify-api-key")

        dify_resource = api.root.add_resource("dify")

        dify_proxy_resource = dify_resource.add_proxy(
            default_integration=apigateway.HttpIntegration(
                f"{dify_base_url}/{{proxy}}",
                proxy=True,
                options=apigateway.IntegrationOptions(
                    request_parameters={
                        "integration.request.path.proxy": "method.request.path.proxy",
                        "integration.request.header.Authorization": f"'Bearer {dify_api_key_name}'",
                        "integration.request.header.Content-Type": "method.request.header.Content-Type",
                        "integration.request.header.Accept": "method.request.header.Accept"
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
                    "method.request.header.Content-Type": False,
                    "method.request.header.Accept": False
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

        chat_messages_resource = dify_resource.add_resource("chat-messages")
        chat_messages_resource.add_method(
            "POST",
            apigateway.HttpIntegration(
                f"{dify_base_url}/chat-messages",
                proxy=False,
                options=apigateway.IntegrationOptions(
                    request_parameters={
                        "integration.request.header.Authorization": f"'Bearer {dify_api_key_name}'",
                        "integration.request.header.Content-Type": "method.request.header.Content-Type"
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

        completion_messages_resource = dify_resource.add_resource("completion-messages")
        completion_messages_resource.add_method(
            "POST",
            apigateway.HttpIntegration(
                f"{dify_base_url}/completion-messages",
                proxy=False,
                options=apigateway.IntegrationOptions(
                    request_parameters={
                        "integration.request.header.Authorization": f"'Bearer {dify_api_key_name}'",
                        "integration.request.header.Content-Type": "method.request.header.Content-Type"
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

        workflows_resource = dify_resource.add_resource("workflows")
        run_resource = workflows_resource.add_resource("run")
        run_resource.add_method(
            "POST",
            apigateway.HttpIntegration(
                f"{dify_base_url}/workflows/run",
                proxy=False,
                options=apigateway.IntegrationOptions(
                    request_parameters={
                        "integration.request.header.Authorization": f"'Bearer {dify_api_key_name}'",
                        "integration.request.header.Content-Type": "method.request.header.Content-Type"
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

        conversations_resource = dify_resource.add_resource("conversations")
        conversations_resource.add_method(
            "GET",
            apigateway.HttpIntegration(
                f"{dify_base_url}/conversations",
                proxy=False,
                options=apigateway.IntegrationOptions(
                    request_parameters={
                        "integration.request.header.Authorization": f"'Bearer {dify_api_key_name}'",
                        "integration.request.querystring.user": "method.request.querystring.user",
                        "integration.request.querystring.last_id": "method.request.querystring.last_id",
                        "integration.request.querystring.limit": "method.request.querystring.limit"
                    },
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
                "method.request.querystring.user": False,
                "method.request.querystring.last_id": False,
                "method.request.querystring.limit": False
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

        messages_resource = dify_resource.add_resource("messages")
        messages_resource.add_method(
            "GET",
            apigateway.HttpIntegration(
                f"{dify_base_url}/messages",
                proxy=False,
                options=apigateway.IntegrationOptions(
                    request_parameters={
                        "integration.request.header.Authorization": f"'Bearer {dify_api_key_name}'",
                        "integration.request.querystring.conversation_id": "method.request.querystring.conversation_id",
                        "integration.request.querystring.user": "method.request.querystring.user",
                        "integration.request.querystring.first_id": "method.request.querystring.first_id",
                        "integration.request.querystring.limit": "method.request.querystring.limit"
                    },
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
                "method.request.querystring.conversation_id": True,
                "method.request.querystring.user": True,
                "method.request.querystring.first_id": False,
                "method.request.querystring.limit": False
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

        feedback_resource = messages_resource.add_resource("{message_id}")
        feedbacks_resource = feedback_resource.add_resource("feedbacks")
        feedbacks_resource.add_method(
            "POST",
            apigateway.HttpIntegration(
                f"{dify_base_url}/messages/{{message_id}}/feedbacks",
                proxy=False,
                options=apigateway.IntegrationOptions(
                    request_parameters={
                        "integration.request.path.message_id": "method.request.path.message_id",
                        "integration.request.header.Authorization": f"'Bearer {dify_api_key_name}'",
                        "integration.request.header.Content-Type": "method.request.header.Content-Type"
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
                "method.request.path.message_id": True,
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