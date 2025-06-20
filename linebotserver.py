from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    JoinEvent,
    StickerMessage,
    TemplateSendMessage,
    MessageAction,
    QuickReply,
    QuickReplyButton,
    ButtonsTemplate,
    ImageMessage,
    FileMessage,
)
import json
import os
import random
import re
import datetime
from linebot.models import QuickReply, QuickReplyButton
import jieba
from collections import Counter

# -*- coding: utf-8 -*-

app = Flask(__name__)

line_bot_api = LineBotApi(
    "o/bUKxlPGA3FzqNC8oscvP2JTMfLijLyTSOyBlqOn+7O8qS7dYmLvylKsxvW122UMu7oI3FXvBeXG2gFisMYJ8H/Ryjy7mfc1MyXNK5SX9VQgAYazOYczx4XyiROCK8qb08flT4QmqM7+62G47+3sQdB04t89/1O/w1cDnyilFU="
)
handler = WebhookHandler("4bf0915e79f18c12d019119189398de9")

INSTRUCTION = (
    "【LineBot 使用說明】\n"
    "指令\\功能說明\n"
    "----------------------\n"
    "設定設定\\查詢/切換 bot 模式\n"
    "閉嘴\\bot 進入靜音模式\n"
    "聊天\\恢復回覆訊息\n"
    "亂說話模式\\啟用跨聊天室回覆\n"
    "乖寶寶模式\\只回本聊天室教的內容\n"
    "學 A B\\教 bot 收到「A」回覆「B」\n"
    "你會說什麼\\查本聊天室教的內容\n"
    "壞壞\\刪除 bot 上次回覆的內容\n"
)
# INSTRUCTION = (
#     "【LineBot 使用說明】\n"
#     "指令\\功能說明\n"
#     "----------------------\n"
#     "設定設定\\查詢/切換 bot 模式\n"
#     "閉嘴\\bot 進入靜音模式\n"
#     "聊天\\恢復回覆訊息\n"
#     "亂說話模式\\啟用跨聊天室回覆\n"
#     "乖寶寶模式\\只回本聊天室教的內容\n"
#     "學 A B\\教 bot 收到「A」回覆「B」\n"
#     "你會說什麼\\查本聊天室教的內容\n"
#     "壞壞\\刪除 bot 上次回覆的內容\n"
#     "統計資料\\查詢個人訊息/貼圖/圖片/文件/連結等統計\n"
#     "我的口頭禪 [年份]\\查詢自己常用詞排行\n"
#     "排行榜\\查詢群組發言排行榜"
# )
commands = [
    "設定設定",
    "閉嘴",
    "聊天",
    "亂說話模式",
    "乖寶寶模式",
    "你會說什麼",
    "壞壞",
    "黃心如怎麼說",
    "全部統計",
    "每小時統計",
    "貼圖統計",
    "統計資料",
    "資料統計",
    "訊息統計",
    "連結統計",
    "圖片統計",
    "文件統計",
    "我的口頭禪",
    "排行榜",
    "說笑話",
    "唱歌",
]
BAN_WORDS = ["洪偉城", "洪偉成", "宏偉成"]


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


SILENT_FILE = "silent_mode.json"
USER_FILE = "user_last_message.json"
LAST_REPLY_FILE = "last_reply.json"
RAGE_FILE = "rage_mode.json"
TEACHER_FILE = "teacher.json"
USER_STATS_FILE = "user_message_stats.json"
USER_MESSAGES_FILE = "user_messages.json"
JOKE_FILE = "joke.json"


