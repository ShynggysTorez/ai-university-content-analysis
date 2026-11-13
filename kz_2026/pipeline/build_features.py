#!/usr/bin/env python3
"""Строит компактную таблицу признаков по корпусу (без полных текстов) -> features.parquet"""
import glob, hashlib, json, os, re, sys
from urllib.parse import urlparse
import pandas as pd
from lingua import Language, LanguageDetectorBuilder

BASE = sys.argv[1] if len(sys.argv) > 1 else "."
D = os.path.join(BASE, "data_kz_v2")

LANGS = [Language.KAZAKH, Language.RUSSIAN, Language.ENGLISH, Language.UKRAINIAN,
         Language.TURKISH, Language.GERMAN, Language.CHINESE, Language.UZBEK]
det = LanguageDetectorBuilder.from_languages(*LANGS).with_low_accuracy_mode().build()
ISO = {Language.KAZAKH: "kk", Language.RUSSIAN: "ru", Language.ENGLISH: "en", Language.UKRAINIAN: "uk",
       Language.TURKISH: "tr", Language.GERMAN: "de", Language.CHINESE: "zh", Language.UZBEK: "uz"}
KK_CH = re.compile(r"[әғқңөұүһі]", re.I)


def lang_of(text):
    t = text[:3000]
    letters = re.findall(r"[^\W\d_]", t)
    if len(letters) < 30:
        return None, None
    cyr = sum(1 for c in letters if "Ѐ" <= c <= "ӿ")
    kk = len(KK_CH.findall(t))
    l = det.detect_language_of(t)
    lingua = ISO.get(l) if l else None
    # итоговое правило: казахские буквы — надёжный маркер; lingua — для остального
    if cyr / len(letters) > 0.5:
        final = "kk" if kk / max(cyr, 1) > 0.015 else ("kk" if lingua == "kk" else "ru")
    else:
        final = lingua if lingua in ("en", "tr", "de", "zh", "uz") else ("en" if lingua else None)
    # смешанные тексты
    lat = len(letters) - cyr
    mixed = 0.2 < cyr / len(letters) < 0.8
    return final, ("mixed" if mixed else lingua)


YEAR_URL = re.compile(r"(?<!\d)(20(1[5-9]|2[0-6]))(?!\d)")
DATE_TXT = re.compile(r"(?<!\d)(\d{1,2})[./](\d{1,2})[./](20(1[5-9]|2[0-6]))(?!\d)")
DATE_ISO = re.compile(r"(?<!\d)(20(1[5-9]|2[0-6]))-(\d{2})-(\d{2})(?!\d)")
MONTHS = r"(январ|феврал|март|апрел|ма[йя]|июн|июл|август|сентябр|октябр|ноябр|декабр|қаңтар|ақпан|наурыз|сәуір|мамыр|маусым|шілде|тамыз|қыркүйек|қазан|қараша|желтоқсан|january|february|march|april|may|june|july|august|september|october|november|december)"
DATE_WORD = re.compile(r"(?<!\d)\d{1,2}\s+" + MONTHS + r"\w*\s+(20(1[5-9]|2[0-6]))", re.I)
DATE_WORD2 = re.compile(MONTHS + r"\w*\s+\d{1,2},?\s+(20(1[5-9]|2[0-6]))", re.I)
COPY = re.compile(r"(©|copyright|все права|барлық құқықтар)", re.I)


def year_of(url, title, text):
    # 1) год в пути URL (папки загрузок, новости /2024/05/)
    path = urlparse(url).path
    m = re.search(r"/(20(1[5-9]|2[0-6]))/(0[1-9]|1[0-2])/", path) or re.search(r"/(20(1[5-9]|2[0-6]))/", path)
    if m:
        return int(m.group(1)), "url"
    # 2) первая полная дата в начале текста (до 1500 символов), не в строке копирайта
    head = text[:1500]
    cands = []
    for rx, g in ((DATE_TXT, 3), (DATE_ISO, 1), (DATE_WORD, 2), (DATE_WORD2, 2)):
        for mm in rx.finditer(head):
            line_start = head.rfind("\n", 0, mm.start())
            line = head[line_start + 1: mm.end() + 30]
            if COPY.search(line):
                continue
            cands.append((mm.start(), int(mm.group(g))))
    if cands:
        return sorted(cands)[0][1], "text_date"
    # 3) год в названии
    m = YEAR_URL.search(title or "")
    if m:
        return int(m.group(1)), "title"
    return None, None


