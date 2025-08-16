# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**重要**: このプロジェクトでは日本語で応答してください。

## Repository Overview

AWS CDK (Python) を使用した API Gateway 統合インフラストラクチャ。OpenAI と Firecrawl の各APIサービスを用途別の独立したAPI Gatewayで管理し、認証、モニタリング、使用量管理を統合します。

## Tech Stack

- **Infrastructure**: AWS CDK v2 (Python 3.8+)
- **依存関係**: `aws-cdk-lib==2.210.0`, `python-dotenv==1.1.1`
- **AWS Services**: API Gateway, CloudWatch, Systems Manager, Secrets Manager
- **API Integrations**: OpenAI Gateway, Firecrawl Gateway

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
cdk diff --all

# 4. CloudFormation テンプレートの生成と検証
cdk synth

# 5. デプロイ実行
cdk deploy --all

# 6. デプロイ完了後、APIキーを取得
aws apigateway get-api-key --api-key <出力されたキーID> --include-value --region ap-northeast-1
```

### API動作確認

```bash
# OpenAI Gateway エンドポイントのテスト
export OPENAI_ENDPOINT="<OpenAI Gateway URL>"
export API_KEY="<取得したAPIキー>"

curl -X GET "${OPENAI_ENDPOINT}/models" \
  -H "x-api-key: ${API_KEY}" \
  -H "Accept: application/json"

# Firecrawl Gateway エンドポイントのテスト
export FIRECRAWL_ENDPOINT="<Firecrawl Gateway URL>"

curl -X POST "${FIRECRAWL_ENDPOINT}/scrape" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","formats":["markdown"]}'
```

## Project Structure

```
infrastructure/
├── .env                           # 環境変数 (gitignore)
├── .env.example                   # 環境変数テンプレート
├── .venv/                         # Python仮想環境 (gitignore)
├── app.py                         # CDKアプリケーションエントリポイント
├── cdk.json                       # CDK設定 (app: "python3 app.py")
├── requirements.txt               # Python依存関係
├── cdk_constructs/                # 各APIサービスのコンストラクト
│   ├── openai_api.py             # OpenAI統合
│   └── firecrawl_api.py          # Firecrawl統合
└── stacks/
    ├── openai_gateway_stack.py   # OpenAI専用Gatewayスタック
    ├── firecrawl_gateway_stack.py # Firecrawl専用Gatewayスタック
    └── usage_plan_stack.py        # 統合使用量プランスタック
```

## 重要な実装詳細

### アーキテクチャ

- **用途別Gateway**: OpenAI と Firecrawl それぞれに独立したAPI Gatewayを構築
- **統合使用量管理**: 共通の Usage Plan Stack で両Gatewayの使用量を統合管理
- **スタック依存関係**: Usage Plan Stack は両Gateway Stackに依存

### OpenAI API キーの扱い

現在の実装では `os.getenv('OPENAI_API_KEY')` を直接使用 (openai_api.py:33行目)。
本番環境では AWS Secrets Manager または Systems Manager Parameter Store の使用を推奨。

### Firecrawl API キーの扱い

同様に `os.getenv('FIRECRAWL_API_KEY')` を使用。
本番環境では適切なシークレット管理サービスへの移行を推奨。

## トラブルシューティング

### デプロイエラーの対処

```bash
# CloudFormation イベントの確認
aws cloudformation describe-stack-events \
  --stack-name <stack-name> \
  --region ap-northeast-1 \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'

# CDKコンテキストのクリア
cdk context --clear

# 詳細ログでデプロイ
cdk deploy --all --verbose --require-approval never
```

### APIキー認証エラー (403 Forbidden)

```bash
# APIキーの状態確認
aws apigateway get-api-keys --region ap-northeast-1

# 使用量プランの確認
aws apigateway get-usage-plans --region ap-northeast-1

# 使用量プランとステージの関連確認
aws apigateway get-usage-plan-keys --usage-plan-id <plan-id> --region ap-northeast-1
```

### CloudWatch ログの確認

```bash
# OpenAI Gateway ログ
aws logs describe-log-streams \
  --log-group-name "/aws/apigateway/openai-gateway" \
  --order-by LastEventTime \
  --descending \
  --limit 5

# Firecrawl Gateway ログ
aws logs describe-log-streams \
  --log-group-name "/aws/apigateway/firecrawl-gateway" \
  --order-by LastEventTime \
  --descending \
  --limit 5
```

## 環境変数の詳細

`.env.example` ファイルの主要設定:

- **CDK設定**: `CDK_DEFAULT_ACCOUNT`, `CDK_DEFAULT_REGION`
- **OpenAI Gateway設定**: `OPENAI_GATEWAY_NAME`, `OPENAI_API_KEY`
- **Firecrawl Gateway設定**: `FIRECRAWL_GATEWAY_NAME`, `FIRECRAWL_API_KEY`
- **使用量プラン**: レート制限、バースト、クォータ設定
- **監視**: CloudWatch Logs, X-Ray トレーシング有効
- **CORS**: 各Gateway個別に設定可能

## スタック削除

```bash
# 全スタックの削除（依存関係順）
cdk destroy --all

# 個別削除（依存関係に注意）
cdk destroy UsagePlanStack
cdk destroy FirecrawlGatewayStack
cdk destroy OpenAIGatewayStack

# 削除確認
aws cloudformation list-stacks \
  --stack-status-filter DELETE_COMPLETE \
  --region ap-northeast-1
```