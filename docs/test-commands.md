# API Gateway テストコマンド集

## 環境情報

```bash
# API Gateway エンドポイント
API_ENDPOINT="https://f1343lyxnd.execute-api.ap-northeast-1.amazonaws.com/prod"

# APIキー (Production)
API_KEY="YOUR_API_KEY_HERE"

# APIキーの取得方法（AWS CLIを使用）
aws apigateway get-api-key --api-key b8azvrlted --include-value --region ap-northeast-1 --query 'value' --output text
```

## OpenAI API テストコマンド

### 1. モデル一覧の取得 (GET /openai/models)

```bash
# 基本的なリクエスト
curl -X GET "${API_ENDPOINT}/openai/models" \
  -H "x-api-key: ${API_KEY}" \
  -H "Accept: application/json"

# 整形された出力（jqを使用）
curl -X GET "${API_ENDPOINT}/openai/models" \
  -H "x-api-key: ${API_KEY}" \
  -H "Accept: application/json" | jq '.'

# 最初の3つのモデルIDのみを表示
curl -X GET "${API_ENDPOINT}/openai/models" \
  -H "x-api-key: ${API_KEY}" \
  -H "Accept: application/json" | jq -r '.data[0:3] | map(.id)'

# GPTモデルのみをフィルタリング
curl -X GET "${API_ENDPOINT}/openai/models" \
  -H "x-api-key: ${API_KEY}" \
  -H "Accept: application/json" | jq '.data[] | select(.id | contains("gpt"))'
```

### 2. チャット補完 (POST /openai/chat/completions)

#### 基本的なチャット補完

```bash
# シンプルな質問
curl -X POST "${API_ENDPOINT}/openai/chat/completions" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "max_tokens": 50
  }'

# 日本語での応答
curl -X POST "${API_ENDPOINT}/openai/chat/completions" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "日本語で挨拶してください"}
    ],
    "max_tokens": 100
  }'

# レスポンスのテキストのみを抽出
curl -X POST "${API_ENDPOINT}/openai/chat/completions" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "What is the capital of Japan?"}
    ],
    "max_tokens": 50
  }' | jq -r '.choices[0].message.content'
```

#### システムメッセージ付きチャット

```bash
curl -X POST "${API_ENDPOINT}/openai/chat/completions" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant that speaks like a pirate."},
      {"role": "user", "content": "Tell me about programming"}
    ],
    "max_tokens": 150,
    "temperature": 0.7
  }'
```

#### 会話の継続

```bash
curl -X POST "${API_ENDPOINT}/openai/chat/completions" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "My name is Alice"},
      {"role": "assistant", "content": "Nice to meet you, Alice! How can I help you today?"},
      {"role": "user", "content": "What is my name?"}
    ],
    "max_tokens": 50
  }'
```

### 3. テキスト埋め込み (POST /openai/embeddings)

```bash
# 単一テキストの埋め込み
curl -X POST "${API_ENDPOINT}/openai/embeddings" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "text-embedding-ada-002",
    "input": "Hello world"
  }'

# 複数テキストの埋め込み
curl -X POST "${API_ENDPOINT}/openai/embeddings" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "text-embedding-ada-002",
    "input": ["Hello world", "Goodbye world"]
  }'

# 埋め込みベクトルの次元数を確認
curl -X POST "${API_ENDPOINT}/openai/embeddings" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "text-embedding-ada-002",
    "input": "Test"
  }' | jq '.data[0].embedding | length'
```

### 4. プロキシエンドポイント (ANY /openai/{proxy+})

```bash
# モデルの詳細情報を取得
curl -X GET "${API_ENDPOINT}/openai/models/gpt-3.5-turbo" \
  -H "x-api-key: ${API_KEY}" \
  -H "Accept: application/json"
```

## エラーハンドリングのテスト

### 401 Unauthorized (APIキーなし)

```bash
curl -X GET "${API_ENDPOINT}/openai/models" \
  -H "Accept: application/json" \
  -w "\nHTTP Status: %{http_code}\n"
```

### 400 Bad Request (不正なリクエストボディ)

```bash
curl -X POST "${API_ENDPOINT}/openai/chat/completions" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "invalid_field": "test"
  }' \
  -w "\nHTTP Status: %{http_code}\n"
```

### レート制限のテスト

```bash
# 連続リクエストを送信してレート制限を確認
for i in {1..10}; do
  echo "Request $i:"
  curl -X GET "${API_ENDPOINT}/openai/models" \
    -H "x-api-key: ${API_KEY}" \
    -H "Accept: application/json" \
    -w "HTTP Status: %{http_code}, Time: %{time_total}s\n" \
    -o /dev/null -s
  sleep 0.1
done
```

