#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 raw_apps.txt（英文原始清单）+ data/translations.json（中文详解库）生成 index.html。

用法：
    python3 scripts/generate.py

新增应用若尚无中文详解，会用 blurb 生成基础介绍并在页面中标注"中文详解待补充"，
保证页面始终可生成；补充翻译后再次运行即可更新。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw_apps.txt"
TRANS = ROOT / "data" / "translations.json"
OUT = ROOT / "index.html"
SOURCES = {"community", "stable", "enterprise"}

# 新增应用的自动分类关键词（按顺序匹配，越具体越靠前）
CATEGORY_RULES = [
    ("存储与文件同步", ["aistor", "minio", "rustfs", "s3", "object storage", "nextcloud", "seafile",
                   "syncthing", "file manager", "filebrowser", "file explorer", "webdav", "sftp",
                   "copyparty", "filestash", "cloudreve", "opencloud", "filex", "strata", "filehub",
                   "file sharing", "file transfer", "pairdrop", "dropgate", "ultra explorer", "ipfs",
                   "versity gateway", "iconik storage", "keibidrop"]),
    ("备份与容灾", ["backup", "restic", "borg", "duplicati", "urbackup", "zerobyte", "momentbackup",
                "databasus", "unifi protect backup"]),
    ("3D打印", ["3d print", "octoprint", "filament", "spool", "bambu", "prusa", "printbuddy",
              "printstash", "stl", "gridfinity", "lens", "3d model"]),
    ("游戏服务", ["minecraft", "game server", "steam", "factorio", "terraria", "palworld",
               "satisfactory", "valheim", "crafty", "mineos", "pterodactyl", "calagopus",
               "gameyfin", "romm", "retrom", "gamevault", "luanti", "tmodloader", "romarr",
               "gaseous", "nsw game", "blackbriar", "headless"]),
    ("加密货币", ["bitcoin", "monero", "crypto", "miner", "xmr", "chia", "p2pool", "electrs",
               "mempool", "node"]),
    ("安全与认证", ["password", "auth", "sso", "2fa", "ldap", "keycloak", "authentik", "authelia",
                "vaultwarden", "passbolt", "tinyauth", "pocket id", "clamav", "fcaptcha",
                "keepass", "1password", "keeyo"]),
    ("智能家居与IoT", ["home assistant", "iot", "mqtt", "zigbee", "z-wave", "esphome", "mosquitto",
                   "smart home", "evcc", "tesla", "tasmota", "neo guard"]),
    ("电子书与漫画", ["calibre", "komga", "kavita", "ebook", "comic", "manga", "book", "cbz",
                  "epub", "shelfmark", "legejo", "storyteller", "chaptarr", "kapowarr",
                  "lazy librarian", "grimmory", "jelu", "nexbooks", "audiobook", "bindery"]),
    ("音乐与音频", ["navidrome", "music", "audio", "subsonic", "lyrion", "piper", "whisper",
                "audiomuse", "koel", "sacd", "faster whisper", "lumen aureum"]),
    ("照片与相册", ["immich", "photo", "gallery", "piwigo", "photoprism", "photoview",
                "photostructure", "snapotter", "digital photo frame"]),
    ("文档与办公", ["pdf", "document", "office", "collabora", "onlyoffice", "eurooffice",
                "paperless", "draw.io", "excalidraw", "penpot", "convertx", "nexpaper",
                "papra", "docspell", "ablago", "archivebox", "omnom", "timelinize"]),
    ("知识与笔记", ["joplin", "logseq", "outline", "trilium", "memos", "bookstack", "wiki",
                "notes", "knowledge", "affine", "blinko", "karakeep", "kept", "vaultbridge",
                "nexlore", "many notes", "futo notes"]),
    ("影音媒体", ["jellyfin", "plex", "emby", "media server", "streaming", "video", "dvr",
              "tvheadend", "channels", "cine", "fliks", "kinora", "remux", "silo", "stash",
              "kometa", "airwave", "mediaman", "mediathek", "tube", "peerTube", "invidious",
              "piped", "nevu", "kryspal", "fladder", "plex"]),
    ("媒体自动化", ["sonarr", "radarr", "lidarr", "readarr", "prowlarr", "bazarr", "seerr",
               "overseerr", "ombi", "indexer", "recyclarr", "cleanuparr", "maintainerr",
               "unpackerr", "holyarrs", "nexcrate", "suggestarr", "sportarr", "wondarr",
               "boxarr", "pulsarr", "tracearr", "clonarr", "profilarr", "umlautadaptarr"]),
    ("下载工具", ["qbittorrent", "transmission", "deluge", "sabnzbd", "nzbget", "jdownloader",
              "metube", "yt-dlp", "youtube-dl", "download", "torrent", "usenet", "debrid",
              "slskd", "retriever", "nzbfast", "bitmagnet", "byparr", "flaresolverr", "trawl"]),
    ("仪表盘与导航", ["dashboard", "homepage", "homarr", "dashy", "heimdall", "homer",
                "organizr", "flame", "glance", "stackyard", "nexdeck", "arrvantage"]),
    ("系统监控与运维", ["monitor", "grafana", "prometheus", "netdata", "uptime", "docker", "portainer",
                 "glances", "beszel", "scrutiny", "gatus", "dozzle", "tianji", "solidping",
                 "umami", "toparr", "nas doctor", "naswarden", "portracker", "pingkit",
                 "speedtest", "speedketchup", "nexpulse", "monitee", "zabbix", "logforge",
                 "snapshot visualizer", "ktn enclosure", "scanvento", "globalping"]),
    ("网络与远程访问", ["proxy", "vpn", "wireguard", "tailscale", "cloudflare", "tunnel", "dns",
                 "ddns", "nginx", "traefik", "netbird", "zerotier", "headscale", "newt",
                 "wg-easy", "zoraxy", "corvus", "mitmproxy", "3proxy", "arti", "i2p",
                 "remote desktop", "rust desk", "meshcentral", "kasm", "termix", "nextrmnl",
                 "open terminal", "nuvirahub", "netboot", "open speed test", "lancache",
                 "dockroute", "docktail", "autoxpose", "twingate", "cloudgate"]),
    ("数据库与搜索", ["postgres", "mysql", "mariadb", "redis", "mongodb", "elasticsearch",
                "elastic search", "search", "database", "meilisearch", "qdrant", "searxng",
                "whoogle", "pgadmin", "nexus repository", "distribution", "iceberg", "memcached"]),
    ("邮件与通讯", ["mail", "email", "chat", "matrix", "signal", "whatsapp", "teamspeak", "mumble",
               "gotify", "ntfy", "notification", "listmonk", "roundcube", "stalwart",
               "mailpit", "bichon", "bulwark", "ihasmail", "plmail", "nexmail", "chatwoot",
               "zammad", "element", "continuwuity", "tuwunel", "subsimail", "unihub"]),
    ("家庭生活与健康", ["budget", "finance", "recipe", "meal", "grocery", "health", "fitness",
                 "workout", "habit", "todo", "task", "family", "inventory", "grocy", "mealie",
                 "tandoor", "kitchenowl", "actual budget", "firefly iii", "ghostfolio",
                 "wealthfolio", "splitpro", "nametag", "lubelogger", "cellarion", "warracker",
                 "yuvomi", "openfamily", "opentracker", "ovumcy", "sparkyfitness", "wger",
                 "opengym", "trek", "travelbuff", "adventurelog", "dawarich", "ferret",
                 "kept", "lyftr", "tempo ai"]),
    ("开发工具与自动化", ["git", "gitea", "forgejo", "jenkins", "ci", "code server", "vscode",
                  "automation", "n8n", "playwright", "node-red", "windmill", "woodpecker",
                  "concourse", "coolify", "hoppscotch", "it tools", "omni tools", "api",
                  "faster whisper", "mitmproxy"]),
    ("AI与大模型", ["llm", "ai", "ollama", "openai", "chatgpt", "gpt", "vector", "embedding",
               "rag", "librechat", "open webui", "anything llm", "localai", "vllm",
               "llms.py", "hermes-agent", "odysseus", "vane", "inbox zero", "paperless ai",
               "agent hub", "wardrowbe", "openclaw", "paperclip", "stdapi.ai", "litellm"]),
]


