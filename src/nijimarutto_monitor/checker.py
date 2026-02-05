import requests
from bs4 import BeautifulSoup

from nijimarutto_monitor.models import StockResult


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
