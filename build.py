#!/usr/bin/env python3
"""NumPilot 블로그 빌드 — posts/*.md 를 읽어 정적 HTML 생성.

사용법:  python3 build.py
출력:    index.html (블로그 메인), blog/<slug>/index.html (각 글)

목차 그룹(부) 정보는 ../OUTLINE.md 를 파싱해 자동으로 얻는다.
아직 원고가 없는 편은 목차에 '예정'으로 회색 표시된다(링크 없음).
"""
import os, re, sys, html, json
import markdown

ROOT = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR = os.path.join(ROOT, "posts")
BLOG_DIR = os.path.join(ROOT, "blog")
OUTLINE = os.path.join(os.path.dirname(ROOT), "OUTLINE.md")

SITE = "Numpilot"
TAGLINE = "말로 설명하면, 폰이 풀어낸다"
SERIES = "손안의 수치해석"
SERIES_BLURB = ("수치해석을 휴대폰에서 하겠다는 무모한 결정, 그리고 그것을 가능하게 만들기 위해 "
                "우리가 설계해야 했던 언어에 대한 기록.")

CSS = """
:root{
  --bg:#ffffff; --alt:#f7f9fb; --line:#e5e9ef; --line2:#d3dae3;
  --fg:#1a2029; --dim:#5b6675; --faint:#8d97a5; --ghost:#a9b2be;
  --accent:#1d6fd6; --accent-soft:#eef4fd;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,monospace;
  --sans:Pretendard,-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Segoe UI",sans-serif;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--sans);
  font-size:17px;line-height:1.78;letter-spacing:-.004em;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline;text-underline-offset:3px}

/* 핸드북 2단 레이아웃 */
.shell{max-width:1120px;margin:0 auto;padding:0 26px;display:grid;
  grid-template-columns:250px minmax(0,1fr);gap:52px;align-items:start}
.solo{max-width:1120px;margin:0 auto;padding:0 26px}

header{border-bottom:1px solid var(--line);background:var(--bg);position:sticky;top:0;z-index:30}
.hd{max-width:1120px;margin:0 auto;padding:0 26px;display:flex;align-items:center;
  justify-content:space-between;height:58px}
.brand{font-size:16px;font-weight:750;letter-spacing:-.02em;color:var(--fg)}
.brand:hover{text-decoration:none}
nav.top a{font-size:14px;color:var(--dim);margin-left:20px}
nav.top a:hover{color:var(--accent);text-decoration:none}

/* ── 사이드바 목차 ───────────────────────────────── */
aside{position:sticky;top:82px;padding:30px 0 40px;font-size:14px;
  max-height:calc(100vh - 104px);overflow-y:auto;overscroll-behavior:contain}
.toc-cb{position:absolute;width:1px;height:1px;opacity:0;pointer-events:none}
.toc-bar{display:flex;align-items:center;gap:9px;margin-bottom:13px}
.side-h{font-family:var(--mono);font-size:11px;letter-spacing:.14em;color:var(--faint);
  text-transform:uppercase;font-weight:600}
.toc-n{font-family:var(--mono);font-size:11px;color:var(--accent);font-weight:700;
  background:var(--accent-soft);border-radius:3px;padding:2px 6px}
.cv{flex:none;display:none;color:var(--faint)}

/* 진행 표시 */
.prog{margin:0 0 15px}
.prog .bar{height:4px;background:var(--line);border-radius:3px;overflow:hidden}
.prog .bar i{display:block;height:100%;background:var(--accent);border-radius:3px}
.prog .t{font-family:var(--mono);font-size:10.5px;color:var(--faint);margin-top:7px;
  letter-spacing:.03em}

/* 부(part) 그룹 */
.toc{list-style:none;margin:0;padding:0}
.pt{border-top:1px solid var(--line)}
.pt:last-of-type{border-bottom:1px solid var(--line)}
.pt>summary{display:flex;align-items:center;gap:8px;padding:9px 2px;cursor:pointer;
  list-style:none;font-size:13.5px;font-weight:700;letter-spacing:-.012em;color:var(--fg)}
.pt>summary::-webkit-details-marker{display:none}
.pt>summary::marker{content:""}
.pt>summary:hover{color:var(--accent)}
.pt .pn{font-family:var(--mono);font-size:10.5px;font-weight:700;color:var(--accent);
  background:var(--accent-soft);border-radius:3px;padding:2px 5px;flex:none;letter-spacing:.02em}
.pt .ptt{flex:1;min-width:0;line-height:1.4;word-break:keep-all}
.pt .pc{font-family:var(--mono);font-size:10px;color:var(--faint);flex:none}
.pt .pcv{flex:none;color:var(--line2);transition:transform .18s}
.pt[open]>summary .pcv{transform:rotate(180deg)}
.pt.cur>summary{color:var(--accent)}
.pt.cur .pn{background:var(--accent);color:#fff}
.items{list-style:none;margin:0 0 9px;padding:0;border-left:2px solid var(--line);
  margin-left:6px}
.items li{margin:0}
.items a,.items .soon{display:block;padding:6px 0 6px 12px;line-height:1.5;font-size:13.5px;
  margin-left:-2px;border-left:2px solid transparent;word-break:keep-all}
.items a{color:var(--dim)}
.items a:hover{color:var(--accent);background:var(--accent-soft);text-decoration:none}
.items a.on{color:var(--accent);font-weight:700;border-left-color:var(--accent);
  background:var(--accent-soft)}
.items .soon{color:var(--ghost);cursor:default}
.items .n{font-family:var(--mono);font-size:11px;color:var(--faint);margin-right:7px}
.items .soon .n{color:#c5ccd6}
.items a.on .n{color:var(--accent)}
.toc-foot{font-family:var(--mono);font-size:10px;color:var(--faint);margin-top:12px;
  letter-spacing:.03em;line-height:1.7}
.toc-foot .dash{display:inline-block;width:16px;border-top:1px dashed var(--line2);
  vertical-align:middle;margin-right:5px}

/* ── index ───────────────────────────────────────── */
.hero{padding:48px 0 26px}
.kicker{display:inline-block;font-family:var(--mono);font-size:11px;letter-spacing:.14em;
  color:var(--accent);text-transform:uppercase;font-weight:650;
  background:var(--accent-soft);padding:5px 10px;border-radius:4px;margin-bottom:18px}
.hero h1{font-size:34px;line-height:1.32;margin:0 0 16px;letter-spacing:-.028em;font-weight:750}
.hero p{color:var(--dim);font-size:16.5px;margin:0;max-width:42em;line-height:1.75}

/* ── 핵심 요약 ───────────────────────────────────── */
.sum{border:1px solid var(--line);border-radius:12px;padding:24px 24px 26px;
  margin:8px 0 42px;background:linear-gradient(180deg,#fbfcfe 0%,#ffffff 55%)}
.sum-h{display:flex;align-items:center;gap:12px;margin-bottom:16px}
.sum-h .lbl{font-family:var(--mono);font-size:10.5px;letter-spacing:.07em;
  text-transform:uppercase;color:var(--accent);font-weight:700;flex:none}
.sum-h .rule{flex:1;height:1px;background:var(--line)}
.sum-h .wip{font-family:var(--mono);font-size:10px;color:var(--faint);flex:none;
  border:1px solid var(--line2);border-radius:20px;padding:2px 9px}
.sum-lead{font-size:19.5px;line-height:1.66;font-weight:700;letter-spacing:-.025em;
  margin:0 0 10px;max-width:34em;word-break:keep-all}
.sum-lead b{color:var(--accent);font-weight:700}
.sum-sub{color:var(--dim);font-size:15.5px;line-height:1.75;margin:0 0 26px;max-width:44em}

.flow{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:30px;margin:0 0 24px}
.step{position:relative;min-width:0;background:#fff;border:1px solid var(--line);
  border-radius:10px;padding:15px 16px 17px}
.step::after{content:"→";position:absolute;right:-22px;top:50%;transform:translateY(-50%);
  font-family:var(--mono);font-size:15px;font-weight:700;color:#b6bfcb;line-height:1}
.step:last-child::after{content:none}
.step .sn{display:block;font-family:var(--mono);font-size:10px;letter-spacing:.08em;
  color:var(--faint);font-weight:700;margin-bottom:9px;text-transform:uppercase}
.step h3{font-size:16px;margin:0 0 9px;font-weight:750;letter-spacing:-.022em;line-height:1.4;
  word-break:keep-all}
.step p{margin:0;font-size:14.5px;line-height:1.66;color:var(--dim)}
.step .say{display:block;font-family:var(--mono);font-size:12.5px;line-height:1.7;
  color:var(--fg);background:var(--alt);border:1px solid var(--line);border-radius:7px;
  padding:9px 11px;margin:0 0 11px;word-break:keep-all}
.step.mid{background:var(--alt);border-color:var(--line2)}
.step.mid .gears{list-style:none;margin:0 0 11px;padding:0;
  border-left:2px solid var(--line2)}
.step.mid .gears li{font-family:var(--mono);font-size:11.5px;color:var(--dim);
  padding:3px 0 3px 10px;line-height:1.55;letter-spacing:-.02em;word-break:keep-all}
.step .out{list-style:none;margin:0 0 11px;padding:0}
.step .out li{font-size:13.5px;color:var(--fg);padding:3px 0 3px 14px;position:relative;
  line-height:1.55;word-break:keep-all}
.step .out li::before{content:"›";position:absolute;left:2px;color:var(--accent);font-weight:700}

.cmp{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:0 0 22px}
.cmp .c{min-width:0;border:1px solid var(--line);border-radius:10px;padding:14px 16px 15px}
.cmp .c.cut{border-left:3px solid var(--accent)}
.cmp .c.keep{border-left:3px solid var(--line2)}
.cmp h4{margin:0 0 9px;font-size:13.5px;font-weight:750;letter-spacing:-.015em;
  word-break:keep-all}
.cmp .c.cut h4{color:var(--accent)}
.cmp ul{list-style:none;margin:0;padding:0}
.cmp li{font-size:14px;color:var(--dim);padding:3px 0 3px 13px;position:relative;line-height:1.6;
  word-break:keep-all}
.cmp li::before{content:"·";position:absolute;left:3px;color:var(--faint);font-weight:700}

.sum-close{border-top:1px solid var(--line);padding-top:17px;font-size:15.5px;
  line-height:1.72;color:var(--fg);margin:0;max-width:46em}
.sum-close strong{font-weight:750}
.sum-close .th{display:block;font-family:var(--mono);font-size:10px;letter-spacing:.05em;
  text-transform:uppercase;color:var(--faint);font-weight:700;margin-bottom:8px}

/* ── 글 목록 ─────────────────────────────────────── */
.list-h{display:flex;align-items:center;gap:12px;margin:0 0 2px}
.list-h .lbl{font-family:var(--mono);font-size:10.5px;letter-spacing:.05em;
  text-transform:uppercase;color:var(--faint);font-weight:700;flex:none}
.list-h .rule{flex:1;height:1px;background:var(--line)}
.list{padding:6px 0 4px}
.item{display:grid;grid-template-columns:44px minmax(0,1fr);gap:16px;padding:22px 0;
  border-top:1px solid var(--line);color:inherit}
.item:hover{text-decoration:none}
.item:hover .t{color:var(--accent)}
.no{font-family:var(--mono);font-size:13px;color:var(--faint);font-weight:600;padding-top:3px}
.t{font-size:19px;font-weight:700;margin:0 0 7px;letter-spacing:-.018em;line-height:1.42;
  color:var(--fg);transition:color .15s;word-break:keep-all}
.ex{color:var(--dim);font-size:15.5px;line-height:1.7;margin:0}
.meta{font-family:var(--mono);font-size:11.5px;color:var(--faint);margin-top:9px}
.item .part{font-family:var(--mono);font-size:10.5px;color:var(--accent);
  letter-spacing:.06em;margin-bottom:5px;display:block}

.up{border-top:1px solid var(--line);padding:22px 0 72px}
.up-h{font-family:var(--mono);font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;
  color:var(--faint);font-weight:700;margin-bottom:12px}
.up-l{display:flex;flex-wrap:wrap;gap:8px;list-style:none;padding:0;margin:0}
.up-l li{font-size:14px;color:var(--ghost);border:1px dashed var(--line2);border-radius:8px;
  padding:6px 12px;line-height:1.5;word-break:keep-all}
.up-l li .n{font-family:var(--mono);font-size:11px;margin-right:7px;color:#c5ccd6}

/* ── article ─────────────────────────────────────── */
article{padding:34px 0 40px;max-width:720px}
.a-kicker{font-family:var(--mono);font-size:11.5px;letter-spacing:.11em;color:var(--accent);
  text-transform:uppercase;font-weight:650;margin-bottom:14px}
.a-kicker .sep{color:var(--line2);margin:0 7px}
article h1{font-size:31px;line-height:1.34;margin:0 0 14px;letter-spacing:-.03em;font-weight:750}
.a-meta{font-family:var(--mono);font-size:12px;color:var(--faint);
  padding-bottom:12px;border-bottom:1px solid var(--line);margin-bottom:34px}
.a-rail{display:flex;align-items:center;gap:10px;margin:0 0 12px}
.a-rail .bar{flex:1;height:3px;background:var(--line);border-radius:2px;overflow:hidden}
.a-rail .bar i{display:block;height:100%;background:var(--accent)}
.a-rail .pos{font-family:var(--mono);font-size:10.5px;color:var(--faint);flex:none;
  letter-spacing:.04em}
.body h2{font-size:21px;margin:46px 0 14px;letter-spacing:-.02em;font-weight:750;line-height:1.42;
  padding-top:4px}
.body h3{font-size:18px;margin:32px 0 10px;font-weight:700}
.body p{margin:0 0 21px}
.body strong{font-weight:750}
.body em{color:var(--dim);font-style:italic}
.body ul,.body ol{padding-left:22px;margin:0 0 21px}
.body li{margin-bottom:7px}
.body blockquote{margin:26px 0;padding:16px 20px;background:var(--alt);
  border-left:3px solid var(--accent);border-radius:0 6px 6px 0;color:var(--dim)}
.body blockquote p{margin:0 0 10px}
.body blockquote p:last-child{margin:0}
.body code{font-family:var(--mono);font-size:.87em;background:var(--alt);
  border:1px solid var(--line);border-radius:4px;padding:1.5px 6px;color:#0f5bb5}
.body pre{background:var(--alt);border:1px solid var(--line);border-radius:8px;
  padding:16px 18px;overflow-x:auto;margin:24px 0}
.body pre code{background:none;border:0;padding:0;font-size:13.5px;line-height:1.7}
.body hr{border:0;border-top:1px solid var(--line);margin:40px 0}
.body img{max-width:100%;height:auto;border-radius:6px;margin:24px 0;border:1px solid var(--line)}
.body table{width:100%;border-collapse:collapse;margin:24px 0;font-size:15.5px;
  display:block;overflow-x:auto}
.body th,.body td{border:1px solid var(--line);padding:9px 12px;text-align:left}
.body th{background:var(--alt);font-weight:700}

/* 이전/다음 */
.pnav{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;
  border-top:1px solid var(--line);padding:26px 0 0;margin-top:44px}
.nv{display:block;min-width:0;border:1px solid var(--line);border-radius:10px;
  padding:13px 15px;color:inherit}
a.nv:hover{border-color:var(--accent);background:var(--accent-soft);text-decoration:none}
.nv.next{text-align:right}
.nv .lbl{display:block;font-family:var(--mono);font-size:10px;color:var(--faint);
  letter-spacing:.12em;text-transform:uppercase;margin-bottom:6px;font-weight:700}
.nv .nt{font-size:14.5px;font-weight:700;line-height:1.5;letter-spacing:-.015em;color:var(--fg);
  word-break:keep-all}
a.nv:hover .nt{color:var(--accent)}
.nv.off{border-style:dashed}
.nv.off .nt{color:var(--ghost);font-weight:650}
.nv.blank{border:0;padding:0}
.a-back{text-align:center;margin-top:20px;font-family:var(--mono);font-size:11.5px;
  letter-spacing:.04em}

footer{border-top:1px solid var(--line);margin-top:56px;padding:24px 0 44px;
  color:var(--faint);font-size:12.5px;font-family:var(--mono)}

/* ── 태블릿/모바일 ───────────────────────────────── */
@media(max-width:900px){
  .shell{grid-template-columns:minmax(0,1fr);gap:0}
  aside{position:static;padding:18px 0 0;max-height:none;overflow:visible;
    border-bottom:1px solid var(--line);margin-bottom:4px;padding-bottom:18px}
  /* 모바일에서는 목차 전체를 접는다 (체크박스 토글, JS 없음) */
  .toc-bar{margin-bottom:0;border:1px solid var(--line);border-radius:9px;
    padding:11px 13px;background:var(--alt);cursor:pointer;
    -webkit-tap-highlight-color:transparent}
  .toc-bar .side-h{flex:1}
  .cv{display:block;transition:transform .18s}
  .toc-cb:checked ~ .toc-bar{border-color:var(--accent);background:var(--accent-soft)}
  .toc-cb:checked ~ .toc-bar .cv{transform:rotate(180deg);color:var(--accent)}
  .toc-cb:focus-visible ~ .toc-bar{outline:2px solid var(--accent);outline-offset:2px}
  .toc-panel{display:none;padding-top:14px}
  .toc-cb:checked ~ .toc-panel{display:block}
  .items a,.items .soon{padding:9px 0 9px 12px}
  .pt>summary{padding:12px 2px}
  article{padding-top:24px}
}
@media(max-width:760px){
  .flow{grid-template-columns:minmax(0,1fr);gap:28px}
  .step::after{content:"↓";right:auto;left:24px;top:auto;bottom:-21px;transform:none}
}
@media(max-width:640px){
  body{font-size:16.5px}
  .shell,.solo,.hd{padding:0 18px}
  .hero{padding:32px 0 22px}
  .hero h1{font-size:26px}
  article h1{font-size:25px}
  .body h2{font-size:19.5px}
  .t{font-size:17.5px}
  .item{grid-template-columns:32px minmax(0,1fr);gap:12px}
  nav.top a{margin-left:13px;font-size:13px}
  .sum{padding:20px 17px 22px;border-radius:11px;margin-bottom:34px}
  .sum-lead{font-size:17.5px}
  .sum-sub{font-size:15px;margin-bottom:22px}
  .sum-h .wip{display:none}
  .cmp{grid-template-columns:minmax(0,1fr)}
  .pnav{grid-template-columns:minmax(0,1fr)}
  .nv.next{text-align:left}
  .nv.blank{display:none}
}
"""