def parse_raw():
    if not RAW.exists():
        sys.exit(f"缺少原始清单文件：{RAW}")
    text = RAW.read_text(encoding="utf-8")
    blocks = [b.strip().splitlines() for b in re.split(r"\n\s*\n", text) if b.strip()]
    apps, errors = [], []
    for idx, block in enumerate(blocks, 1):
        lines = [l.strip() for l in block if l.strip()]
        if len(lines) not in (4, 5) or lines[0] not in SOURCES:
            errors.append((idx, lines))
            continue
        source, name = lines[0], lines[1]
        if len(lines) == 5:
            if not lines[2].isdigit():
                errors.append((idx, lines))
                continue
            stars, version, blurb = int(lines[2]), lines[3], lines[4]
        else:
            stars, version, blurb = None, lines[2], lines[3]
        apps.append({"id": len(apps) + 1, "name": name, "source": source,
                     "stars": stars, "version": version, "blurb": blurb})
    if errors:
        print(f"[警告] 跳过 {len(errors)} 个格式异常的条目：{errors[:3]}", file=sys.stderr)
    return apps


def guess_category(name, blurb):
    text = (name + " " + blurb).lower()
    for cat, keywords in CATEGORY_RULES:
        if any(k in text for k in keywords):
            return cat
    return "其他工具"


