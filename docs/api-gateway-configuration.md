# API Gateway 構成ドキュメント

## 概要

このプロジェクトは、AWS CDKを使用して複数のAPIサービス（OpenAI、AWS Bedrock、Firecrawl、Dify）を統合する統一API Gatewayを構築します。

## 現在のデプロイ状況

### API Gateway エンドポイント
- **Base URL**: `https://f1343lyxnd.execute-api.ap-northeast-1.amazonaws.com/prod/`
- **リージョン**: `ap-northeast-1` (東京)
- **ステージ**: `prod`

### APIキー
- **Production API Key ID**: `b8azvrlted`
- **Development API Key ID**: `whjvpdotz9`

## アーキテクチャ構成

```
┌─────────────────────────────────────────────┐
│           Client Application                 │
│                                              │
└──────────────────┬──────────────────────────┘
                   │ x-api-key
                   ▼
┌─────────────────────────────────────────────┐
│         AWS API Gateway (REST API)          │
│                                              │
│  ┌────────────────────────────────────┐     │
│  │    Usage Plan & API Keys           │     │
│  │  - Rate Limit: 1000 req/sec        │     │
│  │  - Burst Limit: 2000               │     │
│  │  - Quota: 10000 req/day            │     │
│  └────────────────────────────────────┘     │
│                                              │
│  ┌────────────────────────────────────┐     │
│  │         CORS Configuration         │     │
│  │  - Origins: *                      │     │
│  │  - Methods: GET,POST,PUT,DELETE    │     │
│  └────────────────────────────────────┘     │
│                                              │
│  ┌────────────────────────────────────┐     │
│  │     CloudWatch Logging & X-Ray     │     │
│  │  - Log Level: INFO                 │     │
│  │  - Data Trace: Enabled             │     │
│  │  - X-Ray Tracing: Enabled          │     │
│  └────────────────────────────────────┘     │
└──────────────────┬──────────────────────────┘
                   │
      ┌────────────┼────────────┬────────────┐
      ▼            ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│  OpenAI  │ │ Bedrock  │ │Firecrawl │ │   Dify   │
│   API    │ │   API    │ │   API    │ │   API    │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

## 有効なAPIエンドポイント

### OpenAI API (✅ デプロイ済み・動作確認済み)

| エンドポイント | メソッド | 説明 |
|------------|---------|------|
| `/openai/models` | GET | 利用可能なモデル一覧を取得 |
| `/openai/chat/completions` | POST | チャット補完を実行 |
| `/openai/embeddings` | POST | テキストの埋め込みベクトルを生成 |
| `/openai/{proxy+}` | ANY | その他のOpenAI APIへのプロキシ |

### その他のAPI (現在無効化中)

- **Bedrock API**: `/bedrock/*` - AWS Bedrock APIへのプロキシ
- **Firecrawl API**: `/firecrawl/*` - Web スクレイピングAPI
- **Dify API**: `/dify/*` - ワークフロー自動化API

## セキュリティ設定

### 認証
- **API Key認証**: すべてのエンドポイントで`x-api-key`ヘッダーが必要
- **使用量制限**: Usage Planによるレート制限とクォータ管理

### 現在の課題
⚠️ **重要**: OpenAI APIキーが現在CloudFormationテンプレートに直接埋め込まれています。

**推奨される改善案**:
1. AWS Secrets ManagerまたはSystems Manager Parameter Storeを使用
2. Lambda Authorizerによる動的なAPIキー注入
3. API Gatewayのステージ変数を使用

## CDKスタック構成

### ディレクトリ構造
```
infrastructure/
├── app.py                          # CDKアプリケーションのエントリーポイント
├── stacks/
│   └── api_gateway_stack.py       # メインのAPI Gatewayスタック
└── cdk_constructs/
    ├── openai_api.py              # OpenAI API統合
    ├── bedrock_api.py             # Bedrock API統合（無効化中）
    ├── firecrawl_api.py           # Firecrawl API統合（無効化中）
    └── dify_api.py                # Dify API統合（無効化中）
```

### 環境変数設定 (.env)
```bash
# AWS CDK設定
CDK_DEFAULT_ACCOUNT=584575096038
CDK_DEFAULT_REGION=ap-northeast-1
STACK_NAME=api-gateway-integration-stack

# API Gateway設定
API_GATEWAY_NAME=multi-api-gateway
API_GATEWAY_STAGE=prod

# OpenAI設定
OPENAI_API_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=YOUR_OPENAI_API_KEY_HERE  # 実際のAPIキー

# Usage Plan設定
USAGE_PLAN_THROTTLE_RATE_LIMIT=1000
USAGE_PLAN_THROTTLE_BURST_LIMIT=2000
USAGE_PLAN_QUOTA_LIMIT=10000
```

## デプロイ手順

```bash
# 1. 仮想環境のセットアップ
cd infrastructure
python -m venv .venv
source .venv/bin/activate

# 2. 依存関係のインストール
pip install -r requirements.txt

# 3. 環境変数の設定
cp .env.example .env
# .envファイルを編集してAPIキーなどを設定

# 4. CDKのデプロイ
cdk deploy
```

## 監視とログ

### CloudWatch Logs
- **ログ保持期間**: 30日
- **ログレベル**: INFO
- **データトレース**: 有効

### メトリクス
- API呼び出し回数
- レイテンシー
- エラー率
- 4xx/5xx レスポンス

## トラブルシューティング

### よくあるエラー

1. **"Invalid mapping expression" エラー**
   - 原因: API Gatewayのマッピング式で無効な構文を使用
   - 解決: `context.authorizer`は使用できないため、直接値を指定

2. **POSTリクエストが失敗する**
   - 原因: HttpIntegrationで`http_method`パラメータが未指定
   - 解決: `http_method="POST"`を明示的に指定

3. **APIキーが無効と表示される**
   - 原因: APIキーの値ではなく変数名が送信されている
   - 解決: 環境変数から実際のAPIキー値を読み込む

## 今後の改善計画

1. **セキュリティ強化**
   - AWS Secrets Managerを使用したAPIキー管理
   - Lambda Authorizerの実装
   - IPホワイトリストの設定

2. **機能拡張**
   - Bedrock、Firecrawl、Dify APIの有効化
   - レスポンスキャッシュの実装
   - カスタムドメインの設定

3. **運用改善**
   - CI/CDパイプラインの構築
   - 自動テストの追加
   - アラート設定の強化