HEAD = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{TITLE}}</title>
<meta name="description" content="{{DESC}}">
<meta property="og:title" content="{{TITLE}}">
<meta property="og:description" content="{{DESC}}">
<meta property="og:type" content="{{OGTYPE}}">
<meta name="theme-color" content="#ffffff">
<link rel="icon" href="/assets/logo.png">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<style>{{CSS}}</style>
</head>
<body>
<header><div class="hd">
  <a class="brand" href="/">Numpilot</a>
  <nav class="top"><a href="/">블로그</a><a href="/about/">소개</a></nav>
</div></header>
"""

FOOT = """<footer><div class="solo">© Numpilot</div></footer>
</body></html>
"""

CHEV = ('<svg class="{cls}" width="11" height="11" viewBox="0 0 12 12" fill="none" '
        'aria-hidden="true"><path d="M2.5 4.5 6 8l3.5-3.5" stroke="currentColor" '
        'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')


# ── OUTLINE.md 파싱 ──────────────────────────────────────────────
PART_RE = re.compile(r"^##\s*(\d+)\s*부[.·]?\s*(.+?)\s*$")
ITEM_RE = re.compile(r"^(\d+)\.\s+(.+?)\s*$")


def clean_title(s):
    """목차 표기용 장식(✅ ⭐ 범위표기) 제거."""
    s = re.sub(r"\((\d+)\s*[~\-–]\s*(\d+)\)", "", s)      # (6~13)
    s = re.sub(r"[✅⭐️★☆]+\s*핵심", "", s)
    s = re.sub(r"[✅⭐️★☆✔︎✓🔥]+", "", s)
    return re.sub(r"\s+", " ", s).strip(" ·—-")


def parse_outline():
    """OUTLINE.md → [{'no':1,'title':'문제','eps':[(1,'제목'), ...]}, ...]

    파일이 없거나 형식이 어긋나면 빈 리스트를 돌려주고, 호출부가 평면 목차로 대체한다.
    """
    if not os.path.exists(OUTLINE):
        return []
    parts, cur = [], None
    for line in open(OUTLINE, encoding="utf-8").read().splitlines():
        m = PART_RE.match(line)
        if m:
            cur = {"no": int(m.group(1)), "title": clean_title(m.group(2)), "eps": []}
            parts.append(cur)
            continue
        if line.startswith("## "):        # '논문 씨앗' 등 부가 섹션 → 수집 중단
            cur = None
            continue
        if cur is not None:
            mi = ITEM_RE.match(line)
            if mi:
                cur["eps"].append((int(mi.group(1)), clean_title(mi.group(2))))
    return [p for p in parts if p["eps"]]


def build_groups(posts, outline):
    """부 단위 그룹 + 각 편의 발행 여부를 합친 목차 트리를 만든다."""
    if not outline:      # OUTLINE.md 부재 시 평면 목차로 대체
        return [{"no": None, "title": SERIES,
                 "eps": [{"ep": int(p["ep"] or 0), "title": p["title"],
                          "slug": p["slug"], "post": p} for p in posts]}]
    by_ep = {int(p["ep"] or 0): p for p in posts}
    used, groups = set(), []
    for part in outline:
        eps = []
        for ep, title in part["eps"]:
            p = by_ep.get(ep)
            if p:
                used.add(ep)
            eps.append({"ep": ep, "title": (p["title"] if p else title),
                        "slug": (p["slug"] if p else None), "post": p})
        groups.append({"no": part["no"], "title": part["title"], "eps": eps})
    # 목차에 없는 원고는 유실되지 않도록 뒤에 모아 붙인다.
    extra = [p for p in posts if int(p["ep"] or 0) not in used]
    if extra:
        groups.append({"no": None, "title": "그 외",
                       "eps": [{"ep": int(p["ep"] or 0), "title": p["title"],
                                "slug": p["slug"], "post": p} for p in extra]})
    return groups


def part_of(groups, ep):
    for g in groups:
        for e in g["eps"]:
            if e["ep"] == ep:
                return g
    return None


# ── 목차 렌더 ────────────────────────────────────────────────────
def toc_html(groups, current=None):
    """좌측 연재 목차. current = 현재 글 slug (없으면 메인)."""
    total = sum(len(g["eps"]) for g in groups)
    done = sum(1 for g in groups for e in g["eps"] if e["slug"])
    pct = int(round(done * 100.0 / total)) if total else 0

    # 어느 부를 펼칠지: 현재 글이 속한 부, 메인이면 가장 최근 발행 편이 속한 부
    open_part = None
    if current:
        for g in groups:
            if any(e["slug"] == current for e in g["eps"]):
                open_part = g["no"]
    else:
        for g in groups:
            if any(e["slug"] for e in g["eps"]):
                open_part = g["no"]

    o = ['<aside>',
         '<input type="checkbox" id="toctoggle" class="toc-cb">',
         '<label class="toc-bar" for="toctoggle">',
         '<span class="side-h">연재 목차</span>',
         f'<span class="toc-n">{done}/{total}</span>',
         CHEV.format(cls="cv"),
         '</label>',
         '<div class="toc-panel">',
         '<div class="prog"><div class="bar">',
         f'<i style="width:{pct}%"></i></div>',
         f'<div class="t">전체 {total}편 중 {done}편 발행</div></div>',
         '<div class="toc">']

    for g in groups:
        gdone = sum(1 for e in g["eps"] if e["slug"])
        is_cur = bool(current) and any(e["slug"] == current for e in g["eps"])
        opened = " open" if g["no"] == open_part or is_cur else ""
        cls = "pt cur" if is_cur else "pt"
        label = (f'<span class="pn">{g["no"]}부</span>' if g["no"]
                 else '<span class="pn">·</span>')
        o.append(f'<details class="{cls}"{opened}><summary>{label}'
                 f'<span class="ptt">{html.escape(g["title"])}</span>'
                 f'<span class="pc">{gdone}/{len(g["eps"])}</span>'
                 + CHEV.format(cls="pcv") + '</summary><ul class="items">')
        for e in g["eps"]:
            n = f'<span class="n">{e["ep"]:02d}</span>'
            t = html.escape(e["title"])
            if e["slug"]:
                on = ' class="on" aria-current="page"' if e["slug"] == current else ""
                o.append(f'<li><a{on} href="/blog/{e["slug"]}/">{n}{t}</a></li>')
            else:
                o.append(f'<li><span class="soon" title="연재 예정">{n}{t}</span></li>')
        o.append('</ul></details>')

    o.append('</div>')
    o.append('<div class="toc-foot"><span class="dash"></span>회색은 연재 예정 편</div>')
    o.append('</div></aside>')
    return "".join(o)


def parse(path):
    raw = open(path, encoding="utf-8").read()
    meta, body = {}, raw
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"').strip("'")
        body = m.group(2)
    # 본문 첫 h1은 제목과 중복이므로 제거
    body = re.sub(r"^\s*#\s+.*?\n", "", body, count=1)
    # 제목 바로 아래 이탤릭 메타줄 제거
    body = re.sub(r"^\s*\*[^\n]*읽는 데[^\n]*\*\s*\n", "", body, count=1)
    return meta, body


def excerpt(body, n=110):
    txt = re.sub(r"[#>*_`\[\]()!-]", "", body)
    txt = re.sub(r"\s+", " ", txt).strip()
    return (txt[:n] + "…") if len(txt) > n else txt


# ── 핵심 요약 섹션 ───────────────────────────────────────────────
def summary_html():
    """메인 상단 '핵심 요약' — 3단 흐름 + 대비 카드. 순수 HTML/CSS."""
    return """