def fallback(a):
    """新增条目尚无中文详解时的基础内容，保证页面可正常生成。"""
    return {
        "category": guess_category(a["name"], a["blurb"]),
        "tagline": "新增应用 · 中文详解待补充",
        "what_it_is": f"{a['name']}：{a['blurb']} 该条目为新增应用，中文详解待补充。",
        "features": [
            "原始简介已收录在卡片底部，可展开查看",
            "分类由关键词自动推断，后续可人工校正",
            "补充中文详解后重新生成页面即可更新",
        ],
        "use_case": "可先根据原始简介判断是否相关，具体能力请参考上游项目文档。",
        "tips": "该应用尚未有中文详解；部署要求、依赖与授权条款请以官方说明为准。",
        "difficulty": "中",
        "resources": "中",
        "_new": True,
    }


def merge():
    apps = parse_raw()
    trans = json.loads(TRANS.read_text(encoding="utf-8")) if TRANS.exists() else []
    exact, by_name = {}, {}
    for t in trans:
        exact.setdefault((t.get("name"), t.get("source"), t.get("version")), t)
        by_name.setdefault(t.get("name"), t)
    result, new_apps = [], []
    for a in apps:
        t = exact.get((a["name"], a["source"], a["version"])) or by_name.get(a["name"])
        if t:
            a.update({k: v for k, v in t.items() if k not in ("name", "source", "version")})
        else:
            a.update(fallback(a))
            new_apps.append(a["name"])
        result.append(a)
    print(f"共 {len(result)} 条；新增未翻译条目 {len(new_apps)} 条" +
          (f"：{', '.join(new_apps[:10])}" if new_apps else ""))
    return result


TPL = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>自托管应用选型手册 · __COUNT__ 款应用详解</title>
<style>
:root{
  --bg:#f6f7f9; --surface:#ffffff; --surface2:#fbfbfd; --border:#e3e6eb;
  --text:#1e2430; --muted:#6b7280; --faint:#9ca3af;
  --accent:#2563eb; --accent-soft:#eef4ff; --accent-line:#bfd4ff;
  --green:#0f8a60; --green-soft:#e8f7f0;
  --amber:#b45309; --amber-soft:#fff5e6;
  --red:#c02626; --red-soft:#ffeded;
  --purple:#6d3fd1; --purple-soft:#f2ecff;
  --shadow:0 1px 2px rgba(16,24,40,.04),0 4px 14px rgba(16,24,40,.05);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  font-size:14px;line-height:1.65;-webkit-font-smoothing:antialiased}
a{color:var(--accent)}
.wrap{max-width:1480px;margin:0 auto;padding:0 28px 80px}

