import os
from aws_cdk import (
    aws_apigateway as apigateway,
    aws_iam as iam
)
from constructs import Construct


class FirecrawlApiConstruct(Construct):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        api: apigateway.RestApi,
        api_key_required: bool = True,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        firecrawl_base_url = os.getenv("FIRECRAWL_API_BASE_URL", "https://api.firecrawl.dev/v1")
        firecrawl_api_key_name = os.getenv("FIRECRAWL_API_KEY_NAME", "firecrawl-api-key")

        firecrawl_resource = api.root.add_resource("firecrawl")

        firecrawl_proxy_resource = firecrawl_resource.add_proxy(
            default_integration=apigateway.HttpIntegration(
                f"{firecrawl_base_url}/{{proxy}}",
                proxy=True,
                options=apigateway.IntegrationOptions(
                    request_parameters={
                        "integration.request.path.proxy": "method.request.path.proxy",
                        "integration.request.header.Authorization": f"'Bearer {firecrawl_api_key_name}'",
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

        scrape_resource = firecrawl_resource.add_resource("scrape")
        scrape_resource.add_method(
            "POST",
            apigateway.HttpIntegration(
                f"{firecrawl_base_url}/scrape",
                proxy=False,
                options=apigateway.IntegrationOptions(
                    request_parameters={
                        "integration.request.header.Authorization": f"'Bearer {firecrawl_api_key_name}'",
                        "integration.request.header.Content-Type": "method.request.header.Content-Type"
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
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Content-Type": True
                    }
                )
            ]
        )

        crawl_resource = firecrawl_resource.add_resource("crawl")
        crawl_resource.add_method(
            "POST",
            apigateway.HttpIntegration(
                f"{firecrawl_base_url}/crawl",
                proxy=False,
                options=apigateway.IntegrationOptions(
                    request_parameters={
                        "integration.request.header.Authorization": f"'Bearer {firecrawl_api_key_name}'",
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

        crawl_status_resource = crawl_resource.add_resource("status")
        job_id_resource = crawl_status_resource.add_resource("{jobId}")
        
        job_id_resource.add_method(
            "GET",
            apigateway.HttpIntegration(
                f"{firecrawl_base_url}/crawl/status/{{jobId}}",
                proxy=False,
                options=apigateway.IntegrationOptions(
                    request_parameters={
                        "integration.request.path.jobId": "method.request.path.jobId",
                        "integration.request.header.Authorization": f"'Bearer {firecrawl_api_key_name}'"
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
                "method.request.path.jobId": True
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

        search_resource = firecrawl_resource.add_resource("search")
        search_resource.add_method(
            "POST",
            apigateway.HttpIntegration(
                f"{firecrawl_base_url}/search",
                proxy=False,
                options=apigateway.IntegrationOptions(
                    request_parameters={
                        "integration.request.header.Authorization": f"'Bearer {firecrawl_api_key_name}'",
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