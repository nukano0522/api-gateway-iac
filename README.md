# API Gateway Integration Infrastructure

Amazon API Gatewayを使用して複数のAPIサービスを統合管理するためのCDKインフラストラクチャです。

## 概要

このプロジェクトは、以下のAPIサービスを統合管理します：
- OpenAI API
- AWS Bedrock API
- Firecrawl API
- Dify API

各APIエンドポイントを用途や利用者ごとにグルーピングし、コストやリクエスト数を一元管理できます。

## 機能

- **統一エンドポイント**: 全てのAPIサービスを単一のAPI Gatewayエンドポイントから利用可能
- **使用量管理**: APIキーと使用量プランによるアクセス制御とレート制限
- **コスト追跡**: CloudWatchメトリクスによる詳細な使用状況の監視
- **セキュリティ**: APIキー認証とCORS設定
- **ログ記録**: CloudWatch Logsによる包括的なロギング
- **拡張性**: 新しいAPIサービスの追加が容易

## プロジェクト構造

```
api-gateway-iac/
├── .env.example                     # 環境変数テンプレート
├── README.md                        # このファイル
└── infrastructure/                  # CDKインフラコード
    ├── app.py                      # CDKアプリケーションエントリーポイント
    ├── cdk.json                    # CDK設定ファイル
    ├── requirements.txt            # Python依存関係
    ├── stacks/                     # CDKスタック
    │   └── api_gateway_stack.py   # メインAPI Gatewayスタック
    └── constructs/                 # CDKコンストラクト
        ├── openai_api.py          # OpenAI API統合
        ├── bedrock_api.py         # Bedrock API統合
        ├── firecrawl_api.py       # Firecrawl API統合
        └── dify_api.py            # Dify API統合
```

## 前提条件

- Python 3.8以上
- AWS CLI設定済み
- AWS CDK CLI (`npm install -g aws-cdk`)
- 各APIサービスのAPIキー

## セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd api-gateway-iac
```

### 2. Python仮想環境のセットアップ

```bash
cd infrastructure
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 環境変数の設定

```bash
cp .env.example .env
# .envファイルを編集して実際の値を設定
```

主要な環境変数：
- `CDK_DEFAULT_ACCOUNT`: AWSアカウントID
- `CDK_DEFAULT_REGION`: デプロイリージョン（デフォルト: ap-northeast-1）
- `STACK_NAME`: CloudFormationスタック名
- `API_GATEWAY_NAME`: API Gateway名
- 各APIサービスのベースURLとAPIキー名

### 4. CDKブートストラップ（初回のみ）

```bash
cdk bootstrap
```

## デプロイ

### CDKスタックのデプロイ

```bash
cd infrastructure
cdk deploy
```

デプロイ後、以下の情報が出力されます：
- API GatewayエンドポイントURL
- API Gateway REST API ID
- 開発用APIキーID
- 本番用APIキーID

### スタックの削除

```bash
cdk destroy
```

## 使用方法

### APIエンドポイント

デプロイ後、以下のエンドポイントが利用可能になります：

#### OpenAI API
- `POST /openai/chat/completions` - ChatGPT補完
- `GET /openai/models` - モデル一覧
- `POST /openai/embeddings` - テキスト埋め込み
- `ANY /openai/{proxy}` - その他のOpenAI APIエンドポイント

#### Bedrock API
- `GET /bedrock/models` - モデル一覧
- `POST /bedrock/invoke/{model}` - モデル実行
- `POST /bedrock/invoke-stream/{model}` - ストリーミング実行
- `POST /bedrock/claude/messages` - Claude専用エンドポイント

#### Firecrawl API
- `POST /firecrawl/scrape` - Webスクレイピング
- `POST /firecrawl/crawl` - Webクローリング
- `GET /firecrawl/crawl/status/{jobId}` - クロールステータス確認
- `POST /firecrawl/search` - Web検索
- `ANY /firecrawl/{proxy}` - その他のFirecrawlエンドポイント

#### Dify API
- `POST /dify/chat-messages` - チャットメッセージ
- `POST /dify/completion-messages` - 補完メッセージ
- `POST /dify/workflows/run` - ワークフロー実行
- `GET /dify/conversations` - 会話履歴
- `GET /dify/messages` - メッセージ取得
- `POST /dify/messages/{message_id}/feedbacks` - フィードバック送信
- `ANY /dify/{proxy}` - その他のDifyエンドポイント

### APIキーの取得

APIキーは AWS Systems Manager Parameter Store または AWS Secrets Manager から取得します：

```bash
# 開発用APIキーの取得
aws apigateway get-api-key --api-key <dev-api-key-id> --include-value

# 本番用APIキーの取得
aws apigateway get-api-key --api-key <prod-api-key-id> --include-value
```

### リクエスト例

```bash
# OpenAI ChatGPT APIの呼び出し
curl -X POST https://<api-gateway-url>/openai/chat/completions \
  -H "x-api-key: <your-api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Bedrock Claude APIの呼び出し
curl -X POST https://<api-gateway-url>/bedrock/claude/messages \
  -H "x-api-key: <your-api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## モニタリング

### CloudWatch Logs

全てのAPIリクエストは CloudWatch Logs に記録されます。ログは以下の場所で確認できます：
- ログループ: `/aws/apigateway/<api-gateway-name>`
- 保持期間: デフォルト30日（環境変数で設定可能）

### CloudWatch Metrics

以下のメトリクスが自動的に収集されます：
- リクエスト数
- エラー率
- レイテンシー
- 4xxエラー
- 5xxエラー

### 使用量レポート

API使用量は使用量プランごとに追跡され、以下の情報が取得できます：
- 日次/月次のリクエスト数
- APIキーごとの使用状況
- スロットリング情報

## カスタマイズ

### 新しいAPIサービスの追加

1. `infrastructure/constructs/`に新しいコンストラクトファイルを作成
2. `infrastructure/stacks/api_gateway_stack.py`で新しいコンストラクトをインポートして使用
3. `.env.example`に必要な環境変数を追加
4. CDKスタックを再デプロイ

### 使用量プランの変更

`.env`ファイルで以下の設定を変更：
- `USAGE_PLAN_THROTTLE_RATE_LIMIT`: 秒あたりのリクエスト数制限
- `USAGE_PLAN_THROTTLE_BURST_LIMIT`: バーストリクエスト数制限
- `USAGE_PLAN_QUOTA_LIMIT`: 期間あたりのリクエスト数制限
- `USAGE_PLAN_QUOTA_PERIOD`: クォータ期間（DAY/WEEK/MONTH）

## トラブルシューティング

### デプロイエラー

```bash
# CDKの差分確認
cdk diff

# 詳細ログでデプロイ
cdk deploy --verbose
```

### APIキーが機能しない

1. APIキーが使用量プランに関連付けられているか確認
2. APIキーが有効になっているか確認
3. x-api-keyヘッダーが正しく設定されているか確認

### CORS エラー

`.env`ファイルのCORS設定を確認：
- `CORS_ALLOW_ORIGINS`
- `CORS_ALLOW_HEADERS`
- `CORS_ALLOW_METHODS`

## セキュリティ考慮事項

- APIキーは環境変数やSecrets Managerで管理
- 本番環境では具体的なオリジンを指定してCORSを設定
- CloudTrailでAPI管理操作を監査
- WAFの導入を検討

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## サポート

問題や質問がある場合は、GitHubのIssueを作成してください。