#!/bin/bash

# API使用量日次レポート実行スクリプト
# 
# 使用方法:
#   ./daily_report.sh
#
# crontabでの設定例（毎日午前1時実行）:
#   0 1 * * * /path/to/api-gateway-iac/scripts/daily_report.sh

set -e

# スクリプトのディレクトリに移動
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ログディレクトリ作成
LOG_DIR="../logs"
mkdir -p "$LOG_DIR"

# ログファイル名
LOG_FILE="$LOG_DIR/api_usage_report_$(date +%Y%m%d).log"

# 実行ログの開始
echo "========================================" >> "$LOG_FILE"
echo "実行開始: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Python仮想環境の有効化（存在する場合）
if [ -f "../infrastructure/.venv/bin/activate" ]; then
    source ../infrastructure/.venv/bin/activate
fi

# 昨日の使用量レポート生成
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d)
echo "昨日（$YESTERDAY）の使用量レポートを生成中..." | tee -a "$LOG_FILE"

python api_usage_report.py \
    --start-date "$YESTERDAY" \
    --output all \
    --cloudwatch \
    2>&1 | tee -a "$LOG_FILE"

# 週次レポート（月曜日に実行）
if [ $(date +%u) -eq 1 ]; then
    echo "" | tee -a "$LOG_FILE"
    echo "週次レポートを生成中..." | tee -a "$LOG_FILE"
    
    # 先週の開始日と終了日を計算
    if command -v gdate &> /dev/null; then
        # macOS with GNU date
        LAST_WEEK_START=$(gdate -d "last monday" +%Y-%m-%d)
        LAST_WEEK_END=$(gdate -d "last sunday" +%Y-%m-%d)
    elif date --version 2>/dev/null | grep -q GNU; then
        # Linux with GNU date
        LAST_WEEK_START=$(date -d "last monday" +%Y-%m-%d)
        LAST_WEEK_END=$(date -d "last sunday" +%Y-%m-%d)
    else
        # macOS with BSD date
        LAST_WEEK_START=$(date -v-7d -v-monday +%Y-%m-%d)
        LAST_WEEK_END=$(date -v-1d +%Y-%m-%d)
    fi
    
    echo "期間: $LAST_WEEK_START から $LAST_WEEK_END" | tee -a "$LOG_FILE"
    
    python api_usage_report.py \
        --start-date "$LAST_WEEK_START" \
        --end-date "$LAST_WEEK_END" \
        --output all \
        2>&1 | tee -a "$LOG_FILE"
fi

# 月次レポート（毎月1日に実行）
if [ $(date +%d) -eq 01 ]; then
    echo "" | tee -a "$LOG_FILE"
    echo "月次レポートを生成中..." | tee -a "$LOG_FILE"
    
    # 先月の開始日と終了日を計算
    if command -v gdate &> /dev/null; then
        # macOS with GNU date
        LAST_MONTH_START=$(gdate -d "last month" +%Y-%m-01)
        LAST_MONTH_END=$(gdate -d "$(gdate +%Y-%m-01) -1 day" +%Y-%m-%d)
    elif date --version 2>/dev/null | grep -q GNU; then
        # Linux with GNU date
        LAST_MONTH_START=$(date -d "last month" +%Y-%m-01)
        LAST_MONTH_END=$(date -d "$(date +%Y-%m-01) -1 day" +%Y-%m-%d)
    else
        # macOS with BSD date
        LAST_MONTH_START=$(date -v-1m -v1d +%Y-%m-%d)
        LAST_MONTH_END=$(date -v1d -v-1d +%Y-%m-%d)
    fi
    
    echo "期間: $LAST_MONTH_START から $LAST_MONTH_END" | tee -a "$LOG_FILE"
    
    python api_usage_report.py \
        --start-date "$LAST_MONTH_START" \
        --end-date "$LAST_MONTH_END" \
        --output all \
        2>&1 | tee -a "$LOG_FILE"
fi

# 古いログファイルの削除（30日以上前）
find "$LOG_DIR" -name "api_usage_report_*.log" -type f -mtime +30 -delete

# 古いレポートファイルの削除（30日以上前）
find "../reports" -name "api_usage_*.json" -type f -mtime +30 -delete
find "../reports" -name "api_usage_*.csv" -type f -mtime +30 -delete

echo "" | tee -a "$LOG_FILE"
echo "実行完了: $(date)" | tee -a "$LOG_FILE"