from __future__ import annotations

import re
from typing import Any

# 日志对象：用于记录渲染链路的调试信息（主要使用 DEBUG）。
from astrbot.api import logger

# 配置读取工具：统一处理类型转换和默认值。
from ..utils.config_parser import get_bool_value, get_int_value, get_text_value

# 时间格式化工具：把 ISO 时间转换为本地可读格式。
from ..utils.time_formatter import format_time_text

# ===== 上游前端风格复刻：描述映射与标题模板 =====
# 参考：packages/frontend/src/lib/app-descriptions.ts

DEFAULT_DESCRIPTION = "正在忙别的喵~"

# 这些值常见于占位或无效上报，不适合直接展示给用户。
APP_PLACEHOLDER_VALUES = {
    "",
    "unknown",
    "android",
    "windows",
    "macos",
    "linux",
    "ios",
    "iphone",
    "ipad",
    "null",
    "none",
}

DISPLAY_TITLE_PLACEHOLDER_VALUES = {
    "",
    "unknown",
    "android",
    "windows",
    "macos",
    "linux",
    "null",
    "none",
}

# 音乐应用名集合（小写）—— 与上游前端同用途：避免描述与音乐行重复。
MUSIC_APP_NAMES = {
    "spotify",
    "网易云音乐",
    "qq音乐",
    "酷狗音乐",
    "apple music",
    "foobar2000",
    "youtube music",
    "酷我音乐",
    "amazon music",
    "aimp",
    "musicbee",
    "vlc",
    "potplayer",
    "windows media player",
}

