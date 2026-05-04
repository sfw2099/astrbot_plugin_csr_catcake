# -*- coding: utf-8 -*-
import os
import re
import json
import string
import random
import aiohttp
import asyncio

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register, StarTools
from astrbot.api import logger, AstrBotConfig
from astrbot.api.all import Plain, Image, MessageChain

API_URL = "https://catcake.hoshimi.io/api/records"
BASE_URL = "https://catcake.hoshimi.io/"
ANJI_CAKE = "阿基喵利"

SERVER_RULES = {
    "cn": lambda u: u[0] in "123" and len(u) == 9,
    "bili": lambda u: u.startswith("5"),
    "asia": lambda u: u.startswith("8") or (u.startswith("18") and len(u) == 10),
    "na": lambda u: u.startswith("6"),
    "eu": lambda u: u.startswith("7"),
    "sar": lambda u: u.startswith("9"),
}

SERVER_LABELS = {
    "cn": "官服", "bili": "B服", "asia": "亚服",
    "na": "美服", "eu": "欧服", "sar": "港澳台",
    "other": "其他", "all": "全部",
}

SERVER_ALIASES = {
    "官服": "cn", "cn": "cn", "b服": "bili", "B服": "bili", "bili": "bili",
    "亚服": "asia", "asia": "asia", "美服": "na", "na": "na",
    "欧服": "eu", "eu": "eu", "港澳台": "sar", "sar": "sar",
    "其他": "other", "other": "other", "全部": "all", "全服": "all", "all": "all",
}

CAKES = [
    {"n": "阿基喵利", "r": "阿基维利", "s": "img/catcake/阿基喵利_阿基维利.png"},
    {"n": "雪顶椰椰", "r": "白厄", "s": "img/catcake/雪顶椰椰_白厄.png"},
    {"n": "糯米团", "r": "丹恒", "s": "img/catcake/糯米团_丹恒.png"},
    {"n": "红豆牛奶", "r": "风堇", "s": "img/catcake/红豆牛奶_风堇.png"},
    {"n": "太卜糍", "r": "符玄", "s": "img/catcake/太卜糍_符玄.png"},
    {"n": "捣乱专家", "r": "桂乃芬", "s": "img/catcake/捣乱专家_桂乃芬.png"},
    {"n": "藤萝饼", "r": "黑塔", "s": "img/catcake/藤萝饼_黑塔.png"},
    {"n": "花见团子", "r": "花火", "s": "img/catcake/花见团子_花火.png"},
    {"n": "盹盹咪", "r": "景元", "s": "img/catcake/盹盹咪_景元.png"},
    {"n": "星辰拿铁", "r": "姬子", "s": "img/catcake/星辰拿铁_姬子.png"},
    {"n": "墨镜猫咪", "r": "卡芙卡", "s": "img/catcake/墨镜猫咪_卡芙卡.png"},
    {"n": "垃圾糕", "r": "开拓者", "s": "img/catcake/垃圾糕_开拓者.png"},
    {"n": "纯白的孩子", "r": "克拉拉", "s": "img/catcake/纯白的孩子_克拉拉.png"},
    {"n": "萤绒绒", "r": "流萤", "s": "img/catcake/萤绒绒_流萤.png"},
    {"n": "薄荷提拉咪", "r": "那刻夏", "s": "img/catcake/薄荷提拉咪_那刻夏.png"},
    {"n": "幸运点心", "r": "青雀", "s": "img/catcake/幸运点心_青雀.png"},
    {"n": "芝麻酥", "r": "刃", "s": "img/catcake/芝麻酥_刃.png"},
    {"n": "拉姆之友", "r": "阮梅", "s": "img/catcake/拉姆之友_阮梅.png"},
    {"n": "冰糕", "r": "三月七", "s": "img/catcake/冰糕_三月七.png"},
    {"n": "蜂蜜骰子", "r": "砂金", "s": "img/catcake/蜂蜜骰子_砂金.png"},
    {"n": "重力酥", "r": "瓦尔特", "s": "img/catcake/重力酥_瓦尔特_杨.png"},
    {"n": "蝶豆花慕斯", "r": "遐蝶", "s": "img/catcake/蝶豆花慕斯_遐蝶.png"},
    {"n": "白桃布丁", "r": "昔涟", "s": "img/catcake/白桃布丁_昔涟.png"},
    {"n": "天使圣代", "r": "星期日", "s": "img/catcake/天使圣代_星期日.png"},
    {"n": "白玉青团", "r": "爻光", "s": "img/catcake/白玉青团_爻光.png"},
    {"n": "游戏糕手", "r": "银狼", "s": "img/catcake/游戏糕手_银狼.png"},
    {"n": "蓝莓罐子", "r": "真理医生", "s": "img/catcake/蓝莓罐子_真理医生.png"},
    {"n": "谐乐小喵", "r": "知更鸟", "s": "img/catcake/谐乐小喵_知更鸟.png"},
]


@register("astrbot_plugin_csr_catcake", "ALin",
          "星穹铁道猫猫糕查询 - /找猫糕 /登记猫猫糕 /删除猫猫糕", "1.2.0")
class CatCakePlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.cake_lookup = {c["n"]: c for c in CAKES}
        self.char_lookup = {}
        for c in CAKES:
            self.char_lookup.setdefault(c["r"], []).append(c["n"])
        self._session = None
        # SID file in plugin data dir (survives updates)
        self._data_dir = StarTools.get_data_dir("astrbot_plugin_csr_catcake")
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._sid_file = self._data_dir / "sid.txt"
        self._sid = None

    # ── SID management (same algorithm as the website) ────────────────
    def _get_sid(self):
        if self._sid:
            return self._sid
        if self._sid_file.exists():
            sid = self._sid_file.read_text("utf-8").strip()
            if re.match(r'^[A-Za-z0-9_\-]{8,128}$', sid):
                self._sid = sid
                return sid
        # Generate new SID
        chars = string.ascii_letters + string.digits + "-_"
        sid = "".join(random.choices(chars, k=24))
        self._sid_file.write_text(sid, "utf-8")
        self._sid = sid
        logger.info(f"[catcake] new SID generated")
        return sid

    # ── Session ───────────────────────────────────────────────────────
    def _get_session(self):
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(total=15)
            self._session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self._session

    # ── Server matching ───────────────────────────────────────────────
    def _match_server(self, uid, server):
        uid = str(uid)
        if server == "all":
            return True
        if server == "other":
            return not any(rule(uid) for rule in SERVER_RULES.values())
        rule = SERVER_RULES.get(server)
        return rule(uid) if rule else False

    def _server_tag(self, uid):
        uid = str(uid)
        for code, rule in SERVER_RULES.items():
            if rule(uid):
                return SERVER_LABELS.get(code, code)
        return SERVER_LABELS["other"]

    # ── Query resolution ──────────────────────────────────────────────
    def _resolve_query(self, query):
        q = query.strip()
        if not q:
            return None, "查询词不能为空"
        if q in self.cake_lookup:
            return q, None
        if q in self.char_lookup:
            cakes = self.char_lookup[q]
            if len(cakes) == 1:
                return cakes[0], None
            return None, f"角色「{q}」对应多个猫猫糕：{'、'.join(cakes)}，请指定其中一个"
        cake_matches = [n for n in self.cake_lookup if q in n]
        if len(cake_matches) == 1:
            return cake_matches[0], None
        if len(cake_matches) > 1:
            return None, f"「{q}」匹配到多个猫猫糕：{'、'.join(cake_matches)}，请指定其中一个"
        char_matches = [ch for ch in self.char_lookup if q in ch]
        if len(char_matches) == 1:
            cakes = self.char_lookup[char_matches[0]]
            return cakes[0], None
        if len(char_matches) > 1:
            return None, f"「{q}」匹配到多个角色：{'、'.join(char_matches)}，请指定其中一个"
        return None, f"未找到匹配「{q}」的猫猫糕或角色"

    def _resolve_cake_names(self, queries):
        """Resolve multiple queries to cake names. Returns (names, error)."""
        names = []
        for q in queries:
            q = q.strip()
            if not q:
                continue
            name, err = self._resolve_query(q)
            if err:
                return None, err
            if name in names:
                return None, f"猫猫糕「{name}」重复了"
            names.append(name)
        return names, None

    # ── API calls ─────────────────────────────────────────────────────
    async def _fetch_records(self):
        session = self._get_session()
        try:
            async with session.get(API_URL) as resp:
                if resp.status != 200:
                    logger.error(f"[catcake] API returned {resp.status}")
                    return []
                data = await resp.json(content_type=None)
                return data.get("records", [])
        except Exception as e:
            logger.error(f"[catcake] API fetch error: {e}")
            return []

    async def _api_post(self, payload):
        """POST /api/records to create or update a record."""
        sid = self._get_sid()
        session = self._get_session()
        headers = {
            "Content-Type": "application/json",
            "Cookie": f"hsr_sid={sid}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://catcake.hoshimi.io",
            "Referer": "https://catcake.hoshimi.io/",
        }
        try:
            async with session.post(API_URL, json=payload, headers=headers) as resp:
                data = await resp.json(content_type=None)
                if resp.status not in (200, 201):
                    err = (data or {}).get("error", f"HTTP {resp.status}")
                    raise Exception(err)
                return data.get("record")
        except aiohttp.ClientError as e:
            raise Exception(f"网络错误: {e}")

    async def _api_delete(self, record_id):
        """DELETE /api/records/:id."""
        sid = self._get_sid()
        session = self._get_session()
        headers = {
            "Cookie": f"hsr_sid={sid}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://catcake.hoshimi.io",
            "Referer": "https://catcake.hoshimi.io/",
        }
        try:
            async with session.delete(f"{API_URL}/{record_id}", headers=headers) as resp:
                data = await resp.json(content_type=None)
                if resp.status != 200:
                    err = (data or {}).get("error", f"HTTP {resp.status}")
                    raise Exception(err)
                return True
        except aiohttp.ClientError as e:
            raise Exception(f"网络错误: {e}")

    async def _api_delete(self, record_id):
        """DELETE /api/records/:id."""
        sid = self._get_sid()
        session = self._get_session()
        headers = {"Cookie": f"hsr_sid={sid}"}
        try:
            async with session.delete(f"{API_URL}/{record_id}", headers=headers) as resp:
                data = await resp.json(content_type=None)
                if resp.status != 200:
                    err = (data or {}).get("error", f"HTTP {resp.status}")
                    raise Exception(err)
                return True
        except aiohttp.ClientError as e:
            raise Exception(f"网络错误: {e}")

    # ── Image helpers ─────────────────────────────────────────────────
    async def _download_image(self, url, path):
        session = self._get_session()
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "wb") as f:
                        f.write(data)
                    return True
        except Exception as e:
            logger.warning(f"[catcake] download failed: {url} -> {e}")
        return False

    def _compose_card(self, cake_paths, record_id, tmpdir):
        from PIL import Image

        n = len(cake_paths)
        cell_w = 180
        cake_h = 167
        padding = 8
        gap = 6

        total_w = cell_w * n + gap * (n - 1) + padding * 2
        total_h = cake_h + padding * 2

        canvas = Image.new("RGBA", (total_w, total_h), (255, 255, 255, 255))

        for col, path in enumerate(cake_paths):
            x = padding + col * (cell_w + gap)
            try:
                img = Image.open(path).convert("RGBA")
                orig_w, orig_h = img.size
                scale = cell_w / orig_w
                new_h = int(orig_h * scale)
                img = img.resize((cell_w, new_h), Image.LANCZOS)
                y_off = padding + (cake_h - new_h) // 2
                canvas.paste(img, (x, y_off), img)
            except Exception as e:
                logger.warning(f"[catcake] paste cake failed: {e}")

        out_path = os.path.join(tmpdir, f"card_{record_id}.png")
        canvas.save(out_path, "PNG")
        return out_path

    # ── /找猫糕 ───────────────────────────────────────────────────────
    @filter.command("找猫糕")
    async def find_catcake(self, event: AstrMessageEvent):
        msg = event.message_str.strip()
        parts = msg.split()
        if parts and parts[0] in ("找猫糕", "/找猫糕"):
            parts = parts[1:]

        server_input = self.config.get("default_server", "官服")
        query_input = None

        if len(parts) >= 2:
            first = parts[0]
            svr = SERVER_ALIASES.get(first) or SERVER_ALIASES.get(first.lower())
            if svr:
                server_input = first
                query_input = " ".join(parts[1:])
            else:
                query_input = " ".join(parts)
        elif len(parts) == 1:
            query_input = parts[0]

        if not query_input:
            yield event.plain_result(
                "用法：/找猫糕 <服务器> <角色名/猫猫糕名>\n"
                "例如：\n"
                "  /找猫糕 官服 丹恒\n"
                "  /找猫糕 B服 姬子\n"
                "  /找猫糕 全部 阿基维利\n"
                "  /找猫糕 糯米团  (使用默认服务器)\n\n"
                "可用服务器：官服 B服 亚服 美服 欧服 港澳台 其他 全部"
            )
            return

        server = SERVER_ALIASES.get(server_input)
        if not server:
            server = SERVER_ALIASES.get(server_input.lower())
        if not server:
            yield event.plain_result(f"未知服务器：{server_input}")
            return

        cake_name, err = self._resolve_query(query_input)
        if err:
            yield event.plain_result(err)
            return

        server_label = SERVER_LABELS.get(server, server)
        limit = self.config.get("default_limit", 3)
        send_img = self.config.get("send_images", True)

        yield event.plain_result(f"正在查询 [{server_label}] 的「{cake_name}」...")

        records = await self._fetch_records()
        if not records:
            yield event.plain_result("未能获取猫猫糕数据，请稍后再试。")
            return

        results = []
        for r in records:
            if not self._match_server(r.get("uid", ""), server):
                continue
            if cake_name in r.get("cakes", []):
                results.append(r)
        results.sort(key=lambda r: r.get("createdAt", 0), reverse=True)
        if limit:
            results = results[:limit]

        if not results:
            yield event.plain_result(
                f"在 [{server_label}] 中未找到「{cake_name}」的记录。\n"
                "(记录每周一服务器时间04:00重置)"
            )
            return

        import tempfile
        tmpdir = os.path.join(tempfile.gettempdir(), "astrbot_catcake")
        os.makedirs(tmpdir, exist_ok=True)

        for i, r in enumerate(results, 1):
            tag = self._server_tag(r.get("uid", ""))
            anji_note = " [今日限定]" if r.get("isAnji") else ""
            text = f"{i}. {r['name']}{anji_note} | UID: {r['uid']} | {tag}\n"
            text += f"   猫猫糕：{'、'.join(r['cakes'])}"

            chain = [Plain(text)]
            if send_img:
                cake_paths = []
                for cn in r["cakes"]:
                    cn = (cn or "").strip()
                    if not cn:
                        continue
                    ci = self.cake_lookup.get(cn)
                    if not ci:
                        continue
                    cake_url = BASE_URL + ci["s"]
                    cake_path = os.path.join(tmpdir, f"cake_{r['id']}_{ci['n']}.png")
                    if await self._download_image(cake_url, cake_path):
                        cake_paths.append(cake_path)

                if cake_paths:
                    composite_path = self._compose_card(cake_paths, r["id"], tmpdir)
                    if composite_path:
                        chain.append(Image.fromFileSystem(composite_path))

            yield event.chain_result(chain)

            if i < len(results):
                await asyncio.sleep(0.3)

    # ── /登记猫猫糕 ───────────────────────────────────────────────────
    @filter.command("登记猫猫糕")
    async def register_catcake(self, event: AstrMessageEvent):
        msg = event.message_str.strip()
        parts = msg.split()
        if parts and parts[0] in ("登记猫猫糕", "/登记猫猫糕"):
            parts = parts[1:]

        if len(parts) < 5:
            yield event.plain_result(
                "用法：/登记猫猫糕 <玩家名> <UID> <猫猫糕1> <猫猫糕2> <猫猫糕3>\n"
                "例如：/登记猫猫糕 开拓者 123456789 糯米团 芝麻酥 冰糕\n\n"
                "注：UID为9位数字(官服/B服/美服/欧服/港澳台)\n"
                "    或18开头的10位数字(亚服)"
            )
            return

        player_name = parts[0]
        uid = parts[1]
        cake_queries = parts[2:]

        # Validate UID
        if not re.match(r'^\d{9}$', uid) and not re.match(r'^18\d{8}$', uid):
            yield event.plain_result(
                f"UID「{uid}」格式不正确。UID须为9位数字，或18开头的10位数字。"
            )
            return

        # Validate player name
        if len(player_name) > 20:
            yield event.plain_result("玩家名不能超过20个字符。")
            return

        # Resolve cake names (allow 2-3, since Anji is a separate command)
        if len(cake_queries) < 2 or len(cake_queries) > 3:
            yield event.plain_result("请指定2~3个猫猫糕。登记阿基喵利请使用 /登记阿基喵利。")
            return

        cake_names, err = self._resolve_cake_names(cake_queries)
        if err:
            yield event.plain_result(err)
            return

        if ANJI_CAKE in cake_names:
            yield event.plain_result("阿基喵利只能单独登记，请使用 /登记阿基喵利 命令。")
            return

        # Pad to 3 slots (site expects exactly 3)
        while len(cake_names) < 3:
            cake_names.append("")

        payload = {
            "name": player_name,
            "uid": uid,
            "cakes": cake_names[:3],
            "isAnji": False,
        }

        try:
            record = await self._api_post(payload)
            yield event.plain_result(
                f"登记成功！\n"
                f"玩家：{player_name} | UID: {uid}\n"
                f"猫猫糕：{'、'.join(c for c in cake_names if c)}"
            )
        except Exception as e:
            yield event.plain_result(f"登记失败：{e}")

    # ── /登记阿基喵利 ─────────────────────────────────────────────────
    @filter.command("登记阿基喵利")
    async def register_anji(self, event: AstrMessageEvent):
        msg = event.message_str.strip()
        parts = msg.split()
        if parts and parts[0] in ("登记阿基喵利", "/登记阿基喵利"):
            parts = parts[1:]

        if len(parts) < 2:
            yield event.plain_result(
                "用法：/登记阿基喵利 <玩家名> <UID>\n"
                "例如：/登记阿基喵利 开拓者 123456789\n\n"
                "阿基喵利为今日限定猫猫糕，记录在每天凌晨4:00自动清除。"
            )
            return

        player_name = parts[0]
        uid = parts[1]

        if not re.match(r'^\d{9}$', uid) and not re.match(r'^18\d{8}$', uid):
            yield event.plain_result(
                f"UID「{uid}」格式不正确。UID须为9位数字，或18开头的10位数字。"
            )
            return

        if len(player_name) > 20:
            yield event.plain_result("玩家名不能超过20个字符。")
            return

        payload = {
            "name": player_name,
            "uid": uid,
            "cakes": [ANJI_CAKE, "", ""],
            "isAnji": True,
        }

        try:
            record = await self._api_post(payload)
            yield event.plain_result(
                f"阿基喵利登记成功！\n"
                f"玩家：{player_name} | UID: {uid}\n"
                f"今日限定，凌晨4:00自动清除。"
            )
        except Exception as e:
            yield event.plain_result(f"登记失败：{e}")

    # ── /删除猫猫糕 ───────────────────────────────────────────────────
    @filter.command("删除猫猫糕")
    async def delete_catcake(self, event: AstrMessageEvent):
        msg = event.message_str.strip()
        parts = msg.split()
        if parts and parts[0] in ("删除猫猫糕", "/删除猫猫糕"):
            parts = parts[1:]

        if len(parts) < 1:
            yield event.plain_result(
                "用法：/删除猫猫糕 <UID>\n"
                "例如：/删除猫猫糕 123456789\n\n"
                "只能删除自己登记过的记录。"
            )
            return

        uid = parts[0]
        if not re.match(r'^\d{9}$', uid) and not re.match(r'^18\d{8}$', uid):
            yield event.plain_result(
                f"UID「{uid}」格式不正确。"
            )
            return

        # Fetch records to find our own by UID
        records = await self._fetch_records()
        if not records:
            yield event.plain_result("未能获取数据，请稍后再试。")
            return

        own = [r for r in records if str(r.get("uid", "")) == uid and r.get("mine")]
        if not own:
            yield event.plain_result(
                f"未找到UID「{uid}」的登记记录，或该记录不属于本插件。\n"
                "（只能删除通过本插件登记的记录）"
            )
            return

        record = own[0]
        try:
            await self._api_delete(record["id"])
            is_anji = " [阿基喵利]" if record.get("isAnji") else ""
            yield event.plain_result(
                f"已删除{is_anji}\n"
                f"玩家：{record['name']} | UID: {record['uid']}\n"
                f"猫猫糕：{'、'.join(c for c in record.get('cakes', []) if c)}"
            )
        except Exception as e:
            yield event.plain_result(f"删除失败：{e}")

    async def terminate(self):
        if self._session and not self._session.closed:
            await self._session.close()
