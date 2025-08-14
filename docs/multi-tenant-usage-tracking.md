# マルチテナント環境でのAPI使用量・コスト管理設計

## 概要

複数の利用者や組織がAPIを使用する際に、各テナント（利用者/組織）ごとの使用量とコストを可視化するための設計ガイド。

## 設計パターン

### パターン1: API Key ベースの管理（シンプル）

```
┌─────────────────────────────────────────────────────┐
│                   利用者/組織                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ 組織A    │  │ 組織B    │  │ 組織C    │        │
│  │ API Key1 │  │ API Key2 │  │ API Key3 │        │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘        │
└────────┼──────────────┼──────────────┼─────────────┘
         ▼              ▼              ▼
┌─────────────────────────────────────────────────────┐
│                 API Gateway                          │
│  ┌────────────────────────────────────────────┐     │
│  │           Usage Plans & API Keys            │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐  │     │
│  │  │  Plan A  │ │  Plan B  │ │  Plan C  │  │     │
│  │  │  Key: 1  │ │  Key: 2  │ │  Key: 3  │  │     │
│  │  │Limit:1000│ │Limit:5000│ │Limit:10000│ │     │
│  │  └──────────┘ └──────────┘ └──────────┘  │     │
│  └────────────────────────────────────────────┘     │
│                        ▼                             │
│  ┌────────────────────────────────────────────┐     │
│  │         CloudWatch Logs & Metrics          │     │
│  │    - API Key別のメトリクス自動収集          │     │
│  │    - カスタムメトリクスで詳細追跡          │     │
│  └────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘
```

**実装方法:**

```python
# CDK実装例
class MultiTenantApiStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        # 組織ごとのUsage Plan作成
        organizations = [
            {"name": "org-a", "limit": 1000, "burst": 2000, "quota": 100000},
            {"name": "org-b", "limit": 5000, "burst": 10000, "quota": 500000},
            {"name": "org-c", "limit": 10000, "burst": 20000, "quota": 1000000},
        ]
        
        for org in organizations:
            # Usage Plan作成
            usage_plan = api.add_usage_plan(
                f"{org['name']}-plan",
                name=f"{org['name']}-usage-plan",
                throttle=apigateway.ThrottleSettings(
                    rate_limit=org['limit'],
                    burst_limit=org['burst']
                ),
                quota=apigateway.QuotaSettings(
                    limit=org['quota'],
                    period=apigateway.Period.MONTH
                )
            )
            
            # API Key作成
            api_key = apigateway.ApiKey(
                self, f"{org['name']}-key",
                api_key_name=f"{org['name']}-api-key",
                description=f"API key for {org['name']}"
            )
            
            usage_plan.add_api_key(api_key)
            
            # タグ付け（コスト配分用）
            Tags.of(api_key).add("Organization", org['name'])
            Tags.of(api_key).add("CostCenter", f"cc-{org['name']}")
```

### パターン2: Lambda Authorizer + DynamoDB（詳細管理）

```
┌─────────────────────────────────────────────────────┐
│                   利用者/組織                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ 組織A    │  │ 組織B    │  │ 組織C    │        │
│  │ Token1   │  │ Token2   │  │ Token3   │        │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘        │
└────────┼──────────────┼──────────────┼─────────────┘
         ▼              ▼              ▼
┌─────────────────────────────────────────────────────┐
│                 API Gateway                          │
│         ▼                                            │
│  ┌──────────────────────────────────────────┐       │
│  │         Lambda Authorizer                │       │
│  │  - トークン検証                          │       │
│  │  - 組織ID取得                           │       │
│  │  - 使用量チェック                       │       │
│  │  - コンテキスト設定                     │       │
│  └──────────────┬───────────────────────────┘       │
│                 ▼                                    │
│  ┌──────────────────────────────────────────┐       │
│  │         Lambda Function                  │       │
│  │  - リクエスト処理                        │       │
│  │  - 使用量記録                           │       │
│  │  - コスト計算                           │       │
│  └──────────────┬───────────────────────────┘       │
└─────────────────┼────────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────┐
│              DynamoDB Tables                         │
│  ┌──────────────────────────────────────────┐       │
│  │         organizations テーブル            │       │
│  │  - org_id (PK)                          │       │
│  │  - name, plan, limits, created_at       │       │
│  └──────────────────────────────────────────┘       │
│  ┌──────────────────────────────────────────┐       │
│  │         usage_records テーブル           │       │
│  │  - org_id (PK), timestamp (SK)          │       │
│  │  - endpoint, method, response_size      │       │
│  │  - latency, status_code, cost           │       │
│  └──────────────────────────────────────────┘       │
│  ┌──────────────────────────────────────────┐       │
│  │         monthly_summary テーブル         │       │
│  │  - org_id (PK), month (SK)              │       │
│  │  - total_requests, total_cost           │       │
│  │  - endpoint_breakdown                    │       │
│  └──────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────┘
```

**Lambda Authorizer実装例:**

