# API Gateway 使用量プラン（組織）ごとのCloudWatchメトリクス分析ガイド

## 概要

AWS API Gatewayは標準でCloudWatchメトリクスを送信しますが、**使用量プラン（Usage Plan）やAPIキーごとのメトリクスは自動的に送信されません**。このドキュメントでは、組織別（使用量プラン別）の使用状況を分析するための複数のソリューションを提供します。

## 問題点

### 現在のCloudWatchメトリクスの制限

API Gatewayが提供する標準ディメンション：
- `ApiName` - API名でのフィルタリング
- `ApiName, Stage` - API名とステージでのフィルタリング
- `ApiName, Method, Resource, Stage` - メソッドレベルの詳細フィルタリング

**利用できないディメンション：**
- ❌ `UsagePlanId` / `UsagePlanName`
- ❌ `ApiKeyId` / `ApiKeyName`
- ❌ 組織やテナント識別子

## 解決策1: Lambda + EventBridgeによる自動化

### アーキテクチャ

```
EventBridge (5分ごと) → Lambda → API Gateway Usage API → CloudWatch Custom Metrics
```

### Lambda関数の実装

```python
import boto3
import json
from datetime import datetime
from typing import List, Dict, Any

apigateway = boto3.client('apigateway')
cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    API Gateway使用量プランのメトリクスを取得してCloudWatchに送信
    """
    try:
        # すべての使用量プランを取得
        usage_plans = get_all_usage_plans()
        
        for plan in usage_plans:
            process_usage_plan(plan)
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Processed {len(usage_plans)} usage plans')
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }

def get_all_usage_plans() -> List[Dict[str, Any]]:
    """すべての使用量プランを取得"""
    usage_plans = []
    paginator = apigateway.get_paginator('get_usage_plans')
    
    for page in paginator.paginate():
        usage_plans.extend(page['items'])
    
    return usage_plans

def process_usage_plan(plan: Dict[str, Any]) -> None:
    """使用量プランのメトリクスを処理"""
    plan_id = plan['id']
    plan_name = plan.get('name', 'unnamed')
    
    # APIキーごとの使用量を取得
    api_keys = get_api_keys_for_plan(plan_id)
    
    for key in api_keys:
        process_api_key_usage(plan_id, plan_name, key)

def get_api_keys_for_plan(plan_id: str) -> List[Dict[str, Any]]:
    """使用量プランに関連付けられたAPIキーを取得"""
    api_keys = []
    paginator = apigateway.get_paginator('get_usage_plan_keys')
    
    for page in paginator.paginate(usagePlanId=plan_id):
        api_keys.extend(page['items'])
    
    return api_keys

def process_api_key_usage(plan_id: str, plan_name: str, key: Dict[str, Any]) -> None:
    """APIキーの使用状況をCloudWatchに送信"""
    key_id = key['id']
    key_name = key.get('name', 'unnamed')
    
    # 現在の使用状況を取得
    usage = get_current_usage(plan_id, key_id)
    
    if usage:
        # CloudWatchカスタムメトリクスを送信
        send_metrics_to_cloudwatch(
            plan_id=plan_id,
            plan_name=plan_name,
            key_id=key_id,
            key_name=key_name,
            usage=usage
        )

def get_current_usage(plan_id: str, key_id: str) -> Dict[str, Any]:
    """現在の期間の使用状況を取得"""
    try:
        # 現在の期間を計算（日次の場合）
        today = datetime.now().strftime('%Y-%m-%d')
        
        response = apigateway.get_usage(
            usagePlanId=plan_id,
            keyId=key_id,
            startDate=today,
            endDate=today
        )
        
        # 使用量を集計
        total_usage = 0
        if 'items' in response:
            for item in response['items'].values():
                for api_data in item:
                    total_usage += sum(api_data[1])
        
        # 使用量プランのクォータを取得
        plan = apigateway.get_usage_plan(usagePlanId=plan_id)
        quota_limit = plan.get('quota', {}).get('limit', 0)
        
        return {
            'usage': total_usage,
            'limit': quota_limit,
            'percentage': (total_usage / quota_limit * 100) if quota_limit > 0 else 0
        }
    except Exception as e:
        print(f"Error getting usage for plan {plan_id}, key {key_id}: {str(e)}")
        return None

def send_metrics_to_cloudwatch(
    plan_id: str,
    plan_name: str,
    key_id: str,
    key_name: str,
    usage: Dict[str, Any]
) -> None:
    """CloudWatchにカスタムメトリクスを送信"""
    namespace = 'Custom/APIGateway'
    timestamp = datetime.utcnow()
    
    metrics = [
        {
            'MetricName': 'UsageCount',
            'Value': usage['usage'],
            'Unit': 'Count',
            'Timestamp': timestamp,
            'Dimensions': [
                {'Name': 'UsagePlanId', 'Value': plan_id},
                {'Name': 'UsagePlanName', 'Value': plan_name},
                {'Name': 'ApiKeyId', 'Value': key_id},
                {'Name': 'ApiKeyName', 'Value': key_name}
            ]
        },
        {
            'MetricName': 'QuotaLimit',
            'Value': usage['limit'],
            'Unit': 'Count',
            'Timestamp': timestamp,
            'Dimensions': [
                {'Name': 'UsagePlanId', 'Value': plan_id},
                {'Name': 'UsagePlanName', 'Value': plan_name}
            ]
        },
        {
            'MetricName': 'UsagePercentage',
            'Value': usage['percentage'],
            'Unit': 'Percent',
            'Timestamp': timestamp,
            'Dimensions': [
                {'Name': 'UsagePlanId', 'Value': plan_id},
                {'Name': 'UsagePlanName', 'Value': plan_name},
                {'Name': 'ApiKeyId', 'Value': key_id},
                {'Name': 'ApiKeyName', 'Value': key_name}
            ]
        }
    ]
    
    # メトリクスをバッチで送信
    cloudwatch.put_metric_data(
        Namespace=namespace,
        MetricData=metrics
    )
    
    print(f"Sent metrics for {plan_name}/{key_name}: {usage['usage']}/{usage['limit']} ({usage['percentage']:.2f}%)")
```