# 描述映射（全量复刻上游最新 app-descriptions.ts）。
APP_DESCRIPTIONS: dict[str, str] = {
    # 即时通讯
    "Telegram": "正在TG上冲浪喵~",
    "QQ": "正在QQ上水群喵~",
    "TIM": "正在TIM上水群喵~",
    "微信": "正在微信上聊天喵~",
    "WeChat": "正在微信上聊天喵~",
    "Discord": "正在Discord灌水喵~",
    "Line": "正在Line上聊天喵~",
    "企业微信": "正在企业微信办公喵~",
    "钉钉": "正在钉钉办公喵~",
    "Skype": "正在Skype上聊天喵~",
    "飞书": "正在飞书办公喵~",
    "Lark": "正在飞书办公喵~",
    "Slack": "正在Slack摸鱼喵~",
    # AI 助手
    "ChatGPT": "正在和ChatGPT对话喵~",
    "Claude": "正在和Claude对话喵~",
    "Gemini": "正在和Gemini对话喵~",
    "Copilot": "正在和Copilot对话喵~",
    "Microsoft Copilot": "正在和Copilot对话喵~",
    "通义千问": "正在和通义千问对话喵~",
    "文心一言": "正在和文心一言对话喵~",
    "Kimi": "正在和Kimi对话喵~",
    "豆包": "正在和豆包对话喵~",
    "DeepSeek": "正在和DeepSeek对话喵~",
    "Poe": "正在Poe上和AI对话喵~",
    "Perplexity": "正在用Perplexity搜索喵~",
    "HuggingChat": "正在和HuggingChat对话喵~",
    "Ollama": "正在本地跑AI模型喵~",
    "LM Studio": "正在本地跑AI模型喵~",
    # 浏览器
    "Microsoft Edge": "正在用Edge网上冲浪喵~",
    "Google Chrome": "正在用Chrome网上冲浪喵~",
    "Chrome": "正在用Chrome网上冲浪喵~",
    "Firefox": "正在用Firefox网上冲浪喵~",
    "Safari": "正在用Safari网上冲浪喵~",
    "Opera": "正在用Opera网上冲浪喵~",
    "Arc": "正在用Arc网上冲浪喵~",
    "Brave": "正在用Brave网上冲浪喵~",
    "Vivaldi": "正在用Vivaldi网上冲浪喵~",
    "Opera GX": "正在用Opera GX网上冲浪喵~",
    # 代码编辑器
    "VS Code": "正在用VS Code疯狂写bug喵~",
    "Visual Studio Code": "正在用VS Code疯狂写bug喵~",
    "Visual Studio": "正在用VS写代码喵~",
    "IntelliJ IDEA": "正在用IDEA写代码喵~",
    "PyCharm": "正在用PyCharm写代码喵~",
    "WebStorm": "正在用WebStorm写代码喵~",
    "GoLand": "正在用GoLand写代码喵~",
    "JetBrains Rider": "正在用Rider写代码喵~",
    "DataGrip": "正在用DataGrip查数据库喵~",
    "Android Studio": "正在用Android Studio写代码喵~",
    "Cursor": "正在用Cursor疯狂写bug喵~",
    "Sublime Text": "正在用Sublime写代码喵~",
    "Google Antigravity": "正在用Antigravity让AI帮忙写代码喵~",
    "Windsurf": "正在用Windsurf写代码喵~",
    "Zed": "正在用Zed写代码喵~",
    "CLion": "正在用CLion写C++喵~",
    "RustRover": "正在用RustRover写Rust喵~",
    "JetBrains Fleet": "正在用Fleet写代码喵~",
    "HBuilderX": "正在用HBuilderX写前端喵~",
    "Vim": "正在用Vim写代码喵~",
    "Neovim": "正在用Neovim写代码喵~",
    "Emacs": "正在用Emacs写代码喵~",
    "Notepad++": "正在用Notepad++写代码喵~",
    # 开发工具
    "Docker Desktop": "正在用Docker搞容器喵~",
    "GitHub Desktop": "正在用GitHub Desktop管理代码喵~",
    "Postman": "正在用Postman调接口喵~",
    "DBeaver": "正在用DBeaver查数据库喵~",
    "Navicat": "正在用Navicat查数据库喵~",
    "Insomnia": "正在用Insomnia调接口喵~",
    "Wireshark": "正在用Wireshark抓包喵~",
    "Fiddler": "正在用Fiddler抓包喵~",
    "Charles Proxy": "正在用Charles抓包喵~",
    "GitKraken": "正在用GitKraken管理代码喵~",
    "Sourcetree": "正在用Sourcetree管理代码喵~",
    # 设计工具
    "Figma": "正在用Figma做设计喵~",
    "Sketch": "正在用Sketch做设计喵~",
    "Photoshop": "正在用Photoshop修图喵~",
    "Adobe Photoshop": "正在用Photoshop修图喵~",
    "Illustrator": "正在用Illustrator画矢量图喵~",
    "Adobe Illustrator": "正在用Illustrator画矢量图喵~",
    "Premiere Pro": "正在用Premiere剪视频喵~",
    "Adobe Premiere Pro": "正在用Premiere剪视频喵~",
    "After Effects": "正在用AE做特效喵~",
    "Adobe After Effects": "正在用AE做特效喵~",
    "Blender": "正在用Blender搞3D喵~",
    "Cinema 4D": "正在用C4D搞3D喵~",
    "GIMP": "正在用GIMP修图喵~",
    "Canva": "正在用Canva做设计喵~",
    "Adobe XD": "正在用XD做原型喵~",
    "DaVinci Resolve": "正在用达芬奇剪视频喵~",
    "剪映": "正在用剪映剪视频喵~",
    "CapCut": "正在用剪映剪视频喵~",
    "Lightroom": "正在用Lightroom修照片喵~",
    "Adobe Lightroom": "正在用Lightroom修照片喵~",
    "InDesign": "正在用InDesign排版喵~",
    "Adobe InDesign": "正在用InDesign排版喵~",
    "Affinity Photo": "正在用Affinity修图喵~",
    "Affinity Designer": "正在用Affinity做设计喵~",
    "Pixelmator": "正在用Pixelmator修图喵~",
    "Paint.NET": "正在用Paint.NET画图喵~",
    "SAI": "正在用SAI画画喵~",
    "Clip Studio Paint": "正在用CSP画画喵~",
    "MediBang": "正在用MediBang画画喵~",
    "Krita": "正在用Krita画画喵~",
    # 文件管理
    "文件资源管理器": "正在翻文件夹找东西喵~",
    "File Explorer": "正在翻文件夹找东西喵~",
    "文件管理": "正在翻文件夹找东西喵~",
    "Finder": "正在翻文件夹找东西喵~",
    "Total Commander": "正在翻文件夹找东西喵~",
    # 终端
    "Windows Terminal": "正在用命令行敲命令喵~",
    "终端": "正在用命令行敲命令喵~",
    "Terminal": "正在用命令行敲命令喵~",
    "PowerShell": "正在用命令行敲命令喵~",
    "命令提示符": "正在用命令行敲命令喵~",
    "Command Prompt": "正在用命令行敲命令喵~",
    "iTerm2": "正在用命令行敲命令喵~",
    "Termux": "正在Termux里搞事情喵~",
    "Alacritty": "正在用命令行敲命令喵~",
    "Warp": "正在用Warp敲命令喵~",
    "Kitty": "正在用命令行敲命令喵~",
    # 视频
    "哔哩哔哩": "正在B站划水摸鱼喵~",
    "bilibili": "正在B站划水摸鱼喵~",
    "YouTube": "正在YouTube看视频喵~",
    "Netflix": "正在Netflix追剧喵~",
    "爱奇艺": "正在爱奇艺追剧喵~",
    "优酷": "正在优酷追剧喵~",
    "腾讯视频": "正在腾讯视频追剧喵~",
    "VLC": "正在用VLC看视频喵~",
    "PotPlayer": "正在用PotPlayer看视频喵~",
    "mpv": "正在用mpv看视频喵~",
    "Twitch": "正在Twitch看直播喵~",
    "Disney+": "正在Disney+追剧喵~",
    "芒果TV": "正在芒果TV追剧喵~",
    "斗鱼": "正在斗鱼看直播喵~",
    "虎牙": "正在虎牙看直播喵~",
    "Prime Video": "正在Prime Video追剧喵~",
    "HBO": "正在HBO追剧喵~",
    # 音乐
    "Spotify": "正在Spotify听歌喵~",
    "网易云音乐": "正在网易云听歌喵~",
    "QQ音乐": "正在QQ音乐听歌喵~",
    "酷狗音乐": "正在酷狗听歌喵~",
    "Apple Music": "正在Apple Music听歌喵~",
    "foobar2000": "正在用foobar2000听歌喵~",
    "YouTube Music": "正在YouTube Music听歌喵~",
    "酷我音乐": "正在酷我听歌喵~",
    "Amazon Music": "正在Amazon Music听歌喵~",
    "AIMP": "正在用AIMP听歌喵~",
    "Audacity": "正在用Audacity编辑音频喵~",
    # 游戏
    "Steam": "正在Steam玩游戏喵~",
    "Epic Games": "正在Epic玩游戏喵~",
    "Genshin Impact": "正在提瓦特冒险喵~",
    "原神": "正在提瓦特冒险喵~",
    "League of Legends": "正在峡谷激战喵~",
    "英雄联盟": "正在峡谷激战喵~",
    "Honkai: Star Rail": "正在星穹铁道开拓喵~",
    "崩坏：星穹铁道": "正在星穹铁道开拓喵~",
    "Minecraft": "正在Minecraft挖矿喵~",
    "王者荣耀": "正在王者峡谷激战喵~",
    "和平精英": "正在吃鸡喵~",
    "VALORANT": "正在VALORANT对枪喵~",
    "Counter-Strike 2": "正在CS2对枪喵~",
    "CSGO": "正在CSGO对枪喵~",
    "Overwatch": "正在守望先锋战斗喵~",
    "Apex Legends": "正在Apex大逃杀喵~",
    "Elden Ring": "正在交界地冒险喵~",
    "Zelda": "正在海拉鲁冒险喵~",
    "Roblox": "正在Roblox玩喵~",
    "GOG Galaxy": "正在GOG玩游戏喵~",
    "Xbox": "正在Xbox玩游戏喵~",
    "EA App": "正在EA玩游戏喵~",
    "Ubisoft Connect": "正在育碧玩游戏喵~",
    "Battle.net": "正在暴雪玩游戏喵~",
    "明日方舟": "正在罗德岛指挥作战喵~",
    "Arknights": "正在罗德岛指挥作战喵~",
    "绝区零": "正在绝区零战斗喵~",
    "鸣潮": "正在鸣潮冒险喵~",
    # Galgame / 视觉小说
    "いろとりどりのセカイ": "正在攻略gal喵~",
    "五彩斑斓的世界": "正在攻略gal喵~",
    "FAVORITE": "正在攻略gal喵~",
    "ものべの": "正在攻略gal喵~",
    "CLANNAD": "正在攻略gal喵~",
    "Fate/stay night": "正在攻略gal喵~",
    "Summer Pockets": "正在攻略gal喵~",
    "サマーポケッツ": "正在攻略gal喵~",
    "Doki Doki Literature Club": "正在攻略gal喵~",
    "WHITE ALBUM 2": "正在攻略gal喵~",
    "千恋＊万花": "正在攻略gal喵~",
    "Making*Lovers": "正在攻略gal喵~",
    "Sabbat of the Witch": "正在攻略gal喵~",
    "サノバウィッチ": "正在攻略gal喵~",
    "Riddle Joker": "正在攻略gal喵~",
    "喫茶ステラと死神の蝶": "正在攻略gal喵~",
    "Kirikiri": "正在攻略gal喵~",
    "KiriKiri": "正在攻略gal喵~",
    "BGI": "正在攻略gal喵~",
    "SiglusEngine": "正在攻略gal喵~",
    "Ethornell": "正在攻略gal喵~",
    "CatSystem2": "正在攻略gal喵~",
    # 办公效率
    "Word": "正在用Word写文档喵~",
    "Microsoft Word": "正在用Word写文档喵~",
    "Excel": "正在用Excel算数据喵~",
    "Microsoft Excel": "正在用Excel算数据喵~",
    "PowerPoint": "正在做PPT喵~",
    "Microsoft PowerPoint": "正在做PPT喵~",
    "OneNote": "正在用OneNote记笔记喵~",
    "Notion": "正在用Notion记笔记喵~",
    "Obsidian": "正在用Obsidian记笔记喵~",
    "Typora": "正在用Typora记笔记喵~",
    "记事本": "正在用记事本写东西喵~",
    "WPS Office": "正在用WPS办公喵~",
    "WPS": "正在用WPS办公喵~",
    "Google Docs": "正在用Google文档写东西喵~",
    "Google Sheets": "正在用Google表格算数据喵~",
    "Google Slides": "正在用Google幻灯片做PPT喵~",
    "Trello": "正在用Trello管理任务喵~",
    "Todoist": "正在用Todoist管理待办喵~",
    "Logseq": "正在用Logseq记笔记喵~",
    "印象笔记": "正在用印象笔记记东西喵~",
    "Evernote": "正在用印象笔记记东西喵~",
    # 阅读 / 电子书
    "Kindle": "正在Kindle看书喵~",
    "微信读书": "正在微信读书看书喵~",
    "多看阅读": "正在多看阅读看书喵~",
    "Apple Books": "正在看书喵~",
    "Calibre": "正在用Calibre看书喵~",
    # 社交 / 资讯
    "Twitter": "正在刷推特喵~",
    "X": "正在刷推特喵~",
    "微博": "正在微博吃瓜喵~",
    "小红书": "正在逛小红书喵~",
    "抖音": "正在刷短视频喵~",
    "TikTok": "正在刷短视频喵~",
    "知乎": "正在知乎涨知识喵~",
    "今日头条": "正在刷今日头条喵~",
    "Reddit": "正在Reddit冲浪喵~",
    "GitHub": "正在GitHub摸鱼喵~",
    "酷安": "正在酷安逛帖子喵~",
    "百度": "正在百度搜东西喵~",
    "Instagram": "正在刷Instagram喵~",
    "Facebook": "正在逛Facebook喵~",
    "Pinterest": "正在Pinterest找灵感喵~",
    "Threads": "正在刷Threads喵~",
    "快手": "正在刷快手喵~",
    "B站漫画": "正在B站看漫画喵~",
    # 代理工具
    "Mihomo Party": "正在调代理设置喵~",
    "Clash": "正在调代理设置喵~",
    "Clash Verge": "正在调代理设置喵~",
    "v2rayN": "正在调代理设置喵~",
    "Shadowrocket": "正在调代理设置喵~",
    "Quantumult": "正在调代理设置喵~",
    "Surge": "正在调代理设置喵~",
    "NekoBox": "正在调代理设置喵~",
    # 下载 / 传输
    "qBittorrent": "正在下载东西喵~",
    "µTorrent": "正在下载东西喵~",
    "BitComet": "正在下载东西喵~",
    "迅雷": "正在用迅雷下载喵~",
    "IDM": "正在用IDM下载喵~",
    "Internet Download Manager": "正在用IDM下载喵~",
    "Motrix": "正在下载东西喵~",
    "Free Download Manager": "正在下载东西喵~",
    # 云存储
    "Google Drive": "正在用Google云端硬盘喵~",
    "OneDrive": "正在用OneDrive同步文件喵~",
    "百度网盘": "正在用百度网盘喵~",
    "阿里云盘": "正在用阿里云盘喵~",
    "Dropbox": "正在用Dropbox同步文件喵~",
    # 远程 / 会议
    "TeamViewer": "正在远程控制喵~",
    "ToDesk": "正在远程控制喵~",
    "向日葵": "正在远程控制喵~",
    "腾讯会议": "正在开会喵~",
    "Zoom": "正在开会喵~",
    "Microsoft Teams": "正在用Teams开会喵~",
    "Google Meet": "正在开会喵~",
    "钉钉会议": "正在开会喵~",
    "飞书会议": "正在开会喵~",
    # 系统
    "任务管理器": "正在看任务管理器喵~",
    "Task Manager": "正在看任务管理器喵~",
    "系统设置": "正在调系统设置喵~",
    "设置": "正在调设置喵~",
    "Settings": "正在调设置喵~",
    "小米设置": "正在调手机设置喵~",
    "搜索": "正在搜索东西喵~",
    "输入法": "正在打字喵~",
    "画图": "正在画画喵~",
    "UWP 应用": "正在用UWP应用喵~",
    "系统 Shell": "在系统界面喵~",
    "系统界面": "在系统界面喵~",
    "控制面板": "正在调系统设置喵~",
    "Control Panel": "正在调系统设置喵~",
    # Android 特殊项
    "android": "当前手机在线喵~",
    # 购物 / 生活服务
    "支付宝": "正在用支付宝喵~",
    "淘宝": "正在逛淘宝剁手喵~",
    "京东": "正在逛京东剁手喵~",
    "拼多多": "正在拼多多砍一刀喵~",
    "唯品会": "正在唯品会逛特卖喵~",
    "美团": "正在美团点外卖喵~",
    "饿了么": "正在饿了么点外卖喵~",
    "大众点评": "正在大众点评找好吃的喵~",
    "小米应用商店": "正在逛应用商店喵~",
    "闲鱼": "正在逛闲鱼淘二手喵~",
    "Google Play": "正在逛应用商店喵~",
    "App Store": "正在逛应用商店喵~",
    # 出行
    "铁路12306": "正在12306买火车票喵~",
    "携程": "正在携程订行程喵~",
    "百度地图": "正在看地图喵~",
    "高德地图": "正在看地图喵~",
    "Google Maps": "正在看地图喵~",
    "滴滴出行": "正在叫车喵~",
    "飞猪": "正在飞猪订行程喵~",
}

