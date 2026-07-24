#!/usr/bin/env python3
"""NumPilot 블로그 빌드 — posts/*.md 를 읽어 정적 HTML 생성.

사용법:  python3 build.py
출력:    index.html (블로그 메인), blog/<slug>/index.html (각 글)
"""
import os, re, sys, html, json
import markdown

ROOT = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR = os.path.join(ROOT, "posts")
BLOG_DIR = os.path.join(ROOT, "blog")

SITE = "Numpilot"
TAGLINE = "말로 설명하면, 폰이 풀어낸다"
SERIES = "손안의 수치해석"
SERIES_BLURB = ("수치해석을 휴대폰에서 하겠다는 무모한 결정, 그리고 그것을 가능하게 만들기 위해 "
                "우리가 설계해야 했던 언어에 대한 기록.")

CSS = """
:root{
  --bg:#ffffff; --alt:#f7f9fb; --line:#e5e9ef; --line2:#d3dae3;
  --fg:#1a2029; --dim:#5b6675; --faint:#8d97a5;
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
  grid-template-columns:236px minmax(0,1fr);gap:56px;align-items:start}
.solo{max-width:1120px;margin:0 auto;padding:0 26px}

header{border-bottom:1px solid var(--line);background:var(--bg);position:sticky;top:0;z-index:30}
.hd{max-width:1120px;margin:0 auto;padding:0 26px;display:flex;align-items:center;
  justify-content:space-between;height:58px}
.brand{font-size:16px;font-weight:750;letter-spacing:-.02em;color:var(--fg)}
.brand:hover{text-decoration:none}
nav a{font-size:14px;color:var(--dim);margin-left:20px}
nav a:hover{color:var(--accent);text-decoration:none}

/* 사이드바 목차 */
aside{position:sticky;top:82px;padding:34px 0 40px;font-size:14px}
.side-h{font-family:var(--mono);font-size:11px;letter-spacing:.14em;color:var(--faint);
  text-transform:uppercase;margin-bottom:14px;font-weight:600}
.toc{list-style:none;margin:0;padding:0;border-left:2px solid var(--line);}
.toc li{margin:0}
.toc a{display:block;padding:7px 0 7px 14px;color:var(--dim);line-height:1.5;
  margin-left:-2px;border-left:2px solid transparent}
.toc a:hover{color:var(--accent);text-decoration:none;background:var(--accent-soft)}
.toc a.on{color:var(--accent);font-weight:650;border-left-color:var(--accent);
  background:var(--accent-soft)}
.toc .n{font-family:var(--mono);font-size:11.5px;color:var(--faint);margin-right:7px}
.toc a.on .n{color:var(--accent)}

/* index */
.hero{padding:52px 0 30px}
.kicker{display:inline-block;font-family:var(--mono);font-size:11px;letter-spacing:.14em;
  color:var(--accent);text-transform:uppercase;font-weight:650;
  background:var(--accent-soft);padding:5px 10px;border-radius:4px;margin-bottom:18px}
.hero h1{font-size:34px;line-height:1.32;margin:0 0 16px;letter-spacing:-.028em;font-weight:750}
.hero p{color:var(--dim);font-size:16.5px;margin:0;max-width:42em;line-height:1.75}
.list{padding:6px 0 80px}
.item{display:grid;grid-template-columns:44px 1fr;gap:16px;padding:22px 0;
  border-top:1px solid var(--line);color:inherit}
.item:hover{text-decoration:none}
.item:hover .t{color:var(--accent)}
.no{font-family:var(--mono);font-size:13px;color:var(--faint);font-weight:600;padding-top:3px}
.t{font-size:19px;font-weight:700;margin:0 0 7px;letter-spacing:-.018em;line-height:1.42;
  color:var(--fg);transition:color .15s}
.ex{color:var(--dim);font-size:15.5px;line-height:1.7;margin:0}
.meta{font-family:var(--mono);font-size:11.5px;color:var(--faint);margin-top:9px}

/* article */
article{padding:34px 0 40px;max-width:720px}
.a-kicker{font-family:var(--mono);font-size:11.5px;letter-spacing:.13em;color:var(--accent);
  text-transform:uppercase;font-weight:650;margin-bottom:14px}
article h1{font-size:31px;line-height:1.34;margin:0 0 14px;letter-spacing:-.03em;font-weight:750}
.a-meta{font-family:var(--mono);font-size:12px;color:var(--faint);
  padding-bottom:24px;border-bottom:1px solid var(--line);margin-bottom:34px}
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

.pnav{display:flex;justify-content:space-between;gap:16px;
  border-top:1px solid var(--line);padding:24px 0 0;margin-top:44px}
.pnav a{font-size:15px;max-width:46%;font-weight:600}
.pnav .lbl{display:block;font-family:var(--mono);font-size:10.5px;color:var(--faint);
  letter-spacing:.12em;text-transform:uppercase;margin-bottom:5px;font-weight:600}
footer{border-top:1px solid var(--line);margin-top:56px;padding:24px 0 44px;
  color:var(--faint);font-size:12.5px;font-family:var(--mono)}

@media(max-width:900px){
  .shell{grid-template-columns:1fr;gap:0}
  aside{position:static;padding:22px 0 6px;border-bottom:1px solid var(--line);margin-bottom:8px}
  .toc{display:flex;gap:6px;overflow-x:auto;border-left:0;padding-bottom:6px}
  .toc a{white-space:nowrap;border:1px solid var(--line);border-radius:20px;
    padding:5px 12px;margin:0}
  .toc a.on{border-color:var(--accent)}
  article{padding-top:26px}
}
@media(max-width:640px){
  body{font-size:16.5px}
  .hero{padding:36px 0 24px}
  .hero h1{font-size:26px}
  article h1{font-size:25px}
  .body h2{font-size:19.5px}
  .t{font-size:17.5px}
  .item{grid-template-columns:34px 1fr;gap:12px}
  nav a{margin-left:13px;font-size:13px}
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
  <nav><a href="/">블로그</a><a href="/about/">소개</a></nav>
</div></header>
"""