```python
import json
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
org_table = dynamodb.Table('organizations')
usage_table = dynamodb.Table('usage_records')

def handler(event, context):
    # トークンから組織ID取得
    token = event['authorizationToken']
    org_id = validate_and_get_org_id(token)
    
    if not org_id:
        raise Exception('Unauthorized')
    
    # 組織情報取得
    org_info = org_table.get_item(Key={'org_id': org_id})['Item']
    
    # 使用量チェック
    current_usage = get_current_month_usage(org_id)
    if current_usage >= org_info['monthly_limit']:
        raise Exception('Quota exceeded')
    
    # ポリシー生成
    policy = generate_policy('Allow', event['methodArn'])
    
    # コンテキストに組織情報を追加
    policy['context'] = {
        'org_id': org_id,
        'org_name': org_info['name'],
        'plan': org_info['plan'],
        'remaining_quota': str(org_info['monthly_limit'] - current_usage)
    }
    
    return policy

def generate_policy(effect, resource):
    return {
        'principalId': 'user',
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': effect,
                'Resource': resource
            }]
        }
    }
```

### パターン3: API Gateway + Kinesis Data Firehose（リアルタイム分析）

```
┌─────────────────────────────────────────────────────┐
│                 API Gateway                          │
│  ┌──────────────────────────────────────────┐       │
│  │         CloudWatch Logs                  │       │
│  │  - 全APIアクセスログ                     │       │
│  │  - APIキー情報含む                       │       │
│  └──────────────┬───────────────────────────┘       │
└─────────────────┼────────────────────────────────────┘
                  ▼
┌──────────────────────────────────────────────────────┐
│          Kinesis Data Firehose                       │
│  - リアルタイムストリーミング                         │
│  - データ変換（Lambda）                              │
│  - バッファリング & 圧縮                             │
└──────────────┬────────────────┬─────────────────────┘
               ▼                ▼
┌───────────────────┐  ┌──────────────────────┐
│      S3 Bucket    │  │    ElasticSearch     │
│  - 長期保存       │  │  - リアルタイム分析   │
│  - Athena分析     │  │  - Kibanaダッシュボード│
└───────────────────┘  └──────────────────────┘
```

## コスト計算と配分

### 1. 使用量メトリクスの収集

```python
# CloudWatch カスタムメトリクス記録
def record_usage_metrics(org_id, endpoint, request_size, response_size):
    cloudwatch = boto3.client('cloudwatch')
    
    # API呼び出し回数
    cloudwatch.put_metric_data(
        Namespace='APIGateway/Usage',
        MetricData=[
            {
                'MetricName': 'RequestCount',
                'Dimensions': [
                    {'Name': 'Organization', 'Value': org_id},
                    {'Name': 'Endpoint', 'Value': endpoint}
                ],
                'Value': 1,
                'Unit': 'Count',
                'Timestamp': datetime.utcnow()
            },
            {
                'MetricName': 'DataTransfer',
                'Dimensions': [
                    {'Name': 'Organization', 'Value': org_id}
                ],
                'Value': request_size + response_size,
                'Unit': 'Bytes',
                'Timestamp': datetime.utcnow()
            }
        ]
    )
```

### 2. コスト計算ロジック

```python
def calculate_cost(org_id, month):
    # 料金定数（東京リージョン）
    PRICE_PER_MILLION_REQUESTS = 4.25
    PRICE_PER_GB_TRANSFER = 0.114
    
    # 使用量取得
    usage = get_monthly_usage(org_id, month)
    
    # コスト計算
    request_cost = (usage['request_count'] / 1_000_000) * PRICE_PER_MILLION_REQUESTS
    transfer_cost = (usage['data_transfer_gb']) * PRICE_PER_GB_TRANSFER
    
    # OpenAI API使用料（例）
    openai_cost = calculate_openai_cost(usage['openai_tokens'])
    
    return {
        'org_id': org_id,
        'month': month,
        'api_gateway_cost': request_cost + transfer_cost,
        'openai_cost': openai_cost,
        'total_cost': request_cost + transfer_cost + openai_cost,
        'breakdown': {
            'requests': {'count': usage['request_count'], 'cost': request_cost},
            'data_transfer': {'gb': usage['data_transfer_gb'], 'cost': transfer_cost},
            'openai': {'tokens': usage['openai_tokens'], 'cost': openai_cost}
        }
    }
```

### 3. ダッシュボード設計

```yaml
# CloudWatch Dashboard定義
Dashboard:
  - 組織別使用量:
      - API呼び出し回数（時系列）
      - データ転送量（時系列）
      - エラー率
      - レイテンシー
  
  - コスト分析:
      - 組織別月間コスト
      - エンドポイント別コスト
      - 前月比較
      - 予測コスト
  
  - アラート:
      - 使用量制限の80%到達
      - 異常なスパイク検知
      - エラー率上昇
```

## 実装オプションの比較

