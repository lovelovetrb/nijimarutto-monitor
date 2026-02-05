import abc
import logging

import requests

from nijimarutto_monitor.models import StockResult

logger = logging.getLogger(__name__)


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
    """Discord Webhook 通知"""

    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    def notify(self, result: StockResult) -> None:
        if result.is_available:
            content = (
                f"🎉 **在庫復活！**\n"
                f"**{result.variant_name}** が購入可能になりました！\n"
                f"{result.url}"
            )
        else:
            content = (
                f"😢 **売り切れ**\n"
                f"**{result.variant_name}** が売り切れになりました。\n"
                f"{result.url}"
            )
        payload = {"content": content}
        try:
            resp = requests.post(self.webhook_url, json=payload, timeout=10)
            resp.raise_for_status()
            logger.info("Discord 通知を送信しました。")
        except requests.RequestException as e:
            logger.error("Discord 通知の送信に失敗: %s", e)