TOPICS = {
    "ai_general": r"искусственн\w*\s+интеллект\w*|жасанды\s+интеллект\w*|artificial\s+intelligence|(?<![A-Za-z])AI(?![A-Za-z])|(?<![А-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі])(ИИ|ЖИ)(?![А-Яа-яЁё])",
    "genai_chatgpt": r"chat\s?gpt|(?<![A-Za-z])GPT|генеративн\w*|генеративті|generative\s+ai|gen\s?ai|gemini|copilot|deepseek|midjourney|claude\b",
    "llm_nlp": r"(?<![A-Za-z])LLM|language\s+model|языков\w+\s+модел\w*|тілдік\s+модел\w*|natural\s+language\s+processing|обработк\w+\s+естественн\w+\s+язык\w*|NLP",
    "ml_dl": r"machine\s+learning|deep\s+learning|машинн\w+\s+обучени\w*|глубок\w+\s+обучени\w*|машиналық\s+оқыту|терең\s+оқыту|нейросет\w*|нейронн\w+\s+сет\w*|нейрожелі\w*|нейрондық|neural\s+network|computer\s+vision|компьютерн\w+\s+зрени\w*",
    "ai_education": r"ai\s+in\s+education|ai\s+literacy|ИИ\s+в\s+образовани\w*|искусственн\w+\s+интеллект\w*\s+в\s+образовани\w*|білім\s+беру\w*|обучени\w+\s+студент\w*|преподавани\w*|teaching|learning\s+outcomes|оқыту\s+процес\w*|учебн\w+\s+процесс\w*",
    "academic_integrity": r"академическ\w+\s+честност\w*|академиялық\s+адалдық|academic\s+integrity|плагиат\w*|plagiarism|антиплагиат|ai\s+detect\w*|детектор\w*\s+ИИ",
    "ethics_risks": r"этик\w+|ethic\w*|этика\w*|responsible\s+ai|ответственн\w+\s+ИИ|bias|предвзят\w+|дезинформ\w+|deepfake|дипфейк\w*|риск\w*\s+ИИ",
    "policy_regulation": r"положени\w+\s+об?\s+(использовани\w+\s+)?(искусственн|ИИ)|политик\w+\s+(использовани\w+\s+)?(искусственн|ИИ)|ai\s+policy|guidelines?\s+(on|for)\s+(the\s+use\s+of\s+)?(ai|generative)|регламент\w*|ереже\w*|саясат\w*|закон\w*\s+об?\s+искусственн\w+|правил\w+\s+использовани\w+\s+(ИИ|искусственн)",
    "national_initiatives": r"ai[\s-]?sana|alem\.?ai|alemai|цифров\w+\s+казахстан|digital\s+kazakhstan|концепци\w+\s+развития\s+искусственн\w+|стратеги\w+\s+развития\s+искусственн\w+|министерств\w+\s+науки|ҒЖБМ|МНВО",
    "research": r"исследовани\w*|research|зерттеу\w*|статья|article|journal|журнал\w*|doi\.org|scopus|web\s+of\s+science|диссертац\w*|thesis",
    "medicine": r"медицин\w*|медицина|клиник\w*|diagnos\w*|диагност\w*|health\w*|здравоохранен\w*|денсаулық",
    "agriculture_industry": r"сельск\w+\s+хозяйств\w*|агро\w*|agricultur\w*|ауыл\s+шаруашылығы|промышлен\w*|industry|өнеркәсіп|нефт\w*|энергет\w*",
    "labs_centers": r"лаборатори\w+\s+(искусственн|ИИ|AI)|центр\w*\s+(искусственн|ИИ)|ai\s+(lab|center|centre)|жасанды\s+интеллект\s+(зертхана|орталығ)\w*",
    "jobs_labour": r"рын\w+\s+труд\w*|labor\s+market|labour\s+market|еңбек\s+нарығ\w*|професси\w+\s+будущ\w*|future\s+of\s+work|automation|автоматизац\w*",
}
TOPIC_RX = {k: re.compile(v, re.I if k not in ("ai_general",) else re.I) for k, v in TOPICS.items()}
# ai_general: ИИ/ЖИ/AI должны быть регистрозависимы
AI_STRICT = re.compile(r"искусственн\w*\s+интеллект\w*|жасанды\s+интеллект\w*|artificial\s+intelligence", re.I)
AI_ABBR = re.compile(r"(?<![A-Za-z])AI(?![A-Za-z])|(?<![А-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі])(ИИ|ЖИ)(?![А-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі])")


