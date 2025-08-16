# Secrets Manager統合 TODO

## 現状の課題

現在、OpenAI APIキーが環境変数から直接読み込まれており、以下の箇所で使用されています：

1. **プロキシ統合** (Line 52): `/openai/{proxy+}`
2. **chat/completions** (Line 152): POSTエンドポイント  
3. **models** (Line 140): GETエンドポイント
4. **embeddings** (Line 173): POSTエンドポイント

これらすべてで `os.getenv('OPENAI_API_KEY')` を直接使用しているため、セキュリティリスクがあります。

## 実装オプション

### オプション1: Lambda関数を使用（推奠）

**メリット:**
- Secrets Managerから動的にキーを取得可能
- キーがCloudFormationに露出しない
- キーのローテーションが容易

**実装手順:**
1. Lambda関数を作成（Python）
2. Lambda内でSecrets Managerからキーを取得
3. OpenAI APIにプロキシリクエスト
4. API GatewayからLambda統合を設定

**サンプルコード:**
```python
import json
import boto3
import requests
from aws_lambda_powertools import Logger

logger = Logger()
secrets_client = boto3.client('secretsmanager')

def lambda_handler(event, context):
    # Secrets Managerからキーを取得
    secret_name = os.environ['SECRET_NAME']
    response = secrets_client.get_secret_value(SecretId=secret_name)
    api_key = json.loads(response['SecretString'])['api_key']
    
    # OpenAI APIにリクエスト
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # プロキシリクエスト
    openai_response = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers=headers,
        json=json.loads(event['body'])
    )
    
    return {
        'statusCode': openai_response.status_code,
        'body': openai_response.text,
        'headers': dict(openai_response.headers)
    }
```

### オプション2: プロキシ統合を削除

**メリット:**
- 実装がシンプル
- 必要なエンドポイントのみ公開
- 管理が容易

**実装手順:**
1. プロキシ統合のコードを削除（Line 45-110）
2. 個別エンドポイントのみ使用
3. 各エンドポイントでLambda統合を使用

### オプション3: ステージ変数を使用（簡易対応）

**メリット:**
- 実装が最も簡単
- 既存コードの変更が最小限

**デメリット:**
- キーがCloudFormationに露出する可能性
- 動的な更新が困難

**実装手順:**
1. API Gatewayのステージ変数にキーを設定
2. `${stageVariables.openai_api_key}` で参照

## 推奨実装計画

### Phase 1: Lambda関数の作成
- [ ] Lambda関数用のディレクトリ作成 (`infrastructure/lambda/`)
- [ ] OpenAI プロキシLambda関数の実装
- [ ] Lambda関数のCDKコンストラクト作成

### Phase 2: API Gateway統合の更新
- [ ] プロキシ統合をLambda統合に変更
- [ ] chat/completionsをLambda統合に変更
- [ ] modelsをLambda統合に変更
- [ ] embeddingsをLambda統合に変更

### Phase 3: Secrets Manager設定
- [ ] Secrets Managerにシークレット作成スクリプト
- [ ] IAMロールの権限設定
- [ ] ローテーション設定（オプション）

### Phase 4: テストとドキュメント
- [ ] 各エンドポイントのテスト
- [ ] デプロイ手順のドキュメント更新
- [ ] 環境変数からの移行手順

## 必要なリソース

1. **Lambda関数**
   - ランタイム: Python 3.11
   - メモリ: 256MB
   - タイムアウト: 30秒

2. **IAMロール権限**
   - Secrets Manager読み取り
   - CloudWatch Logs書き込み
   - X-Ray トレース（オプション）

3. **Secrets Manager**
   - シークレット名: `openai-api-key`
   - 形式: `{"api_key": "sk-..."}`

## 注意事項

- プロキシ統合は全パスを転送するため、Secrets Manager統合が困難
- Lambda関数を使用することで、完全にセキュアな実装が可能
- 段階的な移行が推奨（まず個別エンドポイントから）

## 参考リンク

- [AWS CDK API Gateway Lambda Integration](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_apigateway.LambdaIntegration.html)
- [Secrets Manager with Lambda](https://docs.aws.amazon.com/secretsmanager/latest/userguide/retrieving-secrets_lambda.html)
- [API Gateway Stage Variables](https://docs.aws.amazon.com/apigateway/latest/developerguide/stage-variables.html)