<section class="sum">
  <div class="sum-h"><span class="lbl">핵심 요약</span><span class="rule"></span>
    <span class="wip">개발 중</span></div>

  <p class="sum-lead">수치해석은 원래 큰 화면이 필요한 작업이다.
    그런데 지금의 기술은 <b>한 문장으로 지시하고, 그 아래에서 복잡한 연산이 돌고,
    다시 한눈에 읽히는 형태로 보고되는</b> 방향으로 가고 있다.</p>
  <p class="sum-sub">번역, 검색, 코드 작성이 이미 그 길을 지났다. 사용자가 다루는 표면은
    문장 한 줄로 얇아졌지만, 그 아래의 연산은 오히려 더 무거워졌다.
    Numpilot은 이 구조를 수치해석에 적용한다.</p>

  <div class="flow">
    <div class="step">
      <span class="sn">Step 01 · 말한다</span>
      <h3>질문은 한 문장으로</h3>
      <span class="say">알루미늄 팬에 페놀수지 손잡이를 달면 손잡이가 뜨거워질까?</span>
      <p>CAD 파일도, 격자 설정 화면도, 물성 테이블도 먼저 열지 않는다.
        엔지니어가 동료에게 묻는 방식 그대로 쓴다.</p>
    </div>
    <div class="step mid">
      <span class="sn">Step 02 · 풀어낸다</span>
      <h3>복잡함은 아래로 내린다</h3>
      <ul class="gears">
        <li>자연어 → DSL 번역</li>
        <li>형상·물성·경계조건 확정</li>
        <li>격자 생성, 지배방정식 이산화</li>
        <li>반복 계산과 수렴 판정</li>
        <li>결과 검증</li>
      </ul>
      <p>이 단계는 줄어들지 않는다. 사용자 눈에 보이지 않게 옮겨질 뿐이다.
        어디서 계산할지, 무엇을 포기할지가 이 연재의 중심 주제다.</p>
    </div>
    <div class="step">
      <span class="sn">Step 03 · 읽는다</span>
      <h3>답은 판단할 수 있는 크기로</h3>
      <ul class="out">
        <li>손잡이가 위험해지는가</li>
        <li>언제부터 그렇게 되는가</li>
        <li>어디를 바꾸면 달라지는가</li>
      </ul>
      <p>수만 개 격자점의 온도장을 다 보여주는 것이 목적이 아니다.
        질문에 대응하는 답만 남긴다.</p>
    </div>
  </div>

  <div class="cmp">
    <div class="c cut">
      <h4>얇아지는 것 — 사람이 감당하는 폭</h4>
      <ul>
        <li>입력: 설정 화면 수십 개 → 문장 한 줄</li>
        <li>출력: 전체 결과장 → 판단에 필요한 몇 가지</li>
        <li>장비: 워크스테이션과 큰 화면 → 손안의 기기</li>
      </ul>
    </div>
    <div class="c keep">
      <h4>얇아지지 않는 것 — 계산의 실체</h4>
      <ul>
        <li>지배방정식과 경계조건</li>
        <li>격자와 반복 계산</li>
        <li>답이 맞다는 것을 확인하는 절차</li>
      </ul>
    </div>
  </div>

  <p class="sum-close"><span class="th">그래서 이 연재는</span>
    계산을 줄이는 이야기가 아니다. 계산은 그대로 두고,
    <strong>사람이 물리를 기술하는 언어를 새로 설계하는</strong> 이야기다.
    문제 정의(1부)에서 DSL 설계(2부), 해석의 기초(3부), AI로의 확장(4부)을 지나
    제품(5부)까지, 만들면서 겪은 판단을 순서대로 기록한다.</p>
