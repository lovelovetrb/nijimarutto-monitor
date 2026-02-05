import logging
import os
import time

import requests
from dotenv import load_dotenv

from nijimarutto_monitor.checker import check_stock
from nijimarutto_monitor.config import AppConfig, MonitorTarget, load_config
from nijimarutto_monitor.notifier import ConsoleNotifier, DiscordWebhookNotifier, Notifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class Monitor:
    """複数ターゲットの在庫を監視し、状態変化時に通知する。"""

    def __init__(self, config: AppConfig, notifiers: list[Notifier]) -> None:
        self.config = config
        self.notifiers = notifiers
        self._prev_states: dict[str, bool | None] = {
            t.state_key: None for t in config.targets
        }

    def run(self) -> None:
        logger.info("=== にじさんじショップ 在庫監視ツール ===")
        logger.info("監視対象: %d 件", len(self.config.targets))
        for t in self.config.targets:
            logger.info("  - %s (%s)", t.label, t.url)
        logger.info(
            "間隔: %d秒 (%d分)",
            self.config.check_interval_sec,
            self.config.check_interval_sec // 60,
        )
        logger.info("監視を開始します。Ctrl+C で終了。")

        while True:
            for target in self.config.targets:
                self._check_target(target)
            time.sleep(self.config.check_interval_sec)

    def _check_target(self, target: MonitorTarget) -> None:
        try:
            result = check_stock(target.url, target.variant_name)
            prev = self._prev_states[target.state_key]

            if prev is None or result.is_available != prev:
                for notifier in self.notifiers:
                    notifier.notify(result)
                self._prev_states[target.state_key] = result.is_available
            else:
                status = "在庫あり" if result.is_available else "売り切れ"
                logger.info("[%s] 変化なし（%s）", target.label, status)

        except requests.RequestException as e:
            logger.error("[%s] ページ取得に失敗: %s", target.label, e)
        except ValueError as e:
            logger.error("[%s] %s", target.label, e)
        except Exception:
            logger.exception("[%s] 予期しないエラー", target.label)


def build_notifiers() -> list[Notifier]:
    """環境変数を参照して Notifier のリストを構築する。"""
    notifiers: list[Notifier] = [ConsoleNotifier()]

    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if discord_webhook_url:
        notifiers.append(DiscordWebhookNotifier(discord_webhook_url))
        logger.info("Discord Webhook 通知: 有効")
    else:
        logger.info("Discord Webhook 通知: 無効 (DISCORD_WEBHOOK_URL 未設定)")

    return notifiers


def main() -> None:
    load_dotenv()
    config = load_config()
    notifiers = build_notifiers()
    monitor = Monitor(config, notifiers)
    monitor.run()
