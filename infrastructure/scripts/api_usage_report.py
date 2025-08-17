#!/usr/bin/env python3
"""
API Gateway使用量レポート生成スクリプト

APIキーごとの使用量を集計し、レポートを生成します。
"""

import json
import argparse
import logging
import sys
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import csv

try:
    import boto3
except ImportError:
    print("エラー: boto3がインストールされていません")
    print("実行: pip install boto3")
    sys.exit(1)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ApiKeyUsage:
    """APIキーの使用量データ"""
    usage_plan_id: str
    usage_plan_name: str
    api_key_id: str
    api_key_name: str
    usage_count: int
    quota_limit: int
    usage_percentage: float
    throttle_rate: int
    throttle_burst: int
    period_start: str
    period_end: str


class ApiUsageReporter:
    """API Gateway使用量レポーター"""
    
    def __init__(self, region: str = 'ap-northeast-1'):
        """
        初期化
        
        Args:
            region: AWSリージョン
        """
        self.region = region
        self.apigateway = boto3.client('apigateway', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        
    def get_usage_plans(self) -> List[Dict[str, Any]]:
        """すべての使用量プランを取得"""
        usage_plans = []
        try:
            paginator = self.apigateway.get_paginator('get_usage_plans')
            for page in paginator.paginate():
                usage_plans.extend(page.get('items', []))
            logger.info(f"取得した使用量プラン数: {len(usage_plans)}")
            return usage_plans
        except Exception as e:
            logger.error(f"使用量プランの取得に失敗: {e}")
            return []
    
    def get_api_keys_for_plan(self, usage_plan_id: str) -> List[Dict[str, Any]]:
        """使用量プランに関連付けられたAPIキーを取得"""
        api_keys = []
        try:
            paginator = self.apigateway.get_paginator('get_usage_plan_keys')
            for page in paginator.paginate(usagePlanId=usage_plan_id):
                api_keys.extend(page.get('items', []))
            return api_keys
        except Exception as e:
            logger.error(f"APIキーの取得に失敗 (Plan: {usage_plan_id}): {e}")
            return []
    
    def get_api_key_details(self, api_key_id: str) -> Dict[str, Any]:
        """APIキーの詳細情報を取得"""
        try:
            response = self.apigateway.get_api_key(
                apiKey=api_key_id,
                includeValue=False  # APIキーの値は取得しない
            )
            return response
        except Exception as e:
            logger.error(f"APIキー詳細の取得に失敗 (Key: {api_key_id}): {e}")
            return {}
    
    def get_usage(
        self, 
        usage_plan_id: str, 
        api_key_id: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """指定期間の使用量を取得"""
        try:
            response = self.apigateway.get_usage(
                usagePlanId=usage_plan_id,
                keyId=api_key_id,
                startDate=start_date,
                endDate=end_date
            )
            
            logger.info(f"API使用量レスポンス: {response}")
            
            # 使用量を集計
            total_usage = 0
            if 'items' in response:
                # itemsは {APIステージID: [[使用量, 残りクォータ]]} の形式
                for api_stage_id, usage_data in response['items'].items():
                    logger.debug(f"APIステージ {api_stage_id}: {usage_data}")
                    
                    if isinstance(usage_data, list):
                        for data_entry in usage_data:
                            if isinstance(data_entry, list) and len(data_entry) >= 1:
                                # 最初の要素が使用量
                                usage_count = data_entry[0]
                                if isinstance(usage_count, (int, float)):
                                    total_usage += usage_count
                                    logger.debug(f"  使用量: {usage_count}")
            
            logger.info(f"合計使用量: {total_usage}")
            
            return {
                'usage': total_usage,
                'start_date': start_date,
                'end_date': end_date
            }
        except Exception as e:
            logger.error(f"使用量の取得に失敗 (Plan: {usage_plan_id}, Key: {api_key_id}): {e}")
            return {'usage': 0, 'start_date': start_date, 'end_date': end_date}
    
    def collect_usage_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[ApiKeyUsage]:
        """すべてのAPIキーの使用量データを収集"""
        
        # 日付のデフォルト設定（今日）
        if not start_date:
            start_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        if not end_date:
            end_date = start_date
            
        logger.info(f"使用量収集期間: {start_date} から {end_date}")
        
        usage_data = []
        usage_plans = self.get_usage_plans()
        
        for plan in usage_plans:
            plan_id = plan['id']
            plan_name = plan.get('name', 'unnamed')
            
            # クォータ情報を取得
            quota = plan.get('quota', {})
            quota_limit = quota.get('limit', 0)
            quota_period = quota.get('period', 'DAY')
            
            # スロットル情報を取得
            throttle = plan.get('throttle', {})
            throttle_rate = throttle.get('rateLimit', 0)
            throttle_burst = throttle.get('burstLimit', 0)
            
            logger.info(f"処理中の使用量プラン: {plan_name} (ID: {plan_id})")
            
            # APIキーごとの使用量を取得
            api_keys = self.get_api_keys_for_plan(plan_id)
            
            for key in api_keys:
                key_id = key['id']
                key_name = key.get('name', 'unnamed')
                
                # APIキーの詳細を取得
                key_details = self.get_api_key_details(key_id)
                # logger.info(f"APIキー詳細: {key_details}")
                if key_details:
                    key_name = key_details.get('name', key_name)
                
                # 使用量を取得
                usage = self.get_usage(plan_id, key_id, start_date, end_date)
                usage_count = usage['usage']
                
                # 使用率を計算
                usage_percentage = 0
                if quota_limit > 0:
                    if quota_period == 'DAY':
                        # 日次クォータの場合
                        days = (datetime.strptime(end_date, '%Y-%m-%d') - 
                               datetime.strptime(start_date, '%Y-%m-%d')).days + 1
                        adjusted_quota = quota_limit * days
                        usage_percentage = (usage_count / adjusted_quota) * 100
                    elif quota_period == 'WEEK':
                        # 週次クォータの場合
                        usage_percentage = (usage_count / quota_limit) * 100
                    elif quota_period == 'MONTH':
                        # 月次クォータの場合
                        usage_percentage = (usage_count / quota_limit) * 100
                
                usage_entry = ApiKeyUsage(
                    usage_plan_id=plan_id,
                    usage_plan_name=plan_name,
                    api_key_id=key_id,
                    api_key_name=key_name,
                    usage_count=usage_count,
                    quota_limit=quota_limit,
                    usage_percentage=round(usage_percentage, 2),
                    throttle_rate=throttle_rate,
                    throttle_burst=throttle_burst,
                    period_start=start_date,
                    period_end=end_date
                )
                
                usage_data.append(usage_entry)
                logger.debug(f"APIキー {key_name}: {usage_count} リクエスト ({usage_percentage:.1f}%)")
        
        return usage_data
    
    def generate_console_report(self, usage_data: List[ApiKeyUsage]) -> str:
        """コンソール表示用のレポートを生成"""
        report = []
        report.append("=" * 100)
        report.append("API Gateway 使用量レポート")
        report.append("=" * 100)
        
        if not usage_data:
            report.append("データがありません")
            return "\n".join(report)
        
        # 期間情報
        period_start = usage_data[0].period_start if usage_data else ""
        period_end = usage_data[0].period_end if usage_data else ""
        report.append(f"期間: {period_start} 〜 {period_end}")
        report.append("")
        
        # 使用量プランごとにグループ化
        plans = {}
        for entry in usage_data:
            if entry.usage_plan_name not in plans:
                plans[entry.usage_plan_name] = []
            plans[entry.usage_plan_name].append(entry)
        
        # プランごとに表示
        for plan_name, entries in plans.items():
            report.append(f"\n【使用量プラン: {plan_name}】")
            report.append("-" * 80)
            
            # ヘッダー
            report.append(f"{'APIキー名':<30} {'使用量':>10} {'クォータ':>10} {'使用率':>8} {'レート制限':>10}")
            report.append("-" * 80)
            
            # データ行
            total_usage = 0
            for entry in entries:
                total_usage += entry.usage_count
                report.append(
                    f"{entry.api_key_name:<30} "
                    f"{entry.usage_count:>10,} "
                    f"{entry.quota_limit:>10,} "
                    f"{entry.usage_percentage:>7.1f}% "
                    f"{entry.throttle_rate:>10}/秒"
                )
            
            # 小計
            report.append("-" * 80)
            report.append(f"{'小計':<30} {total_usage:>10,}")
        
        # 総計
        total_all = sum(entry.usage_count for entry in usage_data)
        report.append("\n" + "=" * 80)
        report.append(f"{'総計':<30} {total_all:>10,} リクエスト")
        
        # 警告（使用率が高いキー）
        high_usage = [e for e in usage_data if e.usage_percentage > 80]
        if high_usage:
            report.append("\n⚠️  警告: 使用率が80%を超えているAPIキー")
            for entry in high_usage:
                report.append(f"  - {entry.api_key_name}: {entry.usage_percentage:.1f}%")
        
        return "\n".join(report)
    
    def save_json_report(self, usage_data: List[ApiKeyUsage], output_dir: str = "reports") -> str:
        """JSON形式でレポートを保存"""
        Path(output_dir).mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{output_dir}/api_usage_{timestamp}.json"
        
        data = [asdict(entry) for entry in usage_data]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"JSONレポートを保存: {filename}")
        return filename
    
    def save_csv_report(self, usage_data: List[ApiKeyUsage], output_dir: str = "reports") -> str:
        """CSV形式でレポートを保存"""
        Path(output_dir).mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{output_dir}/api_usage_{timestamp}.csv"
        
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            if usage_data:
                fieldnames = asdict(usage_data[0]).keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for entry in usage_data:
                    writer.writerow(asdict(entry))
        
        logger.info(f"CSVレポートを保存: {filename}")
        return filename
    
    def send_cloudwatch_metrics(self, usage_data: List[ApiKeyUsage]) -> None:
        """CloudWatchカスタムメトリクスを送信"""
        namespace = 'Custom/APIGateway'
        timestamp = datetime.now(timezone.utc)
        
        metrics = []
        for entry in usage_data:
            # 使用量メトリクス
            metrics.append({
                'MetricName': 'UsageCount',
                'Value': entry.usage_count,
                'Unit': 'Count',
                'Timestamp': timestamp,
                'Dimensions': [
                    {'Name': 'UsagePlanName', 'Value': entry.usage_plan_name},
                    {'Name': 'ApiKeyName', 'Value': entry.api_key_name}
                ]
            })
            
            # 使用率メトリクス
            metrics.append({
                'MetricName': 'UsagePercentage',
                'Value': entry.usage_percentage,
                'Unit': 'Percent',
                'Timestamp': timestamp,
                'Dimensions': [
                    {'Name': 'UsagePlanName', 'Value': entry.usage_plan_name},
                    {'Name': 'ApiKeyName', 'Value': entry.api_key_name}
                ]
            })
        
        # バッチで送信（最大20メトリクス/リクエスト）
        for i in range(0, len(metrics), 20):
            batch = metrics[i:i+20]
            try:
                self.cloudwatch.put_metric_data(
                    Namespace=namespace,
                    MetricData=batch
                )
                logger.info(f"CloudWatchメトリクスを送信: {len(batch)}個")
            except Exception as e:
                logger.error(f"CloudWatchメトリクスの送信に失敗: {e}")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='API Gateway使用量レポート生成',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        help='開始日 (YYYY-MM-DD形式、デフォルト: 今日)'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        help='終了日 (YYYY-MM-DD形式、デフォルト: 開始日と同じ)'
    )
    
    parser.add_argument(
        '--output',
        choices=['console', 'json', 'csv', 'all'],
        default='console',
        help='出力形式 (デフォルト: console)'
    )
    
    parser.add_argument(
        '--cloudwatch',
        action='store_true',
        help='CloudWatchメトリクスを送信'
    )
    
    parser.add_argument(
        '--region',
        type=str,
        default='ap-northeast-1',
        help='AWSリージョン (デフォルト: ap-northeast-1)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='デバッグログを表示'
    )
    
    args = parser.parse_args()
    
    # ログレベル設定
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # レポーター初期化
    reporter = ApiUsageReporter(region=args.region)
    
    # 使用量データ収集
    logger.info("使用量データを収集中...")
    usage_data = reporter.collect_usage_data(
        start_date=args.start_date,
        end_date=args.end_date
    )
    
    if not usage_data:
        logger.warning("収集できたデータがありません")
        return 1
    
    # レポート出力
    if args.output in ['console', 'all']:
        report = reporter.generate_console_report(usage_data)
        print(report)
    
    if args.output in ['json', 'all']:
        reporter.save_json_report(usage_data)
    
    if args.output in ['csv', 'all']:
        reporter.save_csv_report(usage_data)
    
    # CloudWatchメトリクス送信
    if args.cloudwatch:
        logger.info("CloudWatchメトリクスを送信中...")
        reporter.send_cloudwatch_metrics(usage_data)
    
    logger.info("完了")
    return 0


if __name__ == '__main__':
    sys.exit(main())