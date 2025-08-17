#!/bin/bash

# MFA認証スクリプト
# 使用方法: source ./scripts/mfa-auth.sh

# 色付き出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# スクリプトのディレクトリを取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"

# .envファイルが存在する場合は読み込む
if [ -f "$INFRA_DIR/.env" ]; then
    # .envファイルから必要な変数を読み込む
    export $(grep -E '^CDK_DEFAULT_ACCOUNT=' "$INFRA_DIR/.env" | xargs)
fi

# MFAデバイスARN
MFA_SERIAL="arn:aws:iam::${CDK_DEFAULT_ACCOUNT}:mfa/aws-console-test"
# PROFILE="test-cdk"
PROFILE="$AWS_PROFILE"
DURATION_SECONDS=3600  # 1時間

echo -e "${YELLOW}AWS MFA認証を開始します...${NC}"
echo "使用するMFAデバイス: $MFA_SERIAL"
echo ""

# MFAコードの入力
read -p "6桁のMFAコードを入力してください: " MFA_CODE

# 入力値の検証
if [[ ! "$MFA_CODE" =~ ^[0-9]{6}$ ]]; then
    echo -e "${RED}エラー: MFAコードは6桁の数字である必要があります${NC}"
    return 1 2>/dev/null || exit 1
fi

echo -e "${YELLOW}一時認証情報を取得中...${NC}"

# 一時認証情報の取得
CREDS=$(aws sts get-session-token \
    --serial-number "$MFA_SERIAL" \
    --token-code "$MFA_CODE" \
    --duration-seconds "$DURATION_SECONDS" \
    --profile "$PROFILE" \
    --output json 2>&1)

if [ $? -ne 0 ]; then
    echo -e "${RED}エラー: 認証に失敗しました${NC}"
    echo "$CREDS"
    return 1 2>/dev/null || exit 1
fi

# jqがインストールされているか確認
if ! command -v jq &> /dev/null; then
    echo -e "${RED}エラー: jqがインストールされていません${NC}"
    echo "sudo apt-get install jq でインストールしてください"
    return 1 2>/dev/null || exit 1
fi

# 環境変数の設定
export AWS_ACCESS_KEY_ID=$(echo "$CREDS" | jq -r '.Credentials.AccessKeyId')
export AWS_SECRET_ACCESS_KEY=$(echo "$CREDS" | jq -r '.Credentials.SecretAccessKey')
export AWS_SESSION_TOKEN=$(echo "$CREDS" | jq -r '.Credentials.SessionToken')
export AWS_DEFAULT_REGION="ap-northeast-1"

# 有効期限の計算
EXPIRATION=$(echo "$CREDS" | jq -r '.Credentials.Expiration')
EXPIRATION_LOCAL=$(date -d "$EXPIRATION" +'%Y-%m-%d %H:%M:%S %Z')

echo -e "${GREEN}MFA認証が成功しました！${NC}"
echo "有効期限: $EXPIRATION_LOCAL"
echo ""
echo "以下のコマンドが使用可能になりました:"
echo "  - cdk bootstrap"
echo "  - cdk deploy"
echo "  - その他のAWS CLIコマンド"
echo ""
echo -e "${YELLOW}注意: この認証情報は${DURATION_SECONDS}秒（1時間）有効です${NC}"

# 現在の認証情報を確認
echo ""
echo "現在の認証情報:"
aws sts get-caller-identity --no-cli-pager