</section>
"""


def render(tpl, **kw):
    out = tpl
    for k, v in kw.items():
        out = out.replace("{{%s}}" % k, v)
    return out


def main():
    os.makedirs(POSTS_DIR, exist_ok=True)
    md = markdown.Markdown(extensions=["extra", "sane_lists", "smarty"])

    posts = []
    for fn in sorted(os.listdir(POSTS_DIR)):
        if not fn.endswith(".md"):
            continue
        meta, body = parse(os.path.join(POSTS_DIR, fn))
        md.reset()
        posts.append({
            "slug": os.path.splitext(fn)[0],
            "title": meta.get("title", fn),
            "ep": meta.get("episode", ""),
            "rt": meta.get("reading_time", ""),
            "date": meta.get("date", ""),
            "html": md.convert(body),
            "excerpt": excerpt(body),
        })
    posts.sort(key=lambda p: int(p["ep"] or 0))

    outline = parse_outline()
    groups = build_groups(posts, outline)
    total_eps = sum(len(g["eps"]) for g in groups)

    # 편 번호 → 목차 항목 (예정 편 포함). 이전/다음 내비게이션에 쓴다.
    seq = [e for g in groups for e in g["eps"]]
    seq.sort(key=lambda e: e["ep"])
    pos_of = {e["ep"]: i for i, e in enumerate(seq)}

    # ── 각 글 페이지 ──
    for p in posts:
        ep = int(p["ep"] or 0)
        g = part_of(groups, ep)
        i = pos_of.get(ep, 0)
        prev = seq[i - 1] if i > 0 else None
        nxt = seq[i + 1] if i < len(seq) - 1 else None

        def card(e, kind, lbl):
            if not e:
                return f'<span class="nv blank"></span>'
            n = f'{e["ep"]:02d}. {html.escape(e["title"])}'
            if e["slug"]:
                return (f'<a class="nv {kind}" href="/blog/{e["slug"]}/">'
                        f'<span class="lbl">{lbl}</span><span class="nt">{n}</span></a>')
            return (f'<span class="nv {kind} off"><span class="lbl">{lbl} · 연재 예정</span>'
                    f'<span class="nt">{n}</span></span>')

        nav = ('<div class="pnav">' + card(prev, "prev", "이전 편")
               + card(nxt, "next", "다음 편") + '</div>'
               + '<div class="a-back"><a href="/">← 연재 목차 전체 보기</a></div>')

        crumb = SERIES
        if g and g["no"]:
            crumb += f'<span class="sep">/</span>{g["no"]}부 {html.escape(g["title"])}'
        pct = int(round(ep * 100.0 / total_eps)) if total_eps else 0

        page = render(HEAD, TITLE=f'{p["title"]} — {SITE}', DESC=p["excerpt"],
                      OGTYPE="article", CSS=CSS)
        page += (f'<div class="shell">{toc_html(groups, p["slug"])}<main><article>'
                 f'<div class="a-kicker">{crumb}</div>'
                 f'<h1>{html.escape(p["title"])}</h1>'
                 f'<div class="a-rail"><span class="pos">{ep:02d} / {total_eps}</span>'
                 f'<span class="bar"><i style="width:{pct}%"></i></span></div>'
                 f'<div class="a-meta">{p["date"]} · 읽는 데 {p["rt"]}</div>'
                 f'<div class="body">{p["html"]}</div>{nav}</article></main></div>')
        page += FOOT
        d = os.path.join(BLOG_DIR, p["slug"])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page)

    # ── 블로그 메인 ──
    idx = render(HEAD, TITLE=f"{SITE} — {TAGLINE}", DESC=SERIES_BLURB,
                 OGTYPE="website", CSS=CSS)
    idx += (f'<div class="shell">{toc_html(groups)}<main><section class="hero">'
            f'<div class="kicker">연재 · {SERIES}</div>'
            f'<h1>{TAGLINE}</h1><p>{SERIES_BLURB}</p></section>')
    idx += summary_html()
    idx += ('<div class="list-h"><span class="lbl">발행된 글 '
            f'{len(posts)}편</span><span class="rule"></span></div>'
            '<section class="list">')
    for p in posts:
        g = part_of(groups, int(p["ep"] or 0))
        pl = (f'<span class="part">{g["no"]}부 {html.escape(g["title"])}</span>'
              if g and g["no"] else "")
        idx += (f'<a class="item" href="/blog/{p["slug"]}/">'
                f'<div class="no">{int(p["ep"] or 0):02d}</div>'
                f'<div>{pl}<div class="t">{html.escape(p["title"])}</div>'
                f'<p class="ex">{p["excerpt"]}</p>'
                f'<div class="meta">{p["date"]} · {p["rt"]}</div></div></a>')
    if not posts:
        idx += '<p class="ex" style="padding:40px 0">아직 발행된 글이 없습니다.</p>'
    idx += "</section>"

    upcoming = [e for e in seq if not e["slug"]][:4]
    if upcoming:
        idx += '<section class="up"><div class="up-h">다음 편 예고</div><ul class="up-l">'
        for e in upcoming:
            idx += (f'<li><span class="n">{e["ep"]:02d}</span>'
                    f'{html.escape(e["title"])}</li>')
        idx += ('</ul><div class="toc-foot" style="margin-top:14px">'
                f'전체 {total_eps}편 구성은 왼쪽 연재 목차에서 볼 수 있습니다.'
                '</div></section>')
    idx += "</main></div>" + FOOT
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(idx)

    print(f"빌드 완료: {len(posts)}편 발행 / 목차 {total_eps}편 "
          f"({len(groups)}개 그룹)")
    for g in groups:
        gd = sum(1 for e in g["eps"] if e["slug"])
        head = f'{g["no"]}부 {g["title"]}' if g["no"] else g["title"]
        print(f'  [{head}] {gd}/{len(g["eps"])}')
    for p in posts:
        print(f"  {int(p['ep'] or 0):02d}  /blog/{p['slug']}/  {p['title']}")


if __name__ == "__main__":
    main()
