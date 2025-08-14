# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**重要**: このプロジェクトでは日本語で応答してください。

## Repository Overview

AWS CDK (Python) を使用した API Gateway 統合インフラストラクチャ。OpenAI、AWS Bedrock、Firecrawl、Dify の各APIサービスを単一のAPI Gatewayで統合管理し、認証、モニタリング、使用量管理を一元化します。

## Tech Stack

- **Infrastructure**: AWS CDK v2 (Python 3.8+)
- **依存関係**: `aws-cdk-lib==2.210.0`, `python-dotenv==1.1.1`
- **AWS Services**: API Gateway, CloudWatch, Systems Manager, Secrets Manager
- **API Integrations**: OpenAI (有効), Bedrock/Firecrawl/Dify (コメントアウト中)

## Essential Commands

### 開発環境のセットアップ (初回のみ)

```bash
cd infrastructure
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .envファイルを編集して実際の値を設定
```

### CDK デプロイワークフロー

```bash
# 1. 環境変数の確認
source .venv/bin/activate
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(f'Account: {os.getenv(\"CDK_DEFAULT_ACCOUNT\")}')"

# 2. CDK Bootstrap (初回のみ)
cdk bootstrap

# 3. 変更内容の確認
cdk diff

# 4. CloudFormation テンプレートの生成と検証
cdk synth

# 5. デプロイ実行
cdk deploy

# 6. デプロイ完了後、APIキーを取得
aws apigateway get-api-key --api-key <出力されたキーID> --include-value --region ap-northeast-1
```

### API動作確認

```bash
# 環境変数設定
export API_ENDPOINT="<CDKデプロイ後に出力されるURL>"
export API_KEY="<取得したAPIキー>"

# OpenAI models エンドポイントのテスト
curl -X GET "${API_ENDPOINT}/openai/models" \
  -H "x-api-key: ${API_KEY}" \
  -H "Accept: application/json"

# Chat completion テスト
curl -X POST "${API_ENDPOINT}/openai/chat/completions" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"Hello"}],"max_tokens":50}'
```

## Project Structure

```
infrastructure/
├── .env                      # 環境変数 (gitignore)
├── .env.example              # 環境変数テンプレート
├── .venv/                    # Python仮想環境 (gitignore)
├── app.py                    # CDKアプリケーションエントリポイント
├── cdk.json                  # CDK設定 (app: "python3 app.py")
├── requirements.txt          # Python依存関係
├── cdk_constructs/           # 各APIサービスのコンストラクト (注: フォルダ名は cdk_constructs)
│   ├── openai_api.py        # OpenAI統合 (有効)
│   ├── bedrock_api.py       # Bedrock統合 (コメントアウト中)
│   ├── firecrawl_api.py     # Firecrawl統合 (コメントアウト中)
│   └── dify_api.py          # Dify統合 (コメントアウト中)
└── stacks/
    └── api_gateway_stack.py # メインスタック
```

## 重要な実装詳細

### 現在の制限事項

- **OpenAI APIのみ有効**: `stacks/api_gateway_stack.py` の93-96行目で OpenAI のみインスタンス化
- 他のAPI (Bedrock, Firecrawl, Dify) はコメントアウト状態 (13-15行目, 99行目以降)

### コメントアウトされたAPIの有効化

```python
# stacks/api_gateway_stack.py での変更例:

# 1. importのコメントアウトを解除 (13-15行目)
from cdk_constructs.bedrock_api import BedrockApiConstruct

# 2. コンストラクトのインスタンス化 (99行目以降)
bedrock_construct = BedrockApiConstruct(
    self, "BedrockApi",
    api=rest_api,
    api_key_required=api_key_required
)
```

### OpenAI API キーの扱い

現在の実装では `os.getenv('OPENAI_API_KEY')` を直接使用 (openai_api.py:33行目)。
本番環境では AWS Secrets Manager または Systems Manager Parameter Store の使用を推奨。

## トラブルシューティング

### デプロイエラーの対処

```bash
# CloudFormation イベントの確認
aws cloudformation describe-stack-events \
  --stack-name api-gateway-integration-stack \
  --region ap-northeast-1 \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'

# CDKコンテキストのクリア
cdk context --clear

# 詳細ログでデプロイ
cdk deploy --verbose --require-approval never
```

### APIキー認証エラー (403 Forbidden)

```bash
# APIキーの状態確認
aws apigateway get-api-keys --region ap-northeast-1

# 使用量プランの確認
aws apigateway get-usage-plans --region ap-northeast-1
```

### CloudWatch ログの確認

```bash
# ログストリーム一覧
aws logs describe-log-streams \
  --log-group-name "/aws/apigateway/${API_GATEWAY_NAME}" \
  --order-by LastEventTime \
  --descending \
  --limit 5

# 最新のログ確認
aws logs filter-log-events \
  --log-group-name "/aws/apigateway/${API_GATEWAY_NAME}" \
  --start-time $(date -u -d '10 minutes ago' +%s)000
```

## 環境変数の詳細

`.env.example` ファイルの主要設定:

- **CDK設定**: `CDK_DEFAULT_ACCOUNT`, `CDK_DEFAULT_REGION`
- **API Gateway**: `API_GATEWAY_NAME`, `API_GATEWAY_STAGE`
- **使用量プラン**: レート制限 (1000 req/s)、バースト (2000)、日次クォータ (10000)
- **監視**: CloudWatch Logs, X-Ray トレーシング有効
- **CORS**: デフォルトで全オリジン許可 (本番では要変更)

## スタック削除

```bash
# リソースの完全削除
cdk destroy --force

# 削除確認
aws cloudformation describe-stacks \
  --stack-name api-gateway-integration-stack \
  --region ap-northeast-1
```