def classify(url, title, text, doc_type):
    u = (url or "").lower()
    host = urlparse(u).netloc
    t = (title or "").lower()
    head = (text or "")[:2500].lower()
    s = u + " " + t
    if re.search(r"(положени|приказ|бұйрық|ереже|регламент|политика|policy|guideline|codex|кодекс|правила|қағида|устав|стратеги|strategy|концепци|отчет|отчёт|есеп|annual.report|plan.развития|даму.бағдарлама|программа.развития)", s) and not re.search(r"(/article/|journal|vestnik|bulletin|habar|хабаршы|вестник)", s):
        return "Нормативные и стратегические документы"
    if re.search(r"(journal|vestnik|bulletin|habar|хабаршы|вестник|/article/|/ojs/|index\.php/[a-z]+/article|repository|repo\.|dspace|elib|bitstream|handle/|/jour/|proceedings|conference|конференц|материалы|thesis|диссерт|автореферат|monograph|монограф|сборник|scopus|issue|выпуск|том\s?\d|vol\.)", s) or re.search(r"(аннотация|abstract|ключевые слова|keywords|түйін сөздер|doi\.org|список литературы|references|әдебиеттер тізімі)", head):
        return "Научные публикации и журналы"
    if re.search(r"(syllabus|силлабус|curriculum|образовательн\w*.программ|білім.беру.бағдарлама|educational.program|course|курс|дисциплин|пән|модул|магистратур|бакалавриат|doctoral|phd|admission|приём|прием|талапкер|абитуриент|специальност|мамандық|study|program|programme|оп\s|eop|каталог.элективн|catalog)", s):
        return "Образовательные программы и курсы"
    if re.search(r"(news|novost|новост|жаңалық|press|event|событи|мероприят|іс-шара|announce|объявлен|хабарландыру|blog|блог|media|smi|сми|interview|интервью|/post/|article-|statya)", s) or re.search(r"/20\d\d/\d\d/", u):
        return "Новости, события и медиа"
    if re.search(r"(staff|faculty|teacher|преподават|оқытушы|сотрудник|профессор|professor|персонал|person|people|cv|резюме|кадр|vacanc|ваканси)", s):
        return "Персоналии и кадры"
    if re.search(r"(лаборатор|laborator|lab\b|center|centre|центр|орталық|институт|institute|кафедр|department|faculty-of|факультет|project|проект|жоба|grant|грант)", s):
        return "Подразделения, центры и проекты"
    return "Прочее"


def norm_url(u):
    return re.sub(r"[?#].*$", "", (u or "").lower().replace("http://", "https://").replace("://www.", "://")).rstrip("/")


rows = []


def handle(r, parser):
    text = r.get("content_text") or ""
    title = r.get("title") or r.get("search_title") or ""
    url = r.get("final_url") or r.get("url") or ""
    wc = len(text.split()) if text else 0
    lang, lingua = lang_of(text) if wc >= 20 else (None, None)
    yr, ysrc = year_of(url, title, text)
    full = title + "\n" + text
    rec = {
        "link_id": str(r.get("link_id")), "domain": r.get("domain_filter"), "url": url, "parser": parser,
        "doc_type": r.get("doc_type") or ("pdf" if str(r.get("is_pdf")) in ("True", "true", "1") else "html"),
        "title": title[:300], "word_count": wc, "lang": lang, "lang_lingua": lingua,
        "year": yr, "year_src": ysrc, "query": r.get("query_text"),
        "ctype": classify(url, title, text, r.get("doc_type")),
        "ai_strict": len(AI_STRICT.findall(full)), "ai_abbr": len(AI_ABBR.findall(full)),
        "text_hash": hashlib.md5(re.sub(r"\s+", " ", text[:20000]).strip().lower().encode("utf-8", "replace")).hexdigest() if wc else None,
        "url_norm": norm_url(url), "local_file": r.get("local_file"),
        "excerpt": re.sub(r"\s+", " ", text[:400]),
    }
    for k, rx in TOPIC_RX.items():
        if k == "ai_general":
            continue
        rec["t_" + k] = len(rx.findall(full))
    rows.append(rec)


# серверные (Constructor) результаты + ссылки (для query/url)
links = {}
for f in glob.glob(os.path.join(D, "export_*.json")):
    d = json.load(open(f, encoding="utf-8"))["data"]
    for l in d.get("link_collection") or []:
        links[str(l["link_id"])] = l
    for p in d.get("parsed_results") or []:
        l = links.get(str(p.get("link_id")), {})
        p.setdefault("url", l.get("url")); p["query_text"] = l.get("query_text"); p["search_title"] = l.get("title")
        handle(p, "constructor")
n_srv = len(rows)
files_idx = {}
fi = os.path.join(D, "files_index.jsonl")
if os.path.exists(fi):
    for line in open(fi, encoding="utf-8"):
        try:
            x = json.loads(line); files_idx[str(x["link_id"])] = x.get("local_file")
        except Exception:
            pass
with open(os.path.join(D, "local_parsed.jsonl"), encoding="utf-8") as fh:
    for i, line in enumerate(fh):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if not r.get("local_file"):
            r["local_file"] = files_idx.get(str(r.get("link_id")))
        handle(r, "local")
        if i % 2000 == 0:
            print("local", i, flush=True)

df = pd.DataFrame(rows)
# ссылки без какой-либо записи парсинга
seen = set(df.link_id)
miss = [l for k, l in links.items() if k not in seen]
print("server", n_srv, "local", len(df) - n_srv, "links total", len(links), "links without parse rec", len(miss))
df.to_parquet(os.path.join(BASE, "analysis", "features.parquet"), index=False)
pd.DataFrame([{"link_id": str(l["link_id"]), "domain": l["domain_filter"], "url": l["url"], "query": l["query_text"],
               "title": l.get("title"), "snippet": l.get("snippet")} for l in links.values()]).to_parquet(
    os.path.join(BASE, "analysis", "links.parquet"), index=False)
print("saved", len(df))