FOOT = """<footer><div class="solo">© Numpilot</div></footer>
</body></html>
"""


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



def toc_html(posts, current=None):
    """좌측 연재 목차."""
    out = ['<aside><div class="side-h">연재 목차</div><ul class="toc">']
    for q in posts:
        cls = ' class="on"' if current and q["slug"] == current else ""
        out.append(f'<li><a{cls} href="/blog/{q["slug"]}/">'
                   f'<span class="n">{int(q["ep"] or 0):02d}</span>{html.escape(q["title"])}</a></li>')
    out.append("</ul></aside>")
    return "".join(out)


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

    # 각 글 페이지
    for i, p in enumerate(posts):
        prev = posts[i - 1] if i > 0 else None
        nxt = posts[i + 1] if i < len(posts) - 1 else None
        nav = '<div class="pnav">'
        nav += (f'<a href="/blog/{prev["slug"]}/"><span class="lbl">이전</span>{html.escape(prev["title"])}</a>'
                if prev else "<span></span>")
        nav += (f'<a href="/blog/{nxt["slug"]}/" style="text-align:right"><span class="lbl">다음</span>{html.escape(nxt["title"])}</a>'
                if nxt else "<span></span>")
        nav += "</div>"

        page = render(HEAD, TITLE=f'{p["title"]} — {SITE}', DESC=p["excerpt"],
                      OGTYPE="article", CSS=CSS)
        page += (f'<div class="shell">{toc_html(posts, p["slug"])}<main><article>'
                 f'<div class="a-kicker">{SERIES} · {p["ep"]}편</div>'
                 f'<h1>{html.escape(p["title"])}</h1>'
                 f'<div class="a-meta">{p["date"]} · 읽는 데 {p["rt"]}</div>'
                 f'<div class="body">{p["html"]}</div>{nav}</article></main></div>')
        page += FOOT
        d = os.path.join(BLOG_DIR, p["slug"])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page)

    # 블로그 메인
    idx = render(HEAD, TITLE=f"{SITE} — {TAGLINE}", DESC=SERIES_BLURB,
                 OGTYPE="website", CSS=CSS)
    idx += (f'<div class="shell">{toc_html(posts)}<main><section class="hero">'
            f'<div class="kicker">연재 · {SERIES}</div>'
            f'<h1>{TAGLINE}</h1><p>{SERIES_BLURB}</p></section><section class="list">')
    for p in posts:
        idx += (f'<a class="item" href="/blog/{p["slug"]}/">'
                f'<div class="no">{int(p["ep"] or 0):02d}</div>'
                f'<div><div class="t">{html.escape(p["title"])}</div>'
                f'<p class="ex">{p["excerpt"]}</p>'
                f'<div class="meta">{p["date"]} · {p["rt"]}</div></div></a>')
    if not posts:
        idx += '<p class="ex" style="padding:40px 0">아직 발행된 글이 없습니다.</p>'
    idx += "</section></main></div>" + FOOT
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(idx)

    print(f"빌드 완료: {len(posts)}편")
    for p in posts:
        print(f"  {int(p['ep'] or 0):02d}  /blog/{p['slug']}/  {p['title']}")


if __name__ == "__main__":
    main()
