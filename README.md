# nijimarutto-monitor

にじさんじショップの商品在庫を定期的にチェックし、在庫状態の変化を Discord に通知するツールです。

## セットアップ

[uv](https://docs.astral.sh/uv/) が必要です。

```bash
# 依存パッケージのインストール
uv sync
```

### Discord 通知の設定（任意）

```bash
cp .env.example .env
```

`.env` の `DISCORD_WEBHOOK_URL` に Discord Webhook URL を設定すると、在庫状態の変化時に通知が送られます。未設定の場合はコンソールログのみ出力されます。

## 使い方

### 監視対象の設定

`config.yaml` を編集してください。

```yaml
check_interval_sec: 600  # チェック間隔（秒）

targets:
  - url: "https://shop.nijisanji.jp/SSZS-56575.html"
    variant_name: "葛葉"
    label: "にじまるっと 葛葉"

  - url: "https://shop.nijisanji.jp/SSZS-99999.html"
    variant_name: "叶"
    label: "別商品 叶"
```

| フィールド | 必須 | 説明 |
|---|---|---|
| `url` | Yes | 商品ページの URL |
| `variant_name` | Yes | 監視するバリエーション名（ページ内の表記と一致させる） |
| `label` | No | ログや通知に表示する名前（省略時は `variant_name` が使われる） |

### 起動

```bash
uv run nijimarutto-monitor
```

### Docker

```bash
docker build -t nijimarutto-monitor .
docker run --env-file .env nijimarutto-monitor
```

`config.yaml` を差し替えたい場合はマウントできます。

```bash
docker run --env-file .env -v ./config.yaml:/app/config.yaml nijimarutto-monitor
```

## 環境変数

| 変数名 | 説明 |
|---|---|
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL（任意） |
| `CONFIG_PATH` | 設定ファイルのパス（デフォルト: `config.yaml`） |
