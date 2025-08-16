# TODO一覧

このディレクトリには、API Gateway IaCプロジェクトのTODOリストがまとめられています。

## 実装タスク

### 高優先度

1. **[APIキーごとの使用量追跡システム](./api-key-usage-tracking.md)**
   - CloudWatch Logsのcallerフィールド問題への対応
   - Lambda Authorizerの実装
   - カスタムメトリクスの自動収集

2. **[Secrets Manager統合](./secrets-manager-integration.md)**
   - OpenAI/Firecrawl APIキーのセキュア管理
   - Lambda関数での動的キー取得
   - 環境変数からの移行

### 中優先度

3. **監視・アラート強化**
   - CloudWatchダッシュボードのテンプレート化
   - 異常検知アラームの設定
   - 使用量制限アラートの実装

4. **コスト最適化**
   - Lambda関数のコールドスタート対策
   - CloudWatchログの保持期間最適化
   - API Gatewayキャッシュの実装検討

### 低優先度

5. **ドキュメント整備**
   - API仕様書の自動生成
   - 運用手順書の更新
   - トラブルシューティングガイド

6. **テスト自動化**
   - 統合テストの実装
   - 負荷テストの設定
   - CI/CDパイプラインの改善

## 完了済みタスク

- ✅ API Gateway基本構成の実装
- ✅ OpenAI/Firecrawl プロキシ統合
- ✅ 使用量プランとAPIキー管理
- ✅ CloudWatch Logs設定
- ✅ CORS設定

## 次のマイルストーン

- **v1.1.0** (2025年2月予定)
  - Lambda Authorizer実装
  - Secrets Manager統合
  - カスタムメトリクス収集

- **v1.2.0** (2025年3月予定)
  - 包括的な監視ダッシュボード
  - 自動スケーリング設定
  - マルチリージョン対応検討

## 貢献方法

新しいTODOアイテムを追加する場合：
1. このディレクトリに新しいMarkdownファイルを作成
2. ファイル名は`機能名.md`形式で
3. このREADME.mdに追加
4. 優先度を設定

## 関連リソース

- [プロジェクトCLAUDE.md](../../CLAUDE.md)
- [インフラストラクチャREADME](../../infrastructure/README.md)
- [API設計ドキュメント](../api-gateway-design.md)