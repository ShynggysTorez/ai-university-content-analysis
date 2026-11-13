#!/usr/bin/env python3
"""
Локальный парсинг сайтов вузов Казахстана (без сервера Constructor).

1. Забирает с панели Constructor ссылки и уже распарсенные страницы по 4 batch.
2. Скачивает и парсит оставшиеся ссылки на этом компьютере
   (HTML -> текст, PDF -> текст, DOCX -> текст).
3. Сохраняет итог: kz_ai_v2_final.json (формат как у Constructor) + kz_ai_v2_final.csv.

Запуск:  python3 parse_kz_local.py
Можно прерывать (Ctrl+C) и запускать снова — продолжит с того же места.
"""
import concurrent.futures as cf
import csv
import io
import json
import os
import re
import subprocess
import sys
import threading
import time
import warnings
warnings.filterwarnings("ignore")
import logging
logging.getLogger("pypdf").setLevel(logging.ERROR)
from datetime import datetime
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "data_kz_v2")
os.makedirs(OUT_DIR, exist_ok=True)

PANEL = "https://98d8c2773701465a9a40cee38a55251f.constructor.pro"
BATCHES = [
    "serper_collection_20261113_045119_34e50fb7",
    "serper_collection_20261113_045119_2071fe14",
    "serper_collection_20261113_045119_04e6a9ca",
    "serper_collection_20261113_045119_243b27cd",
]
WORKERS = 16
TIMEOUT = 25
MAX_BYTES = 30 * 1024 * 1024  # не качаем файлы больше 30 МБ
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def ensure(pkgs):
    missing = []
    for mod, pip_name in pkgs:
        try:
            __import__(mod)
        except ImportError:
            missing.append(pip_name)
    if missing:
        print("Устанавливаю пакеты:", ", ".join(missing))
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "--user", *missing])


ensure([("requests", "requests"), ("trafilatura", "trafilatura"),
        ("pypdf", "pypdf"), ("docx", "python-docx"), ("bs4", "beautifulsoup4")])

import requests  # noqa: E402
import trafilatura  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402
from pypdf import PdfReader  # noqa: E402
import docx  # noqa: E402

requests.packages.urllib3.disable_warnings()  # у части вузов кривые сертификаты