### CDKでの実装

```python
# infrastructure/stacks/api_gateway_stack.py に追加

from aws_cdk import (
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
)

# Lambda関数の作成
usage_metrics_lambda = lambda_.Function(
    self, "UsageMetricsLambda",
    runtime=lambda_.Runtime.PYTHON_3_11,
    handler="usage_plan_metrics.lambda_handler",
    code=lambda_.Code.from_asset("lambda"),
    timeout=Duration.minutes(5),
    memory_size=256,
    environment={
        "API_GATEWAY_ID": rest_api.rest_api_id,
    }
)

# 必要な権限を付与
usage_metrics_lambda.add_to_role_policy(iam.PolicyStatement(
    actions=[
        "apigateway:GET",
        "apigateway:GetUsagePlans",
        "apigateway:GetUsagePlanKeys",
        "apigateway:GetUsage",
        "apigateway:GetUsagePlan",
        "cloudwatch:PutMetricData"
    ],
    resources=["*"]
))

# EventBridgeルールの作成（5分ごとに実行）
rule = events.Rule(
    self, "UsageMetricsRule",
    schedule=events.Schedule.rate(Duration.minutes(5))
)

rule.add_target(targets.LambdaFunction(usage_metrics_lambda))
```

## 解決策2: AWS CLIによる手動メトリクス送信

### 使用量データの取得

