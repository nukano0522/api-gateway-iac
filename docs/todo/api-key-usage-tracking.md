# APIキーごとの使用量追跡システムの実装

## 課題
CloudWatch LogsのcallerフィールドにAPIキーIDが記録されない問題への対応

### 原因
- APIキーは認可（Authorization）の仕組みであり、認証（Authentication）ではない
- `$context.identity.caller`はIAM認証時のみ値が入る仕様
- APIキーの値自体はセキュリティ上の理由でログに記録されない

## 実装タスク

### 短期対応（即座に実施可能）

#### 1. API Gateway Usage APIを使用した定期レポート作成
- [ ] 使用量取得スクリプトの作成
- [ ] cronまたはEventBridgeでの定期実行設定
- [ ] レポート出力先の決定（S3、CloudWatch、メール等）

```python
# 実装例
import boto3
from datetime import datetime

apigateway = boto3.client('apigateway')

def get_api_key_usage():
    usage_plans = apigateway.get_usage_plans()
    for plan in usage_plans['items']:
        keys = apigateway.get_usage_plan_keys(usagePlanId=plan['id'])
        for key in keys['items']:
            usage = apigateway.get_usage(
                usagePlanId=plan['id'],
                keyId=key['id'],
                startDate=datetime.now().strftime('%Y-%m-%d'),
                endDate=datetime.now().strftime('%Y-%m-%d')
            )
            # レポート処理
```

#### 2. 現在可能な分析方法の活用
- [ ] IPアドレスベースの分析クエリ作成
- [ ] 時間帯とパスの相関分析クエリ作成
- [ ] エラー率監視クエリ作成
- [ ] CloudWatchダッシュボード作成

### 中期対応（1-2週間）

#### 3. Lambda Authorizerの実装
- [ ] Lambda Authorizer関数の作成
- [ ] APIキー検証ロジックの実装
- [ ] DynamoDBまたはParameter StoreでのAPIキー管理
- [ ] callerフィールドへのAPIキー名設定
- [ ] 既存のAPI Gatewayへの適用
- [ ] テスト環境での動作確認

```python
# Lambda Authorizer実装例
def lambda_handler(event, context):
    api_key = event['headers'].get('x-api-key')
    if not validate_api_key(api_key):
        raise Exception('Unauthorized')
    
    api_key_name = get_api_key_name(api_key)
    return {
        'principalId': api_key_name,  # callerフィールドに記録される
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': 'Allow',
                'Resource': event['methodArn']
            }]
        },
        'context': {
            'apiKeyName': api_key_name,
            'apiKeyId': api_key[:8] + '****'
        }
    }
```

### 長期対応（1ヶ月以内）

#### 4. CloudWatchカスタムメトリクスの自動収集システム
- [ ] Lambda関数の作成（usage_plan_metrics.py）
- [ ] EventBridgeルールの設定（5分ごと実行）
- [ ] CloudWatchカスタムメトリクスの定義
- [ ] IAMロールとポリシーの設定
- [ ] CDKスタックの作成（monitoring_stack.py）

#### 5. 包括的な監視ダッシュボード
- [ ] 使用量プラン別のメトリクス表示
- [ ] APIキー別の使用状況グラフ
- [ ] クォータ使用率のアラート設定
- [ ] 異常検知の設定

## 追加検討事項

### セキュリティ考慮事項
- [ ] APIキーのローテーション戦略
- [ ] アクセスログの保持期間設定
- [ ] 機密情報のマスキング確認

### コスト最適化
- [ ] CloudWatchメトリクスの送信頻度調整
- [ ] ログの保持期間最適化
- [ ] Lambda関数のメモリサイズ調整

### ドキュメント整備
- [ ] 実装ガイドの作成
- [ ] 運用手順書の作成
- [ ] トラブルシューティングガイドの追加

## 参考資料
- [AWS API Gateway Access Logs Documentation](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-logging.html)
- [API Gateway Usage Plans](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-usage-plans.html)
- [Lambda Authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html)