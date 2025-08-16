# 1) アーキテクチャの全体像（決定事項の整理）

- **ゲートウェイ分割（用途別）**

  - `GW-openai`, `GW-firecrawl`, `GW-vertex` … のように**物理 API を用途単位で分割**
  - 各ゲートウェイに **`dev` / `stage` / `prod`** のステージ

- **Usage Plan（帯域プラン）**

  - `basic`: **`openai` のみ**（prod）
  - `developer`: **全ゲートウェイの `prod`** にアタッチ（帯域/クォータは developer 用）

- **API キー**

  - 原則 **ユーザー/アプリ単位で 1 本**（環境ごとに分離推奨: dev/stage/prod）
  - 1 キー = 1 Usage Plan（必要あればキーを複数発行）

> ねらい：**「可否（何に入れるか）」を“ゲートウェイ/ステージの関連付け”で表現し、
> 「帯域（どれだけ使えるか）」を Usage Plan で表現**して分離。

---

# 2) アクセス可否と帯域の分離（ポリシー設計）

- **可否（プロダクト権限）**＝**どの API のどのステージに入れるか**

  - `basic` → `GW-openai:prod` のみ関連付け
  - `developer` → `GW-*:*:prod`（= すべての prod）関連付け

- **帯域（レート/クォータ）**＝ Usage Plan 側のパラメータ

  - 例）`basic`: 1 rps / 50k req 月, `developer`: 10 rps / 1M req 月

- **補助的に JWT/Authorizer を併用**（推奨）

  - 共有キー対策、利用停止、組織/ユーザー ID の監査付与のため
  - `authorizerContext`: `orgId`, `userId`, `plan`, `entitlements` を下流に伝搬

---

# 3) キー/メタデータ設計

- **キー発行単位**：ユーザー or クライアントアプリ × 環境（dev/stage/prod）
- **メタテーブル**（例: DynamoDB）

  - `apiKeyId` → `{ orgId, userId, plan, gateways=[openai], stages=[prod], createdAt, status }`

- **ローテーション/失効**：Secrets Manager + 自動化（CI/CD）

---

# 4) 可視化・課金配賦のための計測

- **使用量 API とアクセスログ**の二段構え

  - 使用量（`GetUsage` 等）で **apiKeyId 別のリクエスト数**を取得
  - アクセスログに **`$context.identity.apiKeyId` / `gateway` / `stage` / `route` / `orgId`（authorizer）** を必ず出力

- **集計ビュー（Athena/QuickSight など）**

  - 粒度 ①：`date, apiKeyId, gateway, stage, route` → req 数 / エラー率 / p95
  - 粒度 ②：`orgId, plan` → **組織別・プラン別コスト見える化**
  - 単価テーブル（原価/課金）× 使用量で**概算コスト**を算出し、**ゲートウェイ単位の配賦**を明示

---

# 5) 運用ルールとランブック（例）

- **プロビジョニング**

  1. 組織/ユーザー登録 → 2) `plan` 決定 → 3) API キー発行 → 4) 対応ゲートウェイ/ステージへ関連付け

- **昇格/降格**

  - `basic`⇄`developer` の切替は **Usage Plan の再関連付け**で完了（キーは据え置き可）

- **インシデント対応**

  - 乱用/漏洩: **キー即失効 + ローテーション**、ログで影響範囲追跡
  - スパイク: **レート/バーストの一時調整** + WAF/ボット対策

- **デプロイ**

  - `dev` → `stage` → `prod` の昇格で**破壊的変更はステージ間で吸収**
  - ステージ別に**別キー**を使うため、テナント影響を限定

---

# 6) セキュリティ&ガバナンスの要点

- **共有キー禁止**（ユーザー/アプリごとに一意）
- **OIDC/JWT 併用**（キーは識別子、JWT は実認証）
- **WAF + IP 制御 + CORS 明示**
- **監査**：`orgId, userId, apiKeyId, plan, gateway, stage, route, statusCode, latency` をログ行に

---

# 7) IaC（Terraform）構成イメージ

- `modules/apigw/<usecase>/` … `openai`, `firecrawl`, `vertex`
- `apigw_<usecase>_api` + `apigw_<usecase>_stage_{dev,stage,prod}`
- `apigw_usage_plan_{basic,developer}`（rps/quota を変数化）
- `apigw_api_key`（命名規約: `{org}-{app}-{env}`）
- `apigw_usage_plan_key`（キー ⇆ プラン 紐付け）
- `cloudwatch_log_group`（構造化 JSON ログ）
- 可観測性/ダッシュボードは別モジュールで再利用化

---

# 8) トレードオフと回避策

- **API 数/ステージ数が増える** → リソース/デプロイの管理コスト上昇

  - 回避：**命名規約・IaC モジュール化・CI/CD テンプレート化**

- **Usage Plan だけでは細粒度の“パス単位許可”が弱い**

  - 必要に応じ **Authorizer でルート単位の deny/allow** を追加

- **コスト配賦の正確性**

  - 下流（Lambda/外部 API）の単価差がある場合は**ゲートウェイ別に係数**を持ち、**ルート別係数**も検討

---

# 9) 最終チェックリスト

- [ ] `basic` が **`GW-openai:prod` のみ**に関連付いている
- [ ] `developer` が **全 `*:prod`** に関連付いている
- [ ] すべてのアクセスログに **apiKeyId / orgId / plan / gateway / stage / route** が出る
- [ ] キーは **ユーザー/アプリ × 環境**で一意、共有なし
- [ ] 使用量 API の取得 →S3→Athena DDL→ 可視化まで自動化
- [ ] ローテーション/失効のランブックと自動化
- [ ] CI/CD で `dev→stage→prod` の昇格とロールバック手順を用意

---

この設計は、**“プロダクト可否（ゲートウェイ/ステージ関連付け）”と“帯域（Usage Plan）”の責務分離**が明確で、**可視化と運用自動化の土台**として優れています。
必要なら、この方針で動く **Terraform 雛形（API/Stage/UsagePlan/APIKey/Log）** と **Athena 集計 SQL** をまとめてお出しします。