```bash
#!/bin/bash

# 変数設定
API_GATEWAY_ID="your-api-id"
USAGE_PLAN_ID="your-usage-plan-id"
API_KEY_ID="your-api-key-id"
TODAY=$(date +%Y-%m-%d)

# 使用量を取得
USAGE_DATA=$(aws apigateway get-usage \
    --usage-plan-id $USAGE_PLAN_ID \
    --key-id $API_KEY_ID \
    --start-date $TODAY \
    --end-date $TODAY \
    --region ap-northeast-1)

# 使用量を解析
USAGE_COUNT=$(echo $USAGE_DATA | jq '[.items[][][][]] | add')

# 使用量プランの情報を取得
PLAN_INFO=$(aws apigateway get-usage-plan \
    --usage-plan-id $USAGE_PLAN_ID \
    --region ap-northeast-1)

PLAN_NAME=$(echo $PLAN_INFO | jq -r '.name')
QUOTA_LIMIT=$(echo $PLAN_INFO | jq -r '.quota.limit')

# 使用率を計算
USAGE_PERCENTAGE=$(echo "scale=2; $USAGE_COUNT / $QUOTA_LIMIT * 100" | bc)

echo "Usage Plan: $PLAN_NAME"
echo "Usage: $USAGE_COUNT / $QUOTA_LIMIT ($USAGE_PERCENTAGE%)"
```

### CloudWatchカスタムメトリクスの送信

```bash
#!/bin/bash

# カスタムメトリクスを送信
aws cloudwatch put-metric-data \
    --namespace "Custom/APIGateway" \
    --metric-name "UsageCount" \
    --value $USAGE_COUNT \
    --dimensions \
        UsagePlanId=$USAGE_PLAN_ID \
        UsagePlanName=$PLAN_NAME \
        ApiKeyId=$API_KEY_ID \
    --region ap-northeast-1

aws cloudwatch put-metric-data \
    --namespace "Custom/APIGateway" \
    --metric-name "UsagePercentage" \
    --value $USAGE_PERCENTAGE \
    --dimensions \
        UsagePlanId=$USAGE_PLAN_ID \
        UsagePlanName=$PLAN_NAME \
        ApiKeyId=$API_KEY_ID \
    --region ap-northeast-1

echo "Metrics sent to CloudWatch successfully"
```

## 解決策3: CloudWatchコンソールでの手動設定

### 1. CloudWatchダッシュボードの作成

1. **CloudWatchコンソールを開く**
   - https://console.aws.amazon.com/cloudwatch/
   - リージョン: ap-northeast-1

2. **ダッシュボード作成**
   - 左メニューから「ダッシュボード」を選択
   - 「ダッシュボードの作成」をクリック
   - 名前: `api-gateway-usage-plans`

3. **ウィジェットの追加**

#### 数値ウィジェット（現在の使用量）
```json
{
    "metrics": [
        [ "Custom/APIGateway", "UsageCount", 
          { "stat": "Sum", "label": "開発環境" },
          { "dimensions": { "UsagePlanName": "dit-plan", "ApiKeyName": "dev-api-key" } }
        ],
        [ ".", ".", 
          { "stat": "Sum", "label": "本番環境" },
          { "dimensions": { "UsagePlanName": "dit-plan", "ApiKeyName": "prod-api-key" } }
        ]
    ],
    "period": 300,
    "stat": "Sum",
    "region": "ap-northeast-1",
    "title": "API使用量（現在）"
}
```

#### 折れ線グラフウィジェット（時系列）
```json
{
    "metrics": [
        [ "Custom/APIGateway", "UsagePercentage",
          { "dimensions": { "UsagePlanName": "dit-plan" } }
        ]
    ],
    "period": 300,
    "stat": "Average",
    "region": "ap-northeast-1",
    "title": "使用率の推移（%）",
    "yAxis": {
        "left": {
            "min": 0,
            "max": 100
        }
    }
}
```

### 2. メトリクスフィルターの作成（ログベース）

API GatewayのアクセスログからメトリクスフィルターでカスタムメトリクスPLAを作成：

1. **CloudWatch Logs コンソール**
   - ロググループ: `/aws/apigateway/openai-gw`
   - 「メトリクスフィルター」タブを選択

2. **フィルターパターンの定義**
```
[timestamp, request_id, event_type, api_key_id=*api-key*, ...]
```

3. **メトリクスの割り当て**
   - メトリクス名前空間: `Custom/APIGateway/Logs`
   - メトリクス名: `RequestsByApiKey`
   - メトリクス値: `1`
   - ディメンション:
     - 名前: `ApiKeyId`
     - 値: `$api_key_id`

### 3. CloudWatchアラームの設定

```bash
# 使用率80%超過アラーム
aws cloudwatch put-metric-alarm \
    --alarm-name "api-usage-plan-high-usage" \
    --alarm-description "API使用量プランの使用率が80%を超過" \
    --metric-name UsagePercentage \
    --namespace Custom/APIGateway \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2 \
    --dimensions Name=UsagePlanName,Value=dit-plan
```

## メトリクス設計のベストプラクティス

### 推奨される名前空間とディメンション

```yaml
Namespace: Custom/APIGateway

Dimensions:
  # 必須ディメンション
  - UsagePlanId    # 使用量プランの一意識別子
  - UsagePlanName  # 人間が読める名前（組織名として使用）
  
  # オプションディメンション
  - ApiKeyId       # APIキーの一意識別子
  - ApiKeyName     # APIキーの名前（dev/prod/stg等）
  - Environment    # 環境（development/production）
  - Organization   # 組織名（明示的に設定する場合）

Metrics:
  - UsageCount     # 実際の使用量（Count）
  - QuotaLimit     # クォータ上限（Count）
  - UsagePercentage # 使用率（Percent）
  - ThrottleCount  # スロットリング発生回数（Count）
```

### コスト最適化

1. **メトリクスの送信頻度**
   - 本番環境: 5分ごと
   - 開発環境: 15分ごと
   - コスト: $0.30/月 per メトリクス（最初の10,000メトリクス）

2. **保持期間の設定**
   - 詳細データ: 1週間
   - 集計データ: 3ヶ月
   - 月次サマリー: 1年

3. **ディメンションの最適化**
   - 必要最小限のディメンションを使用
   - 高カーディナリティを避ける

## テストとデバッグ

### Lambda関数のローカルテスト

```python
# test_usage_metrics.py
import json
from lambda.usage_plan_metrics import lambda_handler

# テストイベント
test_event = {}
test_context = {}

# 実行
result = lambda_handler(test_event, test_context)
print(json.dumps(result, indent=2))
```

### CloudWatchメトリクスの確認

```bash
# カスタムメトリクスの一覧取得
aws cloudwatch list-metrics \
    --namespace "Custom/APIGateway" \
    --region ap-northeast-1

# 特定のメトリクスの統計取得
aws cloudwatch get-metric-statistics \
    --namespace "Custom/APIGateway" \
    --metric-name "UsageCount" \
    --dimensions Name=UsagePlanName,Value=dit-plan \
    --start-time 2024-01-15T00:00:00Z \
    --end-time 2024-01-15T23:59:59Z \
    --period 3600 \
    --statistics Sum \
    --region ap-northeast-1
```

## まとめ

API Gatewayの使用量プラン（組織）ごとの分析を実現するには、カスタムソリューションの実装が必要です。以下の方法から選択できます：

1. **自動化重視**: Lambda + EventBridge（推奨）
2. **手動運用**: AWS CLI + シェルスクリプト
3. **ビジュアル重視**: CloudWatchダッシュボード + メトリクスフィルター

実装の優先順位：
1. Lambda関数による自動収集を設定
2. CloudWatchダッシュボードで可視化
3. アラームで異常を検知
4. 定期的なレポート生成

これにより、組織別の使用状況を詳細に追跡し、適切な課金やクォータ管理が可能になります。