# ---------------------------------------------------------------- 1. выгрузка с панели
def export_batch(batch_id):
    path = os.path.join(OUT_DIR, f"export_{batch_id}.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    print(f"Скачиваю с панели {batch_id} ...")
    r = requests.post(f"{PANEL}/api/results/export/json",
                      json={"batch_id": batch_id, "include_links": True, "include_parsed": True},
                      timeout=300)
    r.raise_for_status()
    data = r.json()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return data


# ---------------------------------------------------------------- 2. парсинг
def detect_lang(text):
    t = text[:5000]
    kk = len(re.findall(r"[әғқңөұүһі]", t.lower()))
    cyr = len(re.findall(r"[а-яё]", t.lower()))
    lat = len(re.findall(r"[a-z]", t.lower()))
    if cyr + lat == 0:
        return None
    if cyr >= lat:
        return "kk" if kk > 0.01 * cyr else "ru"
    return "en"


def kind_of(url, ctype):
    u = url.lower().split("?")[0]
    c = (ctype or "").lower()
    if u.endswith(".pdf") or "pdf" in c:
        return "pdf"
    if u.endswith(".docx") or "wordprocessingml" in c:
        return "docx"
    if u.endswith(".doc") or "msword" in c:
        return "doc"
    if re.search(r"\.(pptx?|xlsx?)$", u) or "presentation" in c or "spreadsheet" in c or "ms-excel" in c:
        return "office_other"
    return "html"


def text_from_pdf(b):
    reader = PdfReader(io.BytesIO(b))
    pages = []
    for p in reader.pages[:300]:
        try:
            pages.append(p.extract_text() or "")
        except Exception:
            pass
    return "\n".join(pages), (reader.metadata.title if reader.metadata and reader.metadata.title else None)


def text_from_docx(b):
    d = docx.Document(io.BytesIO(b))
    parts = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            parts.append(" | ".join(c.text for c in row.cells))
    return "\n".join(x for x in parts if x.strip())


def text_from_html(html, url):
    txt = trafilatura.extract(html, url=url, include_tables=True, include_comments=False, favor_recall=True)
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else None
    if not txt:
        for s in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            s.decompose()
        txt = soup.get_text("\n", strip=True)
    return txt or "", title


session_local = threading.local()


def get_session():
    if not hasattr(session_local, "s"):
        s = requests.Session()
        s.headers.update({"User-Agent": UA, "Accept-Language": "ru,kk;q=0.9,en;q=0.8"})
        session_local.s = s
    return session_local.s


def parse_one(link):
    url = link["url"]
    rec = {
        "link_id": link.get("link_id"),
        "batch_id": link.get("batch_id"),
        "domain_filter": link.get("domain_filter"),
        "query_text": link.get("query_text"),
        "url": url,
        "search_title": link.get("title"),
        "snippet": link.get("snippet"),
        "parsed_at": datetime.now().isoformat(),
        "parser": "local",
    }
    try:
        r = get_session().get(url, timeout=TIMEOUT, verify=False, stream=True, allow_redirects=True)
        ctype = r.headers.get("Content-Type", "")
        body = b""
        t_start = time.time()
        for chunk in r.iter_content(65536):
            body += chunk
            if len(body) > MAX_BYTES or time.time() - t_start > 90:
                break
        r.close()
        rec.update({"http_status_code": r.status_code, "final_url": r.url, "content_type": ctype})
        if r.status_code >= 400:
            rec.update({"parse_status": "http_error", "content_text": "", "word_count": 0, "has_useful_content": False})
            return rec
        kind = kind_of(r.url, ctype)
        rec["doc_type"] = kind
        title = None
        if kind == "pdf":
            text, title = text_from_pdf(body)
        elif kind == "docx":
            text = text_from_docx(body)
        elif kind in ("doc", "office_other"):
            text = ""  # старый .doc/.ppt/.xls — только ссылка и сниппет
            rec["parse_status"] = "unsupported_format"
        else:
            enc = r.encoding if r.encoding and r.encoding.lower() != "iso-8859-1" else r.apparent_encoding
            html = body.decode(enc or "utf-8", errors="replace")
            text, title = text_from_html(html, r.url)
        text = re.sub(r"\n{3,}", "\n\n", text or "").strip()
        wc = len(text.split())
        rec.update({
            "title": title or link.get("title"),
            "content_text": text,
            "is_pdf": kind == "pdf",
            "word_count": wc,
            "language_detected": detect_lang(text) if text else None,
            "has_useful_content": wc >= 100,
        })
        rec.setdefault("parse_status", "ok" if wc else "empty")
    except Exception as e:
        rec.update({"parse_status": "error", "error": f"{type(e).__name__}: {str(e)[:200]}",
                    "content_text": "", "word_count": 0, "has_useful_content": False})
    return rec


# ---------------------------------------------------------------- main
def main():
    links, server_parsed = [], []
    for b in BATCHES:
        d = export_batch(b)["data"]
        links.extend(d.get("link_collection") or [])
        server_parsed.extend(d.get("parsed_results") or [])
    print(f"Ссылок: {len(links)}, уже распарсено сервером: {len(server_parsed)}")

    done_server = {p.get("link_id") for p in server_parsed}

    progress_path = os.path.join(OUT_DIR, "local_parsed.jsonl")
    done_local = set()
    if os.path.exists(progress_path):
        with open(progress_path, encoding="utf-8") as f:
            for line in f:
                try:
                    done_local.add(json.loads(line)["link_id"])
                except Exception:
                    pass

    todo = [l for l in links if l.get("link_id") not in done_server and l.get("link_id") not in done_local]
    print(f"Осталось распарсить локально: {len(todo)} (уже сделано локально раньше: {len(done_local)})")

    lock = threading.Lock()
    t0, n = time.time(), 0
    with open(progress_path, "a", encoding="utf-8") as out, cf.ThreadPoolExecutor(WORKERS) as ex:
        futures = [ex.submit(parse_one, l) for l in todo]
        try:
            for fut in cf.as_completed(futures, timeout=None):
                try:
                    rec = fut.result()
                except Exception:
                    continue
                with lock:
                    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    out.flush()
                    n += 1
                    if n % 100 == 0 or n == len(todo):
                        rate = n / max(time.time() - t0, 1)
                        left = (len(todo) - n) / max(rate, 0.01) / 60
                        print(f"  {n}/{len(todo)}  ~{rate*60:.0f} стр/мин, осталось ~{left:.0f} мин")
        except KeyboardInterrupt:
            print("\nОстановлено. Запусти скрипт снова — продолжит с этого места.")
            ex.shutdown(wait=False, cancel_futures=True)
            return

    # ------------------------------------------------ сборка итогового файла
    local = []
    with open(progress_path, encoding="utf-8") as f:
        for line in f:
            try:
                local.append(json.loads(line))
            except Exception:
                pass
    by_id = {l.get("link_id"): l for l in links}
    for p in server_parsed:
        p["parser"] = "constructor"
        l = by_id.get(p.get("link_id"), {})
        p.setdefault("url", l.get("url"))
        p.setdefault("query_text", l.get("query_text"))
        p.setdefault("snippet", l.get("snippet"))
        p["doc_type"] = "pdf" if p.get("is_pdf") else "html"
        p["parse_status"] = "ok" if (p.get("word_count") or 0) > 0 else "empty"
    final = {
        "batch_ids": BATCHES,
        "exported_at": datetime.now().isoformat(),
        "note": "link_collection — все ссылки; parsed_results — серверный (constructor) + локальный парсинг",
        "data": {"link_collection": links, "parsed_results": server_parsed + local},
    }
    jpath = os.path.join(HERE, "kz_ai_v2_final.json")
    with open(jpath, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=1)

    cpath = os.path.join(HERE, "kz_ai_v2_final.csv")
    cols = ["parser", "domain_filter", "url", "final_url", "title", "doc_type", "parse_status",
            "word_count", "language_detected", "has_useful_content", "query_text", "snippet", "content_text"]
    with open(cpath, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in server_parsed + local:
            row = dict(r)
            row["content_text"] = (row.get("content_text") or "")[:30000]
            w.writerow(row)

    ok = sum(1 for r in local if r.get("word_count", 0) > 0)
    print("\nГОТОВО")
    print(f"  ссылок всего: {len(links)}")
    print(f"  распарсено сервером: {len(server_parsed)}, локально с текстом: {ok} из {len(local)}")
    print(f"  {jpath}\n  {cpath}")


if __name__ == "__main__":
    main()