# 有 display_title 时优先套用模板（全量复刻上游）。
TITLE_TEMPLATES: list[tuple[tuple[str, ...], str]] = [
    # 视频应用
    (("YouTube",), "正在YouTube看「{title}」喵~"),
    (("哔哩哔哩", "bilibili"), "正在B站看「{title}」喵~"),
    (("Netflix",), "正在Netflix看「{title}」喵~"),
    (("爱奇艺",), "正在爱奇艺看「{title}」喵~"),
    (("优酷",), "正在优酷看「{title}」喵~"),
    (("腾讯视频",), "正在腾讯视频看「{title}」喵~"),
    (("VLC", "PotPlayer", "mpv"), "正在看「{title}」喵~"),
    (("Twitch",), "正在Twitch看「{title}」喵~"),
    (("Disney+",), "正在Disney+看「{title}」喵~"),
    (("芒果TV",), "正在芒果TV看「{title}」喵~"),
    (("斗鱼",), "正在斗鱼看「{title}」喵~"),
    (("虎牙",), "正在虎牙看「{title}」喵~"),
    (("Prime Video",), "正在Prime Video看「{title}」喵~"),
    (("HBO",), "正在HBO看「{title}」喵~"),
    # 音乐应用
    (("Spotify",), "正在Spotify听「{title}」喵~"),
    (("网易云音乐",), "正在网易云听「{title}」喵~"),
    (("QQ音乐",), "正在QQ音乐听「{title}」喵~"),
    (("酷狗音乐",), "正在酷狗听「{title}」喵~"),
    (("Apple Music",), "正在Apple Music听「{title}」喵~"),
    (("foobar2000",), "正在听「{title}」喵~"),
    (("YouTube Music",), "正在YouTube Music听「{title}」喵~"),
    (("酷我音乐",), "正在酷我听「{title}」喵~"),
    (("Amazon Music",), "正在Amazon Music听「{title}」喵~"),
    (("AIMP",), "正在听「{title}」喵~"),
    # IDE / 编辑器
    (("VS Code", "Visual Studio Code"), "正在用VS Code写「{title}」喵~"),
    (("Cursor",), "正在用Cursor写「{title}」喵~"),
    (("IntelliJ IDEA",), "正在用IDEA写「{title}」喵~"),
    (
        (
            "PyCharm",
            "WebStorm",
            "GoLand",
            "JetBrains Rider",
            "DataGrip",
            "Android Studio",
        ),
        "正在写「{title}」喵~",
    ),
    (("Sublime Text",), "正在用Sublime写「{title}」喵~"),
    (("Visual Studio",), "正在用VS写「{title}」喵~"),
    (("Google Antigravity",), "正在用Antigravity写「{title}」喵~"),
    (("Windsurf",), "正在用Windsurf写「{title}」喵~"),
    (("Zed",), "正在用Zed写「{title}」喵~"),
    (("CLion", "RustRover", "JetBrains Fleet", "HBuilderX"), "正在写「{title}」喵~"),
    (("Vim", "Neovim"), "正在用Vim写「{title}」喵~"),
    (("Emacs",), "正在用Emacs写「{title}」喵~"),
    (("Notepad++",), "正在用Notepad++写「{title}」喵~"),
    # 开发工具
    (("Docker Desktop",), "正在用Docker搞「{title}」喵~"),
    (("GitHub Desktop",), "正在GitHub上搞「{title}」喵~"),
    (("Postman",), "正在用Postman调「{title}」喵~"),
    (("DBeaver", "Navicat"), "正在查「{title}」数据库喵~"),
    (("Insomnia",), "正在用Insomnia调「{title}」喵~"),
    (("GitKraken",), "正在用GitKraken搞「{title}」喵~"),
    (("Sourcetree",), "正在用Sourcetree搞「{title}」喵~"),
    # 游戏平台
    (("Epic Games",), "正在Epic玩「{title}」喵~"),
    (("GOG Galaxy",), "正在GOG玩「{title}」喵~"),
    (("Xbox",), "正在Xbox玩「{title}」喵~"),
    (("EA App",), "正在EA玩「{title}」喵~"),
    (("Ubisoft Connect",), "正在育碧玩「{title}」喵~"),
    (("Battle.net",), "正在暴雪玩「{title}」喵~"),
    # Galgame 引擎
    (
        (
            "Kirikiri",
            "KiriKiri",
            "BGI",
            "SiglusEngine",
            "Ethornell",
            "CatSystem2",
            "いろとりどりのセカイ",
            "五彩斑斓的世界",
            "FAVORITE",
            "ものべの",
            "CLANNAD",
            "Fate/stay night",
            "Summer Pockets",
            "サマーポケッツ",
            "Doki Doki Literature Club",
            "WHITE ALBUM 2",
            "千恋＊万花",
            "Making*Lovers",
            "Sabbat of the Witch",
            "サノバウィッチ",
            "Riddle Joker",
            "喫茶ステラと死神の蝶",
        ),
        "正在攻略「{title}」喵~",
    ),
    # 办公效率
    (("Word", "Microsoft Word"), "正在用Word写「{title}」喵~"),
    (("Excel", "Microsoft Excel"), "正在用Excel看「{title}」喵~"),
    (("PowerPoint", "Microsoft PowerPoint"), "正在做「{title}」PPT喵~"),
    (("OneNote",), "正在OneNote写「{title}」喵~"),
    (("Notion",), "正在Notion看「{title}」喵~"),
    (("Obsidian",), "正在Obsidian写「{title}」喵~"),
    (("Typora",), "正在Typora写「{title}」喵~"),
    (("WPS Office", "WPS"), "正在用WPS写「{title}」喵~"),
    (("Google Docs",), "正在Google文档写「{title}」喵~"),
    (("Logseq",), "正在Logseq写「{title}」喵~"),
    # 设计
    (("Figma",), "正在用Figma做「{title}」喵~"),
    (("Photoshop", "Adobe Photoshop"), "正在用Photoshop修「{title}」喵~"),
    (("Illustrator", "Adobe Illustrator"), "正在用Illustrator画「{title}」喵~"),
    (("Premiere Pro", "Adobe Premiere Pro"), "正在用Premiere剪「{title}」喵~"),
    (("After Effects", "Adobe After Effects"), "正在用AE做「{title}」喵~"),
    (("Blender",), "正在用Blender搞「{title}」喵~"),
    (("DaVinci Resolve",), "正在用达芬奇剪「{title}」喵~"),
    (("剪映", "CapCut"), "正在用剪映剪「{title}」喵~"),
    (("Lightroom", "Adobe Lightroom"), "正在用Lightroom修「{title}」喵~"),
    (("SAI", "Clip Studio Paint", "MediBang", "Krita"), "正在画「{title}」喵~"),
    # 阅读
    (("Kindle",), "正在Kindle看「{title}」喵~"),
    (("微信读书",), "正在微信读书看「{title}」喵~"),
    # 浏览器
    (("Google Chrome", "Chrome"), "正在用Chrome看「{title}」喵~"),
    (("Microsoft Edge",), "正在用Edge看「{title}」喵~"),
    (("Firefox",), "正在用Firefox看「{title}」喵~"),
    (("Safari", "Opera", "Arc"), "正在看「{title}」喵~"),
    (("Brave",), "正在用Brave看「{title}」喵~"),
    (("Vivaldi",), "正在用Vivaldi看「{title}」喵~"),
]