## パフォーマンステスト

### レスポンス時間の測定

```bash
# 詳細な時間測定
curl -X GET "${API_ENDPOINT}/openai/models" \
  -H "x-api-key: ${API_KEY}" \
  -H "Accept: application/json" \
  -w "\n\nPerformance Metrics:\n  DNS Lookup: %{time_namelookup}s\n  TCP Connect: %{time_connect}s\n  SSL Handshake: %{time_appconnect}s\n  Time to First Byte: %{time_starttransfer}s\n  Total Time: %{time_total}s\n" \
  -o /dev/null -s
```

### 並行リクエスト

```bash
# 5つの並行リクエスト
for i in {1..5}; do
  (curl -X GET "${API_ENDPOINT}/openai/models" \
    -H "x-api-key: ${API_KEY}" \
    -H "Accept: application/json" \
    -w "Request $i completed in %{time_total}s\n" \
    -o /dev/null -s) &
done
wait
```

## デバッグ用コマンド

### 詳細なヘッダー情報を表示

```bash
# リクエストとレスポンスのヘッダーを表示
curl -v -X GET "${API_ENDPOINT}/openai/models" \
  -H "x-api-key: ${API_KEY}" \
  -H "Accept: application/json" 2>&1 | grep -E "^[<>]"
```

### レスポンスヘッダーのみを表示

```bash
curl -I -X GET "${API_ENDPOINT}/openai/models" \
  -H "x-api-key: ${API_KEY}" \
  -H "Accept: application/json"
```

### CloudWatch ログの確認（AWS CLI）

```bash
# 最新のログストリームを取得
aws logs describe-log-streams \
  --log-group-name "API-Gateway-Execution-Logs_f1343lyxnd/prod" \
  --order-by LastEventTime \
  --descending \
  --limit 1 \
  --region ap-northeast-1

# ログイベントを確認
aws logs filter-log-events \
  --log-group-name "API-Gateway-Execution-Logs_f1343lyxnd/prod" \
  --start-time $(date -u -d '5 minutes ago' +%s)000 \
  --region ap-northeast-1
```

## 便利なスクリプト

### 環境変数の設定スクリプト

```bash
#!/bin/bash
# save as: setup-test-env.sh

export API_ENDPOINT="https://f1343lyxnd.execute-api.ap-northeast-1.amazonaws.com/prod"
export API_KEY="YOUR_API_KEY_HERE"

echo "API Gateway test environment configured:"
echo "  API_ENDPOINT: $API_ENDPOINT"
echo "  API_KEY: ${API_KEY:0:10}..."
```

### ヘルスチェックスクリプト

```bash
#!/bin/bash
# save as: health-check.sh

API_ENDPOINT="https://f1343lyxnd.execute-api.ap-northeast-1.amazonaws.com/prod"
API_KEY="YOUR_API_KEY_HERE"

echo "Checking API Gateway health..."

# Test models endpoint
response=$(curl -s -o /dev/null -w "%{http_code}" \
  -X GET "${API_ENDPOINT}/openai/models" \
  -H "x-api-key: ${API_KEY}")

if [ "$response" == "200" ]; then
  echo "✅ Models endpoint: OK"
else
  echo "❌ Models endpoint: Failed (HTTP $response)"
fi

# Test chat completions endpoint
response=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "${API_ENDPOINT}/openai/chat/completions" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"test"}],"max_tokens":5}')

if [ "$response" == "200" ]; then
  echo "✅ Chat completions endpoint: OK"
else
  echo "❌ Chat completions endpoint: Failed (HTTP $response)"
fi
```

## トラブルシューティング

### よくある問題と解決方法

1. **403 Forbidden**
   - APIキーが正しいか確認
   - APIキーがUsage Planに関連付けられているか確認

2. **429 Too Many Requests**
   - レート制限に達している
   - Usage Planの設定を確認

3. **504 Gateway Timeout**
   - OpenAI APIの応答が遅い
   - タイムアウト設定の調整が必要

4. **レスポンスが空**
   - Content-Typeヘッダーが正しく設定されているか確認
   - リクエストボディのJSONが有効か確認

## 注意事項

- APIキーは環境変数やシークレット管理ツールで管理することを推奨
- 本番環境では適切なエラーハンドリングとリトライロジックを実装
- レート制限を考慮した実装を行う
- CloudWatch Logsで定期的にエラーログを確認