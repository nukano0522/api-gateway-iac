# API Gateway Integration Infrastructure

Amazon API Gatewayを使用して複数のAPIサービスを用途別に管理するためのCDKインフラストラクチャです。

## 概要

このプロジェクトは、用途別に分離された複数のAPI Gatewayを構築・管理します：
- **OpenAI Gateway**: OpenAI APIサービス専用
- **Firecrawl Gateway**: Firecrawl APIサービス専用

各APIゲートウェイは独立してデプロイ・管理され、共通の使用量プランで統合管理されます。

## 機能

- **用途別エンドポイント**: 各APIサービスごとに独立したGatewayエンドポイント
- **統合使用量管理**: 複数のGatewayにまたがる統一された使用量プランとAPIキー管理
- **コスト追跡**: CloudWatchメトリクスによる詳細な使用状況の監視
- **セキュリティ**: APIキー認証とCORS設定
- **ログ記録**: CloudWatch Logsによる包括的なロギング
- **拡張性**: 新しいAPIサービスGatewayの追加が容易

## プロジェクト構造

```
api-gateway-iac/
├── .env.example                     # 環境変数テンプレート
├── README.md                        # このファイル
├── CLAUDE.md                        # Claude Code用の指示ファイル
└── infrastructure/                  # CDKインフラコード
    ├── app.py                      # CDKアプリケーションエントリーポイント
    ├── cdk.json                    # CDK設定ファイル
    ├── requirements.txt            # Python依存関係
    ├── stacks/                     # CDKスタック
    │   ├── openai_gateway_stack.py    # OpenAI専用Gatewayスタック
    │   ├── firecrawl_gateway_stack.py # Firecrawl専用Gatewayスタック
    │   └── usage_plan_stack.py        # 統合使用量プランスタック
    └── cdk_constructs/             # CDKコンストラクト
        ├── openai_api.py          # OpenAI API統合
        └── firecrawl_api.py       # Firecrawl API統合
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
- OpenAI Gateway設定:
  - `OPENAI_GATEWAY_NAME`: OpenAI Gateway名
  - `OPENAI_API_KEY`: OpenAI APIキー
- Firecrawl Gateway設定:
  - `FIRECRAWL_GATEWAY_NAME`: Firecrawl Gateway名
  - `FIRECRAWL_API_KEY`: Firecrawl APIキー
- 使用量プラン設定

### 4. CDKブートストラップ（初回のみ）

```bash
cdk bootstrap
```

## デプロイ

### CDKスタックのデプロイ

```bash
cd infrastructure
cdk deploy --all
```

デプロイは以下の順序で実行されます：
1. OpenAI Gateway Stack
2. Firecrawl Gateway Stack
3. Usage Plan Stack（前の2つに依存）

デプロイ後、以下の情報が出力されます：
- 各API GatewayエンドポイントURL
- API Gateway REST API ID
- APIキーID

### 個別スタックのデプロイ

```bash
# OpenAI Gatewayのみ
cdk deploy OpenAIGatewayStack

# Firecrawl Gatewayのみ
cdk deploy FirecrawlGatewayStack

# 使用量プランのみ（他のスタックに依存）
cdk deploy UsagePlanStack
```

### スタックの削除

```bash
# 全スタックの削除
cdk destroy --all

# 個別スタックの削除（依存関係に注意）
cdk destroy UsagePlanStack
cdk destroy FirecrawlGatewayStack
cdk destroy OpenAIGatewayStack
```

## 使用方法

### APIエンドポイント

#### OpenAI Gateway
- エンドポイント: `https://<openai-api-id>.execute-api.<region>.amazonaws.com/openai/`
- 利用可能なパス:
  - `POST /chat/completions` - ChatGPT補完
  - `GET /models` - モデル一覧
  - `POST /embeddings` - テキスト埋め込み
  - `ANY /{proxy}` - その他のOpenAI APIエンドポイント

#### Firecrawl Gateway
- エンドポイント: `https://<firecrawl-api-id>.execute-api.<region>.amazonaws.com/firecrawl/`
- 利用可能なパス:
  - `POST /scrape` - Webスクレイピング
  - `POST /crawl` - Webクローリング
  - `GET /crawl/status/{jobId}` - クロールステータス確認
  - `POST /search` - Web検索
  - `ANY /{proxy}` - その他のFirecrawlエンドポイント

### APIキーの取得

APIキーは AWS APIGateway から取得します：

```bash
# APIキーの取得（キーIDはCDKデプロイ時に出力）
aws apigateway get-api-key --api-key <key-id> --include-value --region ap-northeast-1
```

### リクエスト例

```bash
# OpenAI ChatGPT APIの呼び出し
curl -X POST https://<openai-api-id>.execute-api.ap-northeast-1.amazonaws.com/openai/chat/completions \
  -H "x-api-key: <your-api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Firecrawl スクレイピングAPIの呼び出し
curl -X POST https://<firecrawl-api-id>.execute-api.ap-northeast-1.amazonaws.com/firecrawl/scrape \
  -H "x-api-key: <your-api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "formats": ["markdown"],
    "onlyMainContent": true
  }'
```

## モニタリング

### CloudWatch Logs

各API Gatewayのログは個別のロググループに記録されます：
- OpenAI: `/aws/apigateway/openai-gateway`
- Firecrawl: `/aws/apigateway/firecrawl-gateway`
- 保持期間: デフォルト30日（環境変数で設定可能）

### CloudWatch Metrics

以下のメトリクスが各Gatewayごとに収集されます：
- リクエスト数
- エラー率
- レイテンシー
- 4xxエラー
- 5xxエラー

### 使用量レポート

統合使用量プランにより、全Gatewayの使用状況を一元管理：
- 日次/月次のリクエスト数
- APIキーごとの使用状況
- Gateway別の使用状況
- スロットリング情報

## カスタマイズ

### 新しいAPIサービスGatewayの追加

1. `infrastructure/stacks/`に新しいGatewayスタックファイルを作成
2. `infrastructure/cdk_constructs/`に対応するコンストラクトを作成
3. `infrastructure/app.py`で新しいスタックをインスタンス化
4. `infrastructure/stacks/usage_plan_stack.py`に新しいGatewayを追加
5. `.env.example`に必要な環境変数を追加
6. CDKスタックを再デプロイ

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
cdk diff --all

# 詳細ログでデプロイ
cdk deploy --all --verbose

# 特定スタックのみ確認
cdk diff OpenAIGatewayStack
```

### APIキーが機能しない

1. APIキーが使用量プランに関連付けられているか確認
2. APIキーが有効になっているか確認
3. x-api-keyヘッダーが正しく設定されているか確認
4. 使用量プランが各Gatewayステージに関連付けられているか確認

### CORS エラー

`.env`ファイルの各Gateway用CORS設定を確認：
- `OPENAI_CORS_ALLOW_ORIGINS`
- `FIRECRAWL_CORS_ALLOW_ORIGINS`
- その他のCORS関連設定

## セキュリティ考慮事項

- APIキーは環境変数やSecrets Managerで管理
- 本番環境では具体的なオリジンを指定してCORSを設定
- CloudTrailでAPI管理操作を監査
- 各Gatewayで独立したアクセス制御
- WAFの導入を検討

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## サポート

問題や質問がある場合は、GitHubのIssueを作成してください。