# 儲存使用者訊息（依群組和使用者）
def save_user_message(group_id, user_id, message):
    # 不儲存指令
    if message in commands:
        return
    year = str(datetime.datetime.now().year)
    if os.path.exists(USER_MESSAGES_FILE):
        with open(USER_MESSAGES_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}
    if group_id not in data:
        data[group_id] = {}
    if user_id not in data[group_id]:
        data[group_id][user_id] = {}
    if year not in data[group_id][user_id] or not isinstance(
        data[group_id][user_id].get(year), list
    ):
        data[group_id][user_id][year] = []
    data[group_id][user_id][year].append(message)
    with open(USER_MESSAGES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user_top_words(group_id, user_id, year=None, topn=5):
    if not os.path.exists(USER_MESSAGES_FILE):
        return "沒有資料"
    with open(USER_MESSAGES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    user_data = data.get(group_id, {}).get(user_id, {})
    if not user_data:
        return "沒有資料"
    if year is None:
        year = str(datetime.datetime.now().year)
    msgs = user_data.get(year, [])
    if not msgs:
        return "沒有資料"
    # jieba 斷詞
    words = []
    for msg in msgs:
        words += [w for w in jieba.cut(msg) if len(w.strip()) > 1]
    counter = Counter(words)
    most_common = counter.most_common(topn)
    if not most_common:
        return "沒有資料"
    result = f"{year}年你的口頭禪排行：\n"
    # 只顯示前三名
    for idx, (word, count) in enumerate(most_common):
        if idx >= 3:
            break
        result += f"{word}：{count} 次\n"
    return result


# 獲取事件來源的 ID
def get_source_id(event):
    if event.source.type == "user":
        return event.source.user_id
    elif event.source.type == "group":
        return event.source.group_id
    elif event.source.type == "room":
        return event.source.room_id
    else:
        return "unknown"


# 獲取使用者訊息統計（依群組和使用者）
def update_user_message_stats(group_id, user_id, message_type=None, is_link=False):
    now = datetime.datetime.now()
    month_key = now.strftime("%Y-%m")
    hour_key = str(now.hour)
    if os.path.exists(USER_STATS_FILE):
        with open(USER_STATS_FILE, "r", encoding="utf-8") as f:
            try:
                stats = json.load(f)
            except json.JSONDecodeError:
                stats = {}
    else:
        stats = {}
    if group_id not in stats:
        stats[group_id] = {}
    if user_id not in stats[group_id]:
        stats[group_id][user_id] = {"total": 0}
    # 累加總數
    stats[group_id][user_id]["total"] = stats[group_id][user_id].get("total", 0) + 1
    # 累加本月
    stats[group_id][user_id][month_key] = stats[group_id][user_id].get(month_key, 0) + 1
    # 累加每小時
    if "hour_count" not in stats[group_id][user_id]:
        stats[group_id][user_id]["hour_count"] = {}
    stats[group_id][user_id]["hour_count"][hour_key] = (
        stats[group_id][user_id]["hour_count"].get(hour_key, 0) + 1
    )
    # 新增連結、圖片、文件、貼圖統計
    if is_link:
        stats[group_id][user_id]["link_total"] = (
            stats[group_id][user_id].get("link_total", 0) + 1
        )
    if message_type == "image":
        stats[group_id][user_id]["image_total"] = (
            stats[group_id][user_id].get("image_total", 0) + 1
        )
    if message_type == "file":
        stats[group_id][user_id]["file_total"] = (
            stats[group_id][user_id].get("file_total", 0) + 1
        )
    if message_type == "sticker":
        stats[group_id][user_id]["sticker_total"] = (
            stats[group_id][user_id].get("sticker_total", 0) + 1
        )

    with open(USER_STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


# 獲取使用者訊息統計（依群組和使用者）
def get_user_message_stats(group_id, user_id):
    now = datetime.datetime.now()
    month_key = now.strftime("%Y-%m")
    if os.path.exists(USER_STATS_FILE):
        with open(USER_STATS_FILE, "r", encoding="utf-8") as f:
            try:
                stats = json.load(f)
            except json.JSONDecodeError:
                stats = {}
    else:
        stats = {}
    user_stats = stats.get(group_id, {}).get(user_id, {})
    total = user_stats.get("total", 0)
    month = user_stats.get(month_key, 0)
    return total, month


# 設定最後回覆的 key（依群組）
def set_last_reply(source_id, key):
    if os.path.exists(LAST_REPLY_FILE):
        with open(LAST_REPLY_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}
    data[source_id] = {"key": key}
    with open(LAST_REPLY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 獲取最後回覆的 key（依群組）
def get_last_reply(source_id):
    if os.path.exists(LAST_REPLY_FILE):
        with open(LAST_REPLY_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                group_data = data.get(source_id, {})
                return group_data.get("key")
            except json.JSONDecodeError:
                return None
    return None


# 獲取使用者最後的訊息
def get_user_last_message():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


# 設定使用者最後的訊息
def set_user_last_message(user_id, message):
    data = get_user_last_message()
    data[user_id] = message
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 新增：儲存所有使用者最後訊息（用於群組重複訊息清空）
def save_user_last_message(data):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 檢查是否為靜音模式（依群組）
def is_silent(source_id):
    if os.path.exists(SILENT_FILE):
        with open(SILENT_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data.get(source_id, False)
            except json.JSONDecodeError:
                return False
    return False


# 設定靜音模式（依群組）
def set_silent(source_id, silent):
    if os.path.exists(SILENT_FILE):
        with open(SILENT_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}
    data[source_id] = silent
    with open(SILENT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 檢查是否為亂說話模式
def is_rage_mode(source_id):
    if os.path.exists(RAGE_FILE):
        with open(RAGE_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data.get(source_id, False)
            except json.JSONDecodeError:
                return False
    return False


# 設定亂說話模式
def set_rage_mode(source_id, mode):
    if os.path.exists(RAGE_FILE):
        with open(RAGE_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}
    data[source_id] = mode
    with open(RAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 獲取群組發言排行榜
def get_group_message_rank_with_names(group_id):
    with open("user_message_stats.json", "r", encoding="utf-8") as f:
        stats = json.load(f)

    users = stats.get(group_id, {})
    if not users:
        return "查無此群組資料"

    # 排序
    rank = sorted(users.items(), key=lambda x: x[1].get("total", 0), reverse=True)
    result = "發言排行榜：\n"
    for idx, (user_id, data) in enumerate(rank, 1):
        total = data.get("total", 0)
        # 查詢暱稱
        try:
            profile = line_bot_api.get_group_member_profile(group_id, user_id)
            name = profile.display_name
        except Exception:
            name = user_id  # 查不到就顯示 user_id
        result += f"{idx}. {name}：{total} 次\n"
    return result


@handler.add(JoinEvent)
def handle_join(event):
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=INSTRUCTION))


@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker(event):
    user_id = event.source.user_id
    source_id = get_source_id(event)
    # 更新貼圖統計（與圖片、文件統計格式一致）
    update_user_message_stats(source_id, user_id, message_type="sticker")
    # 不回覆


@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    user_id = event.source.user_id
    source_id = get_source_id(event)
    update_user_message_stats(source_id, user_id, message_type="image")
    # 不回覆


@handler.add(MessageEvent, message=FileMessage)
def handle_file(event):
    user_id = event.source.user_id
    source_id = get_source_id(event)
    update_user_message_stats(source_id, user_id, message_type="file")
    # 不回覆


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    user_id = event.source.user_id
    source_id = get_source_id(event)
    # 判斷是否為連結
    is_link = bool(re.match(r"https?://", text.strip()))
    update_user_message_stats(source_id, user_id, is_link=is_link)
    if event.source.type in ["group", "room"]:
        save_user_message(source_id, user_id, text)
    filename = "data.json"
    if text == "設定設定":
        # 取得目前狀態
        rage = is_rage_mode(source_id)
        status = "亂說話模式" if rage else "乖寶寶模式"
        silent = is_silent(source_id)
        silent_status = "靜音模式" if silent else "聊天模式"
        reply_text = f"目前模式：{status}\n目前狀態：{silent_status}"

        template_message = TemplateSendMessage(
            alt_text="設定狀態",
            template=ButtonsTemplate(
                title="模式設定",
                text=reply_text,
                actions=[
                    MessageAction(label="亂說話模式", text="亂說話模式"),
                    MessageAction(label="乖寶寶模式", text="乖寶寶模式"),
                ],
            ),
        )
        line_bot_api.reply_message(event.reply_token, template_message)
        return

    # 處理閉嘴/聊天指令
    if text == "閉嘴":
        if not is_silent(source_id):
            set_silent(source_id, True)
            reply = "好啦 我閉嘴"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
            return
    if text == "聊天":
        if is_silent(source_id):
            reply = "嗚呼 強勢回歸！"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
            set_silent(source_id, False)
            return

    # 若在靜音狀態則不回覆
    if is_silent(source_id):
        return
    # 查詢功能
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                all_data = json.load(f)
            except json.JSONDecodeError:
                all_data = []
    else:
        all_data = []

    if is_rage_mode(source_id):
        # 狂暴模式：查所有聊天室，隨機選一個
        matched_items = [
            item
            for item in all_data
            if re.match(rf"^{re.escape(item.get('key'))} *$", text)
        ]
        if matched_items:
            item = random.choice(matched_items)
            value = item.get("value", "")
            if "/" in value:
                options = [v.strip() for v in value.split("/")]
                reply = random.choice(options)
            else:
                reply = value
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
            set_last_reply(source_id, item.get("key"))
            return
    else:
        # 正常模式：只查本聊天室
        for item in all_data:
            key = item.get("key")
            pattern = rf"^{re.escape(key)} *$"
            if re.match(pattern, text) and item.get("source_id") == source_id:
                value = item.get("value", "")
                if "/" in value:
                    options = [v.strip() for v in value.split("/")]
                    reply = random.choice(options)
                else:
                    reply = value
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(text=reply)
                )
                set_last_reply(source_id, item.get("key"))
                return

    if text == "說笑話":

        if os.path.exists(JOKE_FILE):
            with open(JOKE_FILE, "r", encoding="utf-8") as f:
                try:
                    jokes = json.load(f)
                except json.JSONDecodeError:
                    jokes = []
        else:
            jokes = []
        if jokes:
            joke = random.choice(jokes)
            reply = joke.get("joke", "今天沒有笑話喔！")
        else:
            reply = "今天沒有笑話喔！"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    match = re.match(r"^我的口頭禪(?:\s*(\d{4}))?$", text)
    if event.source.type in ["group", "room"]:
        if match:
            year = match.group(1)
            if not year:
                year = str(datetime.datetime.now().year)
            reply = get_user_top_words(source_id, user_id, year=year)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
            return
    # 處理亂說話模式
    if text == "亂說話模式":
        if is_rage_mode(source_id):
            return  # 已經是亂說話模式就不回話
        set_rage_mode(source_id, True)
        reply = "我忍好久了"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # 處理乖寶寶模式（關閉亂說話模式）
    if text == "乖寶寶模式":
        if not is_rage_mode(source_id):
            return  # 已經不是亂說話模式就不回話
        set_rage_mode(source_id, False)
        reply = "我現在乖的一匹"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    if text == "排行榜":
        if event.source.type == "group":
            group_id = source_id
            rank_text = get_group_message_rank_with_names(group_id)
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=rank_text)
            )
        else:
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text="請在群組中使用本指令")
            )
        return
    if text == "統計資料" or text == "資料統計":
        # 讀取統計資料
        if os.path.exists(USER_STATS_FILE):
            with open(USER_STATS_FILE, "r", encoding="utf-8") as f:
                try:
                    stats = json.load(f)
                except json.JSONDecodeError:
                    stats = {}
        else:
            stats = {}
        user_stats = stats.get(source_id, {}).get(user_id, {})
        total = user_stats.get("total", 0)
        month = user_stats.get(datetime.datetime.now().strftime("%Y-%m"), 0)
        sticker_total = user_stats.get("sticker_total", 0)
        link_total = user_stats.get("link_total", 0)
        image_total = user_stats.get("image_total", 0)
        file_total = user_stats.get("file_total", 0)
        hour_count = user_stats.get("hour_count", {})

        # 組成多頁訊息（CarouselTemplate）
        quick_reply = QuickReply(
            items=[
                QuickReplyButton(
                    action=MessageAction(label="全部統計", text="全部統計")
                ),
                QuickReplyButton(
                    action=MessageAction(label="訊息統計", text="訊息統計")
                ),
                QuickReplyButton(
                    action=MessageAction(label="貼圖統計", text="貼圖統計")
                ),
                QuickReplyButton(
                    action=MessageAction(label="每小時統計", text="每小時統計")
                ),
                QuickReplyButton(
                    action=MessageAction(label="連結統計", text="連結統計")
                ),
                QuickReplyButton(
                    action=MessageAction(label="圖片統計", text="圖片統計")
                ),
                QuickReplyButton(
                    action=MessageAction(label="文件統計", text="文件統計")
                ),
                QuickReplyButton(
                    action=MessageAction(label="我今年的口頭禪", text="我的口頭禪")
                ),
            ]
        )
        reply_text = "請選擇要查詢的統計類型："
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=reply_text, quick_reply=quick_reply)
        )
        return
    if text == "訊息統計":
        if os.path.exists(USER_STATS_FILE):
            with open(USER_STATS_FILE, "r", encoding="utf-8") as f:
                try:
                    stats = json.load(f)
                except json.JSONDecodeError:
                    stats = {}
        else:
            stats = {}
        user_stats = stats.get(source_id, {}).get(user_id, {})
        total = user_stats.get("total", 0)
        month = user_stats.get(datetime.datetime.now().strftime("%Y-%m"), 0)
        reply = f"你在這個群組總共說了 {total} 句話\n本月說了 {month} 句話"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return
    if text == "全部統計":
        if os.path.exists(USER_STATS_FILE):
            with open(USER_STATS_FILE, "r", encoding="utf-8") as f:
                try:
                    stats = json.load(f)
                except json.JSONDecodeError:
                    stats = {}
        else:
            stats = {}
        user_stats = stats.get(source_id, {}).get(user_id, {})
        total = user_stats.get("total", 0)
        month = user_stats.get(datetime.datetime.now().strftime("%Y-%m"), 0)
        sticker_total = user_stats.get("sticker_total", 0)
        link_total = user_stats.get("link_total", 0)
        image_total = user_stats.get("image_total", 0)
        file_total = user_stats.get("file_total", 0)
        hour_count = user_stats.get("hour_count", {})
        now = datetime.datetime.now()
        reply = (
            f"你在這個群組總共說了 {total} 句話\n"
            f"本月({now.strftime('%Y-%m')})說了 {month} 句話\n"
            f"傳過 {sticker_total} 次貼圖\n"
            f"傳過 {link_total} 次連結\n"
            f"傳過 {image_total} 次圖片\n"
            f"傳過 {file_total} 次文件\n"
        )
        if hour_count:
            max_hour = max(hour_count, key=lambda h: hour_count[h])
            max_count = hour_count[max_hour]
            reply += f"你最常在 {max_hour}:00 ~ {int(max_hour)+1}:00 說話（共 {max_count} 句）"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return
    if text == "每小時統計":
        if os.path.exists(USER_STATS_FILE):
            with open(USER_STATS_FILE, "r", encoding="utf-8") as f:
                try:
                    stats = json.load(f)
                except json.JSONDecodeError:
                    stats = {}
        else:
            stats = {}
        user_stats = stats.get(source_id, {}).get(user_id, {})
        hour_count = user_stats.get("hour_count", {})
        if hour_count:
            max_hour = max(hour_count, key=lambda h: hour_count[h])
            max_count = hour_count[max_hour]
            reply = f"你最常在 {max_hour}:00 ~ {int(max_hour)+1}:00 說話（共 {max_count} 句）"
        else:
            reply = "你還沒有說過話喔！"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return
    if text == "連結統計":
        if os.path.exists(USER_STATS_FILE):
            with open(USER_STATS_FILE, "r", encoding="utf-8") as f:
                try:
                    stats = json.load(f)
                except json.JSONDecodeError:
                    stats = {}
        else:
            stats = {}
        user_stats = stats.get(source_id, {}).get(user_id, {})
        link_total = user_stats.get("link_total", 0)
        reply = f"你在這個群組傳過 {link_total} 次連結"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return
    if text == "圖片統計":
        if os.path.exists(USER_STATS_FILE):
            with open(USER_STATS_FILE, "r", encoding="utf-8") as f:
                try:
                    stats = json.load(f)
                except json.JSONDecodeError:
                    stats = {}
        else:
            stats = {}
        user_stats = stats.get(source_id, {}).get(user_id, {})
        image_total = user_stats.get("image_total", 0)
        reply = f"你在這個群組傳過 {image_total} 次圖片"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return
    if text == "文件統計":
        if os.path.exists(USER_STATS_FILE):
            with open(USER_STATS_FILE, "r", encoding="utf-8") as f:
                try:
                    stats = json.load(f)
                except json.JSONDecodeError:
                    stats = {}
        else:
            stats = {}
        user_stats = stats.get(source_id, {}).get(user_id, {})
        file_total = user_stats.get("file_total", 0)
        reply = f"你在這個群組傳過 {file_total} 次文件"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return
    if text == "貼圖統計":
        # 讀取統計資料
        if os.path.exists(USER_STATS_FILE):
            with open(USER_STATS_FILE, "r", encoding="utf-8") as f:
                try:
                    stats = json.load(f)
                except json.JSONDecodeError:
                    stats = {}
        else:
            stats = {}
        user_stats = stats.get(source_id, {}).get(user_id, {})
        sticker_total = user_stats.get("sticker_total", 0)
        reply = f"你在這個群組傳過 {sticker_total} 次貼圖"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    if text.startswith("學 "):
        parts = text.strip().split(maxsplit=2)
        if len(parts) == 3:
            key = parts[1]
            value = parts[2]
            # 禁止學習特定關鍵字
            if key in BAN_WORDS or value in BAN_WORDS:
                reply = "你怎麼敢的啊?"
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(text=reply)
                )
                return
            if key in commands:
                reply = f'你是不是沒看使用說明\n"{key}" 是指令，不能學習'
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(text=reply)
                )
                return
            filename = "data.json"
            # 讀取現有資料
            if os.path.exists(filename):
                with open(filename, "r", encoding="utf-8") as f:
                    try:
                        all_data = json.load(f)
                    except json.JSONDecodeError:
                        all_data = []
            else:
                all_data = []
            # 移除已存在的相同 key 且同一個聊天室
            all_data = [
                item
                for item in all_data
                if not (item.get("key") == key and item.get("source_id") == source_id)
            ]
            # 加入新資料
            all_data.append({"key": key, "value": value, "source_id": source_id})
            # 寫回 json
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            print(f"已學會：{key} = {value} (來源: {source_id})")
            reply = f"好喔 好喔"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        else:
            reply = "格式錯誤，請輸入：學 A B"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
    if text == "你會說什麼":

        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                try:
                    all_data = json.load(f)
                except json.JSONDecodeError:
                    all_data = []
        else:
            all_data = []
        lines = ["這裡教我說\n=============="]
        for item in all_data:
            if item.get("source_id") == source_id:
                lines.append(f"{item.get('key')} ; {item.get('value')}")
        reply = "\n".join(lines)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
    if text == "壞壞":
        last_key = get_last_reply(source_id)
        if last_key:
            # 讀取現有資料
            if os.path.exists(filename):
                with open(filename, "r", encoding="utf-8") as f:
                    try:
                        all_data = json.load(f)
                    except json.JSONDecodeError:
                        all_data = []
            else:
                all_data = []
            # 找到 last_key 並且 source_id 相同的 value
            last_val = None
            for item in all_data:
                if item.get("key") == last_key and item.get("source_id") == source_id:
                    last_val = item.get("value")
                    break
            if not last_val:
                return  # 已經刪除就不回覆
            # 刪除對應 key 且 source_id 相同的資料
            all_data = [
                item
                for item in all_data
                if not (
                    item.get("key") == last_key and item.get("source_id") == source_id
                )
            ]
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            # 回覆 value
            reply = f"下次不說{last_val}了"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return
    if text == "黃心如怎麼說":
        teacher_file = TEACHER_FILE
        if os.path.exists(teacher_file):
            with open(teacher_file, "r", encoding="utf-8") as f:
                teacher_data = json.load(f)
                phrases = teacher_data.get("phrases", [])
                reply = random.choice(phrases)
        else:
            reply = "老師今天沒話說～"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # 跟風模式
    if not (text.startswith("學 ") or text in commands):
        user_last = get_user_last_message()
        current_key = f"{source_id}:{user_id}"

        # 取得同一個群組內所有人的最後訊息
        group_user_keys = [k for k in user_last if k.startswith(f"{source_id}:")]

        # 找出這個群組的上一句話（不包含自己）
        last_other_user_key = None
        last_other_user_text = None
        # 依照寫入順序找最後一個不是自己的 key
        for k in reversed(list(user_last.keys())):
            if k.startswith(f"{source_id}:") and k != current_key:
                last_other_user_key = k
                last_other_user_text = user_last[k]
                break

        # 如果上一句是不同人說的，且內容和自己這句一樣，才跟風
        if last_other_user_text == text and last_other_user_key is not None:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=text))
            # 清空這個群組所有人的紀錄
            for k in group_user_keys:
                del user_last[k]
            save_user_last_message(user_last)
            return

        # 正常記錄這個人的訊息
        set_user_last_message(current_key, text)


if __name__ == "__main__":
    app.run(port=5000, debug=True)