APP_DESCRIPTIONS_LOWER = {k.lower(): v for k, v in APP_DESCRIPTIONS.items()}
TITLE_TEMPLATES_LOWER: dict[str, str] = {}
for names, template in TITLE_TEMPLATES:
    for name in names:
        TITLE_TEMPLATES_LOWER[name.lower()] = template


def _is_online(device_item: dict[str, Any]) -> bool:
    """判断设备是否在线。

    兼容场景：
    - bool: True / False
    - int: 1 / 0
    - str: "1" / "true" / "True"
    """
    value = device_item.get("is_online", 0)

    # 布尔值直接返回。
    if isinstance(value, bool):
        return value
    # 数值按 1 表示在线。
    if isinstance(value, int):
        return value == 1
    # 字符串做兼容解析。
    if isinstance(value, str):
        return value.strip() in {"1", "true", "True"}

    # 其他未知类型默认按离线处理（保守策略）。
    return False


def _clean_text(value: Any) -> str:
    """安全转字符串并去除首尾空白。"""
    if value is None:
        return ""
    return str(value).strip()


def _is_app_placeholder(app_name: str) -> bool:
    """判断 app_name 是否为占位值。"""
    return app_name.strip().lower() in APP_PLACEHOLDER_VALUES


def _normalize_display_title(display_title: str, app_name: str) -> str:
    """清理 display_title 占位值与重复值。"""
    title = display_title.strip()
    if not title:
        return ""

    lower_title = title.lower()
    if lower_title in DISPLAY_TITLE_PLACEHOLDER_VALUES:
        return ""

    app_clean = app_name.strip()
    if app_clean and lower_title == app_clean.lower():
        return ""

    return title


def _friendly_app_name(app_name: str) -> str:
    """用于“应用：”字段的友好展示值。"""
    name = app_name.strip()
    if not name:
        return "未识别应用"
    if _is_app_placeholder(name):
        return "未识别应用"
    return name


def _format_battery(extra_data: dict[str, Any]) -> str:
    """格式化电量文本。"""
    battery_percent = extra_data.get("battery_percent")
    battery_charging = extra_data.get("battery_charging")

    # 无有效电量数值时返回默认说明，保证字段稳定。
    if not isinstance(battery_percent, (int, float)):
        return "未知"

    # 电量百分比统一取整展示。
    percent_text = f"{round(float(battery_percent))}%"

    # 若上报了充电状态，则附加“充电中/未充电”。
    if isinstance(battery_charging, bool):
        return f"{percent_text} {'⚡充电中' if battery_charging else '未充电'}"

    return percent_text


def _extract_music(extra_data: dict[str, Any]) -> dict[str, str]:
    """抽取并规整音乐信息。"""
    music_data = extra_data.get("music")
    if not isinstance(music_data, dict):
        return {}

    return {
        "title": _clean_text(music_data.get("title")),
        "artist": _clean_text(music_data.get("artist")),
        "app": _clean_text(music_data.get("app")),
    }


def _format_music(extra_data: dict[str, Any]) -> str:
    """格式化音乐信息文本。"""
    music_data = _extract_music(extra_data)
    title_text = music_data.get("title", "")
    artist_text = music_data.get("artist", "")
    app_text = music_data.get("app", "")

    # 三项都为空则返回默认说明，保证字段稳定。
    if not any([title_text, artist_text, app_text]):
        return "暂无播放"

    # 优先组合为“歌手 - 歌名”。
    core_text = ""
    if title_text and artist_text:
        core_text = f"{artist_text} - {title_text}"
    else:
        core_text = title_text or artist_text or ""

    # 若包含播放器名，按“核心文本 (播放器)”展示。
    if app_text:
        if core_text:
            return f"{core_text} ({app_text})"
        return app_text

    return core_text


def _steam_title_to_description(display_title: str) -> str:
    """复刻上游 Steam 模板的特殊判断逻辑。"""
    title_lower = display_title.lower()

    if title_lower in {"steam", ""}:
        return "正在浏览 Steam 喵~"
    if title_lower == "好友列表":
        return "正在与 Steam 好友聊天喵~"
    if re.match(r"^[0-9a-f]{20,}$", display_title, flags=re.IGNORECASE):
        return "正在浏览 Steam 喵~"
    if (
        len(display_title) <= 20
        and " " not in display_title
        and not re.search(r"[a-z]{3,}", display_title, flags=re.IGNORECASE)
    ):
        return "正在与 Steam 好友聊天喵~"

    return f"正在Steam玩「{display_title}」喵~"


def _build_activity_description(
    app_name: str, display_title: str, extra_data: dict[str, Any]
) -> str:
    """复刻上游 getAppDescription 核心逻辑（Python 版）。"""
    cleaned_app = app_name.strip()
    cleaned_title = _normalize_display_title(display_title, cleaned_app)

    if not cleaned_app:
        return DEFAULT_DESCRIPTION

    app_lower = cleaned_app.lower()

    if app_lower == "idle":
        return "暂时离开了喵~"

    music_data = _extract_music(extra_data)
    is_music_app_foreground = app_lower in MUSIC_APP_NAMES

    base_text = ""

    # 若有 display_title，优先使用模板；但音乐应用且有 music.title 时跳过模板，避免与 ♪ 信息重复。
    if cleaned_title and not (is_music_app_foreground and music_data.get("title")):
        if app_lower == "steam":
            base_text = _steam_title_to_description(cleaned_title)
        else:
            template = TITLE_TEMPLATES_LOWER.get(app_lower)
            if template:
                base_text = template.format(title=cleaned_title)

    # 未命中模板时走描述映射。
    if not base_text:
        mapped = APP_DESCRIPTIONS_LOWER.get(app_lower)
        if mapped:
            base_text = mapped

    # 最终兜底：有标题显示标题，否则默认文案。
    if not base_text:
        if cleaned_title:
            base_text = f"正在玩「{cleaned_title}」喵~"
        else:
            base_text = DEFAULT_DESCRIPTION

    return base_text


def _parse_keyword_list(raw_text: str) -> list[str]:
    """解析关键词列表（支持逗号/分号/换行分隔）。"""
    separators = [",", "，", ";", "；", "\n", "\r", "\t"]
    normalized = raw_text
    for separator in separators:
        normalized = normalized.replace(separator, ",")

    keywords: list[str] = []
    for part in normalized.split(","):
        keyword = part.strip().lower()
        if keyword:
            keywords.append(keyword)

    return keywords


def _build_device_search_text(device_item: dict[str, Any]) -> str:
    """构建设备关键词匹配文本（仅 device_name，统一小写）。"""
    return _clean_text(device_item.get("device_name")).lower()


def _match_device_keywords(device_item: dict[str, Any], keywords: list[str]) -> bool:
    """关键词命中判断：任意关键词为子串即命中。"""
    if not keywords:
        return False

    haystack = _build_device_search_text(device_item)
    if not haystack:
        return False

    return any(keyword in haystack for keyword in keywords)


def _contains_keyword(text: str, keywords: list[str]) -> bool:
    """判断文本是否命中任意关键词（大小写不敏感、子串匹配）。"""
    if not text or not keywords:
        return False

    haystack = text.lower()
    return any(keyword in haystack for keyword in keywords)


def _mask_sensitive_text(text: str, keywords: list[str], replacement: str) -> str:
    """对命中敏感关键词的文本执行替换。"""
    if _contains_keyword(text, keywords):
        return replacement
    return text


def _apply_device_keyword_filters(
    device_items: list[dict[str, Any]], config: dict[str, Any]
) -> list[dict[str, Any]]:
    """按配置对白名单/黑名单关键词进行设备筛选。"""
    whitelist_raw = get_text_value(config, "device_whitelist_keywords", "")
    blacklist_raw = get_text_value(config, "device_blacklist_keywords", "")

    whitelist_keywords = _parse_keyword_list(whitelist_raw)
    blacklist_keywords = _parse_keyword_list(blacklist_raw)

    filtered_items = device_items

    # 白名单：仅保留命中关键词的设备。
    if whitelist_keywords:
        filtered_items = [
            item
            for item in filtered_items
            if _match_device_keywords(item, whitelist_keywords)
        ]

    # 黑名单：移除命中关键词的设备（优先级高于白名单）。
    if blacklist_keywords:
        filtered_items = [
            item
            for item in filtered_items
            if not _match_device_keywords(item, blacklist_keywords)
        ]

    logger.debug(
        "[视奸面板] 关键词筛选：whitelist=%s, blacklist=%s, before=%s, after=%s",
        len(whitelist_keywords),
        len(blacklist_keywords),
        len(device_items),
        len(filtered_items),
    )

    return filtered_items


def _pick_device_items(
    payload_data: dict[str, Any], config: dict[str, Any]
) -> list[dict[str, Any]]:
    """从 payload 中挑选用于展示的设备列表。"""
    device_items_raw = payload_data.get("devices", [])
    # devices 字段异常时返回空列表，避免后续遍历报错。
    if not isinstance(device_items_raw, list):
        return []

    # 是否包含离线设备。
    include_offline_devices = get_bool_value(config, "include_offline_devices", False)
    # 最大展示设备数量，做上下限保护。
    max_devices = get_int_value(config, "max_devices", 10, min_value=1, max_value=100)

    # 仅保留 dict 项，过滤掉异常元素。
    device_items = [item for item in device_items_raw if isinstance(item, dict)]

    # 关键词黑白名单筛选。
    device_items = _apply_device_keyword_filters(device_items, config)

    # 默认只显示在线设备，减少消息噪音。
    if not include_offline_devices:
        device_items = [item for item in device_items if _is_online(item)]

    # 排序规则：在线优先，其次按设备名排序，保证输出稳定。
    device_items.sort(
        key=lambda item: (
            0 if _is_online(item) else 1,
            str(item.get("device_name", "")),
        )
    )

    # 按 max_devices 截断，防止一次输出过长。
    return device_items[:max_devices]


def get_render_device_count(
    payload_data: dict[str, Any], config: dict[str, Any]
) -> int:
    """获取最终将展示的设备数量（与渲染筛选逻辑一致）。"""
    return len(_pick_device_items(payload_data, config))


def render_dashboard_message(
    payload_data: dict[str, Any], config: dict[str, Any]
) -> str:
    """将 /api/current 返回数据渲染为更接近上游前端风格的回复文本。"""
    all_devices_raw = payload_data.get("devices", [])
    # 防御式转换：确保 all_devices 是 dict 列表。
    all_devices = (
        [item for item in all_devices_raw if isinstance(item, dict)]
        if isinstance(all_devices_raw, list)
        else []
    )

    # 头部统计口径：先应用关键词黑白名单，再统计在线/总数。
    # 这样“在线设备 x/y”会和过滤结果一致。
    counted_devices = _apply_device_keyword_filters(all_devices, config)
    total_count = len(counted_devices)
    online_count = sum(1 for item in counted_devices if _is_online(item))

    # 读取所有显示开关（由 _conf_schema.json 定义）。
    show_platform = get_bool_value(config, "show_platform", True)
    show_app_name = get_bool_value(config, "show_app_name", True)
    show_display_title = get_bool_value(config, "show_display_title", True)
    show_battery = get_bool_value(config, "show_battery", True)
    show_music = get_bool_value(config, "show_music", True)
    show_last_seen = get_bool_value(config, "show_last_seen", True)
    show_viewer_count = get_bool_value(config, "show_viewer_count", False)
    show_server_time = get_bool_value(config, "show_server_time", False)

    info_blacklist_keywords = _parse_keyword_list(
        get_text_value(config, "info_blacklist_keywords", "")
    )
    info_blacklist_replacement = (
        get_text_value(
            config, "info_blacklist_replacement", "不想让你看到我在干什么喵~"
        )
        or "不想让你看到我在干什么喵~"
    )

    # 初始化输出文本行。
    lines: list[str] = [
        "📊 Live Dashboard 状态面板",
        f"在线设备：{online_count}/{total_count}",
    ]

    # 调试日志：输出本次渲染基础统计与关键开关状态。
    logger.debug(
        "[视奸面板] 开始渲染消息：total=%s, online=%s, show_platform=%s, show_title=%s",
        total_count,
        online_count,
        show_platform,
        show_display_title,
    )

    # 可选展示访客数。
    if show_viewer_count:
        viewer_count = payload_data.get("viewer_count")
        if isinstance(viewer_count, int):
            lines.append(f"当前访客：{viewer_count}")

    # 可选展示服务端时间。
    if show_server_time:
        server_time = payload_data.get("server_time")
        if isinstance(server_time, str) and server_time.strip():
            lines.append(f"服务端时间：{format_time_text(server_time)}")

    # 挑选实际展示设备列表。
    device_items = _pick_device_items(payload_data, config)
    logger.debug("[视奸面板] 渲染设备列表：picked=%s", len(device_items))

    # 没有可展示设备时返回简短提示。
    if not device_items:
        lines.append("")
        lines.append("暂无符合条件的设备状态喵。")
        return "\n".join(lines)

    # 设备区块与头部之间插入空行，提升可读性。
    lines.append("")

    # 逐台设备渲染。
    for device_item in device_items:
        # 设备基础信息。
        device_name = _clean_text(device_item.get("device_name")) or "未知设备"
        platform_text = _clean_text(device_item.get("platform")) or "unknown"
        app_name_raw = _clean_text(device_item.get("app_name"))
        display_title_raw = _clean_text(device_item.get("display_title"))
        status_online = _is_online(device_item)
        status_text = "在线" if status_online else "离线"

        # extra 字段容错处理。
        extra_data = device_item.get("extra", {})
        if not isinstance(extra_data, dict):
            extra_data = {}

        # 设备首行：设备名 + 在线状态 + 平台（可选）。
        head_text = f"• {device_name} [{status_text}]"
        if show_platform:
            head_text += f" ({platform_text})"
        lines.append(head_text)

        # 主叙事句：现在正在…
        if status_online:
            activity_text = _build_activity_description(
                app_name_raw, display_title_raw, extra_data
            )
        else:
            activity_text = "离线休息中喵~"
        lines.append(f"  现在：{activity_text}")

        # 应用名（可选）：命中信息黑名单关键词时替换为统一文案。
        if show_app_name:
            app_name_text = _friendly_app_name(app_name_raw)
            app_name_text = _mask_sensitive_text(
                app_name_text,
                info_blacklist_keywords,
                info_blacklist_replacement,
            )
            lines.append(f"  应用：{app_name_text}")

        # display_title（可选）：命中信息黑名单关键词时替换为统一文案。
        if show_display_title:
            normalized_title = _normalize_display_title(display_title_raw, app_name_raw)
            title_text = normalized_title or "（无可展示标题）"
            if normalized_title:
                title_text = _mask_sensitive_text(
                    normalized_title,
                    info_blacklist_keywords,
                    info_blacklist_replacement,
                )
            lines.append(f"  标题：{title_text}")

        # 电量（可选）。
        if show_battery:
            battery_text = _format_battery(extra_data)
            lines.append(f"  🔋 电量：{battery_text}")

        # 音乐（可选）。
        if show_music:
            music_text = _format_music(extra_data)
            lines.append(f"  🎵 音乐：{music_text}")

        # 最后上报时间（可选）。
        if show_last_seen:
            last_seen = device_item.get("last_seen_at")
            if isinstance(last_seen, str) and last_seen.strip():
                lines.append(f"  🕒 上报：{format_time_text(last_seen)}")
            else:
                lines.append("  🕒 上报：暂无上报")

        # 每台设备之间留一个空行。
        lines.append("")

    # 去除尾部多余空行，保证回复结尾干净。
    while lines and not lines[-1].strip():
        lines.pop()

    # 合并文本并记录长度（DEBUG）。
    rendered = "\n".join(lines)
    logger.debug("[视奸面板] 渲染完成：reply_chars=%s", len(rendered))
    return rendered