/* ---------- hero ---------- */
.hero{background:linear-gradient(135deg,#ffffff 0%,#f3f7ff 100%);border-bottom:1px solid var(--border);padding:44px 0 30px}
.hero-in{max-width:1480px;margin:0 auto;padding:0 28px}
.eyebrow{display:inline-block;font-size:12px;letter-spacing:.12em;color:var(--accent);font-weight:700;
  background:var(--accent-soft);border:1px solid var(--accent-line);border-radius:99px;padding:3px 12px}
h1{font-size:32px;line-height:1.25;margin:14px 0 8px;letter-spacing:-.02em}
.sub{color:var(--muted);font-size:14px;max-width:900px;margin:0}
.stats{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}
.stat{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 16px;min-width:104px;box-shadow:var(--shadow)}
.stat b{display:block;font-size:20px;line-height:1.2}
.stat span{font-size:12px;color:var(--muted)}

/* ---------- panels ---------- */
.panel{background:var(--surface);border:1px solid var(--border);border-radius:14px;box-shadow:var(--shadow);padding:20px 22px;margin-top:22px}
.panel h2{font-size:17px;margin:0 0 12px}
.legend{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px 24px;color:var(--muted);font-size:13px}
.legend b{color:var(--text)}
.pill{display:inline-block;border-radius:5px;padding:0 6px;font-size:12px;font-weight:600;line-height:20px}
.pill.community{background:var(--accent-soft);color:var(--accent)}
.pill.stable{background:var(--green-soft);color:var(--green)}
.pill.enterprise{background:var(--purple-soft);color:var(--purple)}
.pill.deprecated{background:var(--red-soft);color:var(--red)}

table.overview{width:100%;border-collapse:collapse;font-size:13px}
table.overview th,table.overview td{padding:8px 10px;border-bottom:1px solid var(--border);text-align:left;vertical-align:top}
table.overview th{color:var(--muted);font-weight:600;background:var(--surface2);position:sticky;top:0}
table.overview tr{cursor:pointer}
table.overview tbody tr:hover{background:var(--accent-soft)}
table.overview td.n{width:64px;color:var(--muted);font-variant-numeric:tabular-nums}
table.overview td.rep{color:var(--muted)}

/* ---------- toolbar ---------- */
.toolbar{position:sticky;top:0;z-index:20;background:rgba(246,247,249,.94);backdrop-filter:blur(10px);
  border-bottom:1px solid var(--border);padding:12px 0;margin-top:26px}
.tb-in{max-width:1480px;margin:0 auto;padding:0 28px}
.tb-row{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.tb-row + .tb-row{margin-top:10px}
.search{flex:1;min-width:260px;position:relative}
.search input{width:100%;padding:9px 12px 9px 34px;border:1px solid var(--border);border-radius:9px;background:var(--surface);color:var(--text);font-size:14px;outline:none}
.search input:focus{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.search svg{position:absolute;left:10px;top:50%;transform:translateY(-50%);opacity:.45}
select,button{font:inherit;color:var(--text)}
select{padding:8px 10px;border:1px solid var(--border);border-radius:8px;background:var(--surface);outline:none}
button{cursor:pointer;border:1px solid var(--border);background:var(--surface);border-radius:8px;padding:8px 12px}
button:hover{border-color:var(--accent);color:var(--accent)}
button.primary{background:var(--accent);border-color:var(--accent);color:#fff}
button.primary:hover{background:#1d4ed8;color:#fff}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{border:1px solid var(--border);background:var(--surface);color:var(--muted);border-radius:99px;padding:4px 11px;font-size:12.5px;line-height:1.5}
.chip:hover{border-color:var(--accent);color:var(--accent)}
.chip.on{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
.result{color:var(--muted);font-size:13px;white-space:nowrap}
.result b{color:var(--text);font-size:15px}

/* ---------- cards ---------- */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(400px,1fr));gap:16px;margin-top:20px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:18px 18px 16px;box-shadow:var(--shadow);display:flex;flex-direction:column;break-inside:avoid}
.card.picked{border-color:var(--accent);box-shadow:0 0 0 2px var(--accent-soft),var(--shadow)}
.chead{display:flex;align-items:flex-start;gap:10px}
.pick{flex:none;display:flex;align-items:center;gap:5px;font-size:12px;color:var(--muted);cursor:pointer;user-select:none;border:1px solid var(--border);border-radius:7px;padding:3px 7px;background:var(--surface2)}
.pick input{accent-color:var(--accent);margin:0}
.chead h3{font-size:17px;margin:0;line-height:1.4;flex:1;word-break:break-word}
.meta{display:flex;flex-wrap:wrap;gap:5px;margin:10px 0 8px}
.meta span{font-size:11.5px;color:var(--muted);background:var(--surface2);border:1px solid var(--border);border-radius:5px;padding:1px 7px;white-space:nowrap}
.meta .hot{color:var(--amber);background:var(--amber-soft);border-color:#f6dfb8}
.meta .cat{color:var(--accent);background:var(--accent-soft);border-color:var(--accent-line)}
.tagline{margin:0 0 8px;font-weight:600;color:var(--accent);font-size:13.5px}
.what{margin:0;color:#374151;font-size:13.5px}
.features{margin:10px 0;padding-left:18px;color:#374151;font-size:13px}
.features li{margin:2px 0}
.row{font-size:13px;margin:3px 0;color:#374151}
.row b{display:inline-block;min-width:34px;color:var(--muted);font-weight:600}
.row.tip{color:#7c4a12;background:var(--amber-soft);border-radius:7px;padding:6px 9px;margin-top:9px}
.row.tip b{color:var(--amber)}
details.orig{margin-top:10px;border-top:1px dashed var(--border);padding-top:8px}
details.orig summary{cursor:pointer;color:var(--faint);font-size:12px;list-style:none}
details.orig summary::-webkit-details-marker{display:none}
details.orig summary:before{content:"▸ ";font-size:11px}
details.orig[open] summary:before{content:"▾ "}
details.orig p{margin:6px 0 0;color:var(--muted);font-size:12px;word-break:break-word}
.empty{text-align:center;color:var(--muted);padding:60px 20px}

/* ---------- selection bar ---------- */
.selbar{position:fixed;left:50%;transform:translateX(-50%);bottom:20px;z-index:30;display:none;
  background:#111827;color:#fff;border-radius:12px;padding:10px 14px;box-shadow:0 10px 30px rgba(0,0,0,.22);
  align-items:center;gap:12px;font-size:13px}
.selbar.show{display:flex}
.selbar b{color:#93c5fd}
.selbar button{background:#1f2937;border-color:#374151;color:#fff;padding:6px 10px;font-size:12px}
.selbar button:hover{background:#374151;color:#fff}
.selbar button.export{background:var(--accent);border-color:var(--accent)}
.selbar button.export:hover{background:#1d4ed8}

.foot{margin-top:34px;color:var(--muted);font-size:12.5px;text-align:center}

@media (max-width:760px){
  .wrap,.hero-in,.tb-in{padding-left:16px;padding-right:16px}
  h1{font-size:25px}
  .grid{grid-template-columns:1fr}
  .panel{padding:16px}
}
@media print{
  :root{--bg:#fff;--surface:#fff;--surface2:#fff;--border:#d8d8d8;--shadow:none}
  body{background:#fff;font-size:10.5pt}
  .hero{background:#fff;padding:10px 0 14px}
  h1{font-size:20pt}
  .toolbar,.selbar,.pick,.panel#overview,button,details.orig{display:none !important}
  .wrap,.hero-in{max-width:none;padding:0 12mm}
  .grid{display:block;margin-top:10px}
  .card{border:1px solid #d8d8d8;border-radius:6px;padding:10px 12px;margin-bottom:9px;box-shadow:none;break-inside:avoid;page-break-inside:avoid}
  .chead h3{font-size:12pt}
  .features{margin:5px 0}
  .row.tip{background:#fff8e8}
  table.overview{display:none}
  .printonly{display:block !important}
}
.printonly{display:none}
</style>
</head>
<body>
<div class="hero">
  <div class="hero-in">
    <span class="eyebrow">自托管应用选型手册</span>
    <h1>应用商店全量详解与选型指南</h1>
    <p class="sub">逐一梳理清单中的每一款应用：定位、核心功能、适用场景、部署难度与安装提示。可搜索、按分类筛选、勾选生成候选清单，方便对比后决定安装。</p>
    <div class="stats" id="stats"></div>
  </div>
</div>

<div class="wrap">
  <section class="panel">
    <h2>阅读说明</h2>
    <div class="legend">
      <div><span class="pill community">community</span> 社区应用，由社区维护，数量最多。</div>
      <div><span class="pill stable">stable</span> 官方稳定版通道，通常更强调稳定性。</div>
      <div><span class="pill enterprise">enterprise</span> 企业版，需确认授权与使用条款。</div>
      <div><b>★ 星标</b> 上游项目热度参考，不等于质量或易用性。</div>
      <div><b>版本</b> 为清单收录的插件版本，不代表上游软件版本。</div>
      <div><b>难度 / 资源</b> 为部署上手难度与资源占用的粗略估计。</div>
      <div><b>原始简介</b> 展开可查看清单提供的英文原文，便于核对。</div>
      <div><b>同名条目</b> 来源或版本不同（如 Syncthing、Nextcloud），会分别展示。</div>
    </div>
  </section>

  <section class="panel" id="overview">
    <h2>分类速览（点击分类可直接筛选）</h2>
    <table class="overview">
      <thead><tr><th>分类</th><th>数量</th><th>代表应用（按星标）</th></tr></thead>
      <tbody id="ovbody"></tbody>
    </table>
  </section>

  <div class="toolbar">
    <div class="tb-in">
      <div class="tb-row">
        <div class="search">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
          <input id="q" type="search" placeholder="搜索名称、功能、场景，例如：照片备份、DNS、下载、PDF…">
        </div>
        <select id="source"><option value="">全部来源</option><option value="community">community 社区</option><option value="stable">stable 稳定版</option><option value="enterprise">enterprise 企业版</option></select>
        <select id="diff"><option value="">全部难度</option><option value="低">难度：低</option><option value="中">难度：中</option><option value="高">难度：高</option></select>
        <select id="res"><option value="">全部资源</option><option value="轻">资源：轻</option><option value="中">资源：中</option><option value="重">资源：重</option></select>
        <select id="sort"><option value="hot">按热度排序</option><option value="name">按名称排序</option><option value="cat">按分类排序</option><option value="diff">按上手难度排序</option></select>
        <button type="button" onclick="window.print()">打印 / 导出 PDF</button>
      </div>
      <div class="tb-row">
        <div class="chips" id="chips"></div>
        <span class="result" id="result"></span>
      </div>
    </div>
  </div>

  <div class="grid" id="grid"></div>
  <div class="foot">本手册基于所提供的应用商店清单整理，共 __COUNT__ 条；功能描述为便于选型的概述，实际能力以各项目官方文档为准。</div>
</div>

<div class="selbar" id="selbar">
  <span>已选候选 <b id="seln">0</b> 款</span>
  <button type="button" class="export" id="export">导出候选清单 CSV</button>
  <button type="button" id="clear">清空</button>
</div>

<script>
const DATA = __DATA__;
const CATS = [...new Set(DATA.map(a=>a.category))].sort((a,b)=>{
  const n = DATA.filter(x=>x.category===b).length-DATA.filter(x=>x.category===a).length;
  return n!==0?n:a.localeCompare(b,'zh-CN');
});
const dups = {};
DATA.forEach(a=>{dups[a.name]=(dups[a.name]||0)+1});
const $ = id=>document.getElementById(id);
const esc = s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const state = {q:'',cat:'',source:'',diff:'',res:'',sort:'hot'};
let selected = new Set(JSON.parse(localStorage.getItem('nas-app-selected')||'[]'));

function renderStats(){
  const sc = s=>DATA.filter(a=>a.source===s).length;
  const items=[['应用条目',DATA.length],['应用分类',CATS.length],['社区版',sc('community')],['稳定版',sc('stable')],['企业版',sc('enterprise')]];
  $('stats').innerHTML = items.map(([k,v])=>`<div class="stat"><b>${v}</b><span>${k}</span></div>`).join('');
}
function renderChips(){
  $('chips').innerHTML = ['全部',...CATS].map(c=>`<button type="button" class="chip ${state.cat===c||(!state.cat&&c==='全部')?'on':''}" data-cat="${c==='全部'?'':esc(c)}">${esc(c)}</button>`).join('');
  document.querySelectorAll('.chip').forEach(b=>b.onclick=()=>{state.cat=b.dataset.cat;renderChips();render()});
}
function renderOverview(){
  const rows = CATS.map(c=>{
    const list=DATA.filter(a=>a.category===c);
    const top=list.slice().sort((a,b)=>(b.stars||0)-(a.stars||0))[0];
    return `<tr data-cat="${esc(c)}"><td><b>${esc(c)}</b></td><td class="n">${list.length}</td><td class="rep">${esc(top.name)}</td></tr>`;
  }).join('');
  $('ovbody').innerHTML=rows;
  document.querySelectorAll('#ovbody tr').forEach(tr=>tr.onclick=()=>{
    state.cat=tr.dataset.cat;renderChips();render();
    document.querySelector('.toolbar').scrollIntoView({behavior:'smooth',block:'start'});
  });
}
function match(a,q){
  if(!q)return true;
  const hay=[a.name,a.tagline,a.what_it_is,a.use_case,a.tips,a.blurb,a.category,...a.features].join(' ').toLowerCase();
  return q.split(/\s+/).every(t=>hay.includes(t));
}
function render(){
  let list=DATA.filter(a=>
    (!state.cat||a.category===state.cat)&&
    (!state.source||a.source===state.source)&&
    (!state.diff||a.difficulty===state.diff)&&
    (!state.res||a.resources===state.res)&&
    match(a,state.q)
  );
  const order={'低':0,'中':1,'高':2};
  list.sort((a,b)=>{
    if(state.sort==='name')return a.name.localeCompare(b.name,'en',{sensitivity:'base'});
    if(state.sort==='cat')return a.category.localeCompare(b.category,'zh-CN')||a.name.localeCompare(b.name,'en');
    if(state.sort==='diff')return order[a.difficulty]-order[b.difficulty]||(b.stars||0)-(a.stars||0);
    return (b.stars??-1)-(a.stars??-1);
  });
  $('result').innerHTML=`显示 <b>${list.length}</b> / ${DATA.length} 款`;
  $('grid').innerHTML = list.length?list.map(a=>{
    const dep=/deprecated/i.test(a.name+a.blurb);
    const stars=a.stars==null?'<span>★ 暂无</span>':`<span class="hot">★ ${a.stars.toLocaleString()}</span>`;
    return `<article class="card ${selected.has(a.name)?'picked':''}">
      <div class="chead">
        <label class="pick"><input type="checkbox" class="pickbox" data-name="${esc(a.name)}" ${selected.has(a.name)?'checked':''}>候选</label>
        <h3>${esc(a.name)}</h3>
        <span class="pill ${a.source}">${a.source}</span>${dep?'<span class="pill deprecated">已弃用</span>':''}
      </div>
      <div class="meta">${stars}<span>v${esc(a.version)}</span><span class="cat">${esc(a.category)}</span><span>难度 ${a.difficulty}</span><span>资源 ${a.resources}</span>${dups[a.name]>1?'<span>同名多版本</span>':''}</div>
      <p class="tagline">${esc(a.tagline)}</p>
      <p class="what">${esc(a.what_it_is)}</p>
      <ul class="features">${a.features.map(f=>`<li>${esc(f)}</li>`).join('')}</ul>
      <div class="row"><b>适用</b>${esc(a.use_case)}</div>
      <div class="row tip"><b>提示</b>${esc(a.tips)}</div>
      <details class="orig"><summary>原始简介</summary><p>${esc(a.blurb)}</p></details>
    </article>`;
  }).join(''):'<div class="empty">没有符合条件的应用，试试更换关键词或筛选条件。</div>';
  document.querySelectorAll('.pickbox').forEach(cb=>cb.onchange=()=>{
    if(cb.checked)selected.add(cb.dataset.name);else selected.delete(cb.dataset.name);
    localStorage.setItem('nas-app-selected',JSON.stringify([...selected]));
    cb.closest('.card').classList.toggle('picked',cb.checked);syncSel();
  });
}
function syncSel(){
  $('seln').textContent=selected.size;
  $('selbar').classList.toggle('show',selected.size>0);
}
$('q').oninput=e=>{state.q=e.target.value.trim().toLowerCase();render()};
['source','diff','res','sort'].forEach(k=>$(k).onchange=e=>{state[k]=e.target.value;render()});
$('clear').onclick=()=>{selected.clear();localStorage.setItem('nas-app-selected','[]');syncSel();render()};
$('export').onclick=()=>{
  const rows=[['名称','分类','来源','星标','版本','难度','资源','定位','适用场景','安装提示']];
  DATA.filter(a=>selected.has(a.name)).forEach(a=>rows.push([a.name,a.category,a.source,a.stars??'',a.version,a.difficulty,a.resources,a.tagline,a.use_case,a.tips]));
  const csv='\ufeff'+rows.map(r=>r.map(v=>'"'+String(v).replace(/"/g,'""')+'"').join(',')).join('\r\n');
  const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
  const a=document.createElement('a');a.href=url;a.download='候选应用清单.csv';a.click();URL.revokeObjectURL(url);
};
renderStats();renderChips();renderOverview();render();syncSel();
</script>
</body>
</html>'''


def main():
    apps = merge()
    payload = json.dumps(apps, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = TPL.replace("__DATA__", payload).replace("__COUNT__", str(len(apps)))
    assert "__DATA__" not in html and "__COUNT__" not in html
    OUT.write_text(html, encoding="utf-8")
    print(f"已生成 {OUT}（{len(html):,} 字符）")


if __name__ == "__main__":
    main()
