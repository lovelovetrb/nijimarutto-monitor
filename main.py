"""にじさんじショップ 在庫監視ツール"""

import abc
import logging
import os
import time
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

TARGET_URL = "https://shop.nijisanji.jp/SSZS-56575.html"
TARGET_VARIANT = "葛葉"
CHECK_INTERVAL_SEC = 10 * 60  # 10分


@dataclass
class StockResult:
    variant_name: str
    is_available: bool
    url: str


# --- 通知 ---


class Notifier(abc.ABC):
    """通知の基底クラス。新しい通知先を追加する場合はこれを継承してください。"""

    @abc.abstractmethod
    def notify(self, result: StockResult) -> None: ...


class ConsoleNotifier(Notifier):
    def notify(self, result: StockResult) -> None:
        if result.is_available:
            logger.info(
                "★★★ 在庫復活！ ★★★  %s が購入可能です！ → %s",
                result.variant_name,
                result.url,
            )
        else:
            logger.info("%s は現在売り切れです。", result.variant_name)


class DiscordWebhookNotifier(Notifier):
    """Discord Webhook 通知（後で有効化する場合に使用）"""

    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    def notify(self, result: StockResult) -> None:
        if not result.is_available:
            return  # 売り切れ中は Discord には送らない
        payload = {
            "content": (
                f"🎉 **在庫復活！**\n"
                f"**{result.variant_name}** が購入可能になりました！\n"
                f"{result.url}"
            ),
        }
        try:
            resp = requests.post(self.webhook_url, json=payload, timeout=10)
            resp.raise_for_status()
            logger.info("Discord 通知を送信しました。")
        except requests.RequestException as e:
            logger.error("Discord 通知の送信に失敗: %s", e)


# --- 在庫チェック ---


def check_stock(url: str, variant_name: str) -> StockResult:
    """指定バリエーションの在庫状況を取得する。"""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # バリエーション名を含む radio-button-title を探索
    for title_span in soup.select("span.radio-button-title"):
        if variant_name not in title_span.get_text():
            continue

        # 親の <li> まで遡る
        li = title_span.find_parent("li")
        if li is None:
            continue

        # data-nostock 属性で判定（radio input は li 直下の span 内）
        radio = li.select_one("input.js-product-radio")
        if radio and radio.get("data-nostock") == "true":
            return StockResult(variant_name, is_available=False, url=url)

        # js-is-available hidden input で判定
        avail_input = li.select_one("input.js-is-available")
        if avail_input and avail_input.get("value") == "false":
            return StockResult(variant_name, is_available=False, url=url)

        # 「在庫なし」ラベルの有無で判定
        sold_out_label = li.select_one("span.label-red")
        if sold_out_label and "在庫なし" in sold_out_label.get_text():
            return StockResult(variant_name, is_available=False, url=url)

        # 上記いずれにも該当しなければ在庫あり
        return StockResult(variant_name, is_available=True, url=url)

    raise ValueError(f"バリエーション '{variant_name}' がページ内に見つかりませんでした。")


# --- メインループ ---


def main() -> None:
    notifiers: list[Notifier] = [ConsoleNotifier()]

    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if discord_webhook_url:
        notifiers.append(DiscordWebhookNotifier(discord_webhook_url))
        logger.info("Discord Webhook 通知: 有効")
    else:
        logger.info("Discord Webhook 通知: 無効 (DISCORD_WEBHOOK_URL 未設定)")

    logger.info("=== にじさんじショップ 在庫監視ツール ===")
    logger.info("対象: %s", TARGET_VARIANT)
    logger.info("URL:  %s", TARGET_URL)
    logger.info("間隔: %d秒 (%d分)", CHECK_INTERVAL_SEC, CHECK_INTERVAL_SEC // 60)
    logger.info("監視を開始します。Ctrl+C で終了。")

    prev_available: bool | None = None

    while True:
        try:
            result = check_stock(TARGET_URL, TARGET_VARIANT)

            # 状態が変化した場合、または初回チェック時に通知
            if prev_available is None or result.is_available != prev_available:
                for notifier in notifiers:
                    notifier.notify(result)
                prev_available = result.is_available
            else:
                status = "在庫あり" if result.is_available else "売り切れ"
                logger.info("変化なし（%s）", status)

        except requests.RequestException as e:
            logger.error("ページ取得に失敗: %s", e)
        except ValueError as e:
            logger.error("%s", e)
        except Exception:
            logger.exception("予期しないエラー")

        time.sleep(CHECK_INTERVAL_SEC)


if __name__ == "__main__":
    main()