| 項目 | API Key方式 | Lambda Authorizer | Kinesis方式 |
|------|------------|------------------|------------|
| **実装難易度** | 低 | 中 | 高 |
| **初期コスト** | 低 | 中 | 高 |
| **カスタマイズ性** | 低 | 高 | 高 |
| **リアルタイム性** | 低 | 中 | 高 |
| **スケーラビリティ** | 高 | 中 | 高 |
| **詳細度** | 基本的 | 詳細 | 非常に詳細 |

## 推奨アーキテクチャ

### スモールスタート（組織数 < 10）
```
API Key + CloudWatch Metrics + 月次レポート
- 実装が簡単
- AWS標準機能で完結
- コスト最小
```

### 中規模（組織数 10-100）
```
Lambda Authorizer + DynamoDB + CloudWatch Dashboard
- 柔軟な制御
- リアルタイム使用量追跡
- カスタムレポート可能
```

### 大規模（組織数 > 100）
```
Lambda Authorizer + Kinesis + ElasticSearch + S3
- 完全なリアルタイム分析
- 高度な可視化
- 長期データ保持
```

## セットアップ手順

### Step 1: 基本構成（API Key方式）

```bash
# 1. Usage Plan作成
aws apigateway create-usage-plan \
  --name "org-a-plan" \
  --throttle burstLimit=2000,rateLimit=1000 \
  --quota limit=100000,period=MONTH

# 2. API Key作成
aws apigateway create-api-key \
  --name "org-a-key" \
  --enabled \
  --tags Organization=OrgA,CostCenter=CC001

# 3. CloudWatchダッシュボード作成
aws cloudwatch put-dashboard \
  --dashboard-name APIUsageByOrg \
  --dashboard-body file://dashboard.json
```

### Step 2: 使用量追跡Lambda

```python
# usage_tracker.py
import json
import boto3
from decimal import Decimal

def handler(event, context):
    # APIGatewayのコンテキストから情報取得
    org_id = event['requestContext']['authorizer']['org_id']
    api_key = event['requestContext']['identity']['apiKey']
    endpoint = event['resource']
    method = event['httpMethod']
    
    # レスポンスサイズ計算
    response_size = len(json.dumps(event['body']))
    
    # DynamoDBに記録
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('api_usage')
    
    table.put_item(
        Item={
            'org_id': org_id,
            'timestamp': context.aws_request_id,
            'api_key': api_key,
            'endpoint': endpoint,
            'method': method,
            'response_size': response_size,
            'cost': calculate_request_cost(response_size)
        }
    )
    
    return {
        'statusCode': 200,
        'headers': {
            'X-Organization-ID': org_id,
            'X-Request-Cost': str(calculate_request_cost(response_size))
        }
    }
```

### Step 3: 月次レポート生成

```python
# monthly_report.py
import boto3
from datetime import datetime, timedelta
import pandas as pd

def generate_monthly_report():
    # 前月のデータ取得
    end_date = datetime.now().replace(day=1) - timedelta(days=1)
    start_date = end_date.replace(day=1)
    
    # CloudWatchメトリクス取得
    cloudwatch = boto3.client('cloudwatch')
    
    organizations = ['org-a', 'org-b', 'org-c']
    report_data = []
    
    for org in organizations:
        metrics = cloudwatch.get_metric_statistics(
            Namespace='AWS/ApiGateway',
            MetricName='Count',
            Dimensions=[
                {'Name': 'ApiName', 'Value': 'multi-api-gateway'},
                {'Name': 'ApiKeyName', 'Value': f'{org}-key'}
            ],
            StartTime=start_date,
            EndTime=end_date,
            Period=2592000,  # 30 days
            Statistics=['Sum']
        )
        
        total_requests = metrics['Datapoints'][0]['Sum'] if metrics['Datapoints'] else 0
        cost = calculate_monthly_cost(org, total_requests)
        
        report_data.append({
            'Organization': org,
            'Month': start_date.strftime('%Y-%m'),
            'Total Requests': total_requests,
            'API Gateway Cost': cost['api_gateway'],
            'OpenAI Cost': cost['openai'],
            'Total Cost': cost['total']
        })
    
    # レポート生成
    df = pd.DataFrame(report_data)
    df.to_csv(f'monthly_report_{start_date.strftime("%Y%m")}.csv', index=False)
    
    # メール送信やS3アップロードなど
    send_report_email(df)
```

## ベストプラクティス

1. **段階的実装**
   - まずAPI Keyベースで開始
   - 必要に応じて詳細な追跡を追加

2. **コスト配分タグ**
   - すべてのリソースに組織タグを付与
   - AWS Cost Explorerで分析可能に

3. **アラート設定**
   - 使用量の異常検知
   - 予算超過の事前通知

4. **データ保持期間**
   - 詳細ログ: 30日
   - 集計データ: 13ヶ月
   - 請求データ: 7年

5. **セキュリティ**
   - API Keyの定期ローテーション
   - 最小権限の原則
   - 監査ログの有効化