# API使用量レポートスクリプト

API GatewayのAPIキーごとの使用量を集計し、レポートを生成するスクリプトです。

## 機能

- 使用量プラン（Basic, Developer）ごとの集計
- APIキーごとの詳細な使用状況
- クォータに対する使用率の計算
- 複数の出力形式（コンソール、JSON、CSV）
- CloudWatchカスタムメトリクスへの送信
- 高使用率の警告表示

## セットアップ

### 1. 依存パッケージのインストール

```bash
cd scripts
pip install -r requirements.txt
```

### 2. AWS認証の設定

以下のいずれかの方法でAWS認証を設定してください：

- AWS CLIの設定: `aws configure`
- 環境変数: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- IAMロール（EC2/Lambda実行時）

## 使用方法

### 基本的な使用（今日の使用量を表示）

```bash
python api_usage_report.py
```

### 日付範囲を指定

```bash
# 特定の日の使用量
python api_usage_report.py --start-date 2025-01-15

# 期間を指定
python api_usage_report.py --start-date 2025-01-01 --end-date 2025-01-15
```

### 出力形式の指定

```bash
# JSON形式で保存
python api_usage_report.py --output json

# CSV形式で保存
python api_usage_report.py --output csv

# すべての形式で出力
python api_usage_report.py --output all
```

### CloudWatchメトリクス送信

```bash
python api_usage_report.py --cloudwatch
```

### デバッグモード

```bash
python api_usage_report.py --debug
```

## 出力例

### コンソール出力

```
====================================================================================================
API Gateway 使用量レポート
====================================================================================================
期間: 2025-01-16 〜 2025-01-16

【使用量プラン: basic】
--------------------------------------------------------------------------------
APIキー名                      使用量     クォータ   使用率   レート制限
--------------------------------------------------------------------------------
basic-dev-key                      250      1,000   25.0%        100/秒
basic-prod-key                     750      1,000   75.0%        100/秒
--------------------------------------------------------------------------------
小計                             1,000

【使用量プラン: developer】
--------------------------------------------------------------------------------
APIキー名                      使用量     クォータ   使用率   レート制限
--------------------------------------------------------------------------------
developer-dev-key                5,000    100,000    5.0%      1,000/秒
developer-prod-key              85,000    100,000   85.0%      1,000/秒
--------------------------------------------------------------------------------
小計                            90,000

================================================================================
総計                            91,000 リクエスト

⚠️  警告: 使用率が80%を超えているAPIキー
  - developer-prod-key: 85.0%
```

### JSON出力

レポートは`reports/api_usage_YYYYMMDD_HHMMSS.json`として保存されます：

```json
[
  {
    "usage_plan_id": "abc123",
    "usage_plan_name": "basic",
    "api_key_id": "key123",
    "api_key_name": "basic-dev-key",
    "usage_count": 250,
    "quota_limit": 1000,
    "usage_percentage": 25.0,
    "throttle_rate": 100,
    "throttle_burst": 200,
    "period_start": "2025-01-16",
    "period_end": "2025-01-16"
  }
]
```

### CSV出力

レポートは`reports/api_usage_YYYYMMDD_HHMMSS.csv`として保存されます。

## 定期実行の設定

### cronでの日次実行

```bash
# crontabに追加（毎日午前1時に実行）
0 1 * * * cd /path/to/api-gateway-iac/scripts && python api_usage_report.py --output all --cloudwatch
```

### シェルスクリプトでの実行

```bash
#!/bin/bash
# daily_report.sh

cd /path/to/api-gateway-iac/scripts

# 昨日の使用量レポート
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)
python api_usage_report.py \
  --start-date $YESTERDAY \
  --output all \
  --cloudwatch

# 週次レポート（月曜日に実行）
if [ $(date +%u) -eq 1 ]; then
  LAST_WEEK_START=$(date -d "last monday" +%Y-%m-%d)
  LAST_WEEK_END=$(date -d "last sunday" +%Y-%m-%d)
  python api_usage_report.py \
    --start-date $LAST_WEEK_START \
    --end-date $LAST_WEEK_END \
    --output all
fi
```

## CloudWatchダッシュボード

CloudWatchメトリクスを送信すると、以下のカスタムメトリクスが利用可能になります：

- **Namespace**: `Custom/APIGateway`
- **メトリクス**:
  - `UsageCount`: 使用量（リクエスト数）
  - `UsagePercentage`: クォータに対する使用率（%）
- **ディメンション**:
  - `UsagePlanName`: 使用量プラン名
  - `ApiKeyName`: APIキー名

## トラブルシューティング

### 権限エラー

必要なIAM権限：
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "apigateway:GET",
        "apigateway:GetUsagePlans",
        "apigateway:GetUsagePlanKeys",
        "apigateway:GetUsage",
        "apigateway:GetApiKey",
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*"
    }
  ]
}
```

### データが取得できない場合

1. APIキーが使用量プランに関連付けられているか確認
2. 指定した日付にリクエストがあったか確認
3. リージョンが正しいか確認（デフォルト: ap-northeast-1）

### デバッグ

```bash
# デバッグログを有効にして実行
python api_usage_report.py --debug
```

## 今後の拡張予定

- [ ] Lambda関数としてのデプロイ対応
- [ ] メール送信機能
- [ ] Slack/Teams通知
- [ ] 前日比・前週比の変化率表示
- [ ] コスト計算機能
- [ ] グラフ生成機能