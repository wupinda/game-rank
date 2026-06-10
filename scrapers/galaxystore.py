"""
三星 Galaxy Store 游戏榜单
使用内部 XML-RPC 接口（storeserver/ods.as），无需认证。
alignOrder: bestselling = 畅销榜, popular = 热门榜
categoryID: G000046767 = Online Game（最大分类）
"""
import xml.etree.ElementTree as ET
import logging
from .base import BaseScraper, RankItem

logger = logging.getLogger(__name__)

_API = "https://galaxystore.samsung.com/storeserver/ods.as"

_HEADERS = {
    "Content-Type":      "application/xml",
    "User-Agent":        ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/124.0.0.0 Safari/537.36"),
    "Origin":            "https://galaxystore.samsung.com",
    "x-galaxystore-url": "http://us-odc.samsungapps.com/ods.as",
    "Accept":            "application/xml, text/xml, */*",
}

_ORDER_MAP = {
    "revenue":  "bestselling",
    "download": "popular",
}

_CATEGORY_ID = "G000046767"  # Online Game

_XML_TPL = """\
<?xml version="1.0" encoding="UTF-8"?>
<SamsungProtocol networkType="0" version2="0" lang="EN" openApiVersion="28"
    deviceModel="SM-G998B"
    storeFilter="themeDeviceModel=SM-G998B_TM||OTFVersion=8000000"
    mcc="310" mnc="03" csc="MWD" odcVersion="9.9.30.9" version="6.5"
    filter="1" odcType="01" systemId="1604973510099"
    sessionId="10a4ee19e202011101104" logId="XXX" userMode="0">
  <request name="categoryProductList2Notc" id="2030" numParam="10" transactionId="10a4ee19">
    <param name="imgWidth">135</param>
    <param name="startNum">1</param>
    <param name="imgHeight">135</param>
    <param name="alignOrder">{align_order}</param>
    <param name="contentType">All</param>
    <param name="endNum">{top_n}</param>
    <param name="categoryName">{cat}</param>
    <param name="categoryID">{cat}</param>
    <param name="srcType">01</param>
    <param name="status">0</param>
  </request>
</SamsungProtocol>"""


def _list_to_dict(list_elem) -> dict:
    """Convert <list> element with <value name="..."> children to dict."""
    return {v.get("name"): v.text for v in list_elem.findall("value")}


class GalaxyStoreScraper(BaseScraper):
    PLATFORM = "galaxystore"
    SUPPORTED_RANK_TYPES = ["download", "revenue"]

    def fetch(self, rank_type: str) -> list:
        align_order = _ORDER_MAP.get(rank_type, "popular")
        xml_body = _XML_TPL.format(
            align_order=align_order,
            top_n=self.TOP_N,
            cat=_CATEGORY_ID,
        )

        try:
            resp = self.session.post(
                _API,
                params={"id": "categoryProductList2Notc"},
                data=xml_body.encode("utf-8"),
                headers=_HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
        except Exception as e:
            logger.warning(f"Galaxy Store 接口请求失败: {e}")
            return []

        try:
            root = ET.fromstring(resp.text)
        except ET.ParseError as e:
            logger.warning(f"Galaxy Store XML 解析失败: {e}")
            return []

        items = []
        for entry in root.iter("list"):
            d = _list_to_dict(entry)
            name = (d.get("productName") or "").strip()
            if not name:
                continue
            items.append(RankItem(
                rank=len(items) + 1,
                name=name,
                platform=self.PLATFORM,
                rank_type=rank_type,
                game_id=d.get("productID") or "",
                developer=d.get("sellerName") or "",
                icon_url=d.get("productImgUrl") or "",
                rating=float(d.get("averageRating") or 0),
            ))
            if len(items) >= self.TOP_N:
                break

        if not items:
            logger.warning("Galaxy Store 未解析到数据")
        return items
