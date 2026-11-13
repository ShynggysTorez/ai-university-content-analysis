import pandas as pd, numpy as np, re, json
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40); pd.set_option('display.max_colwidth', 90)
import os
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'data')
F = os.path.join(HERE, '..', 'work', 'features.parquet')  # результат pipeline/build_features.py
df = pd.read_parquet(F)
um = pd.read_csv(os.path.join(DATA, 'uni_map.csv'))
REG = {'Алматы': 'г. Алматы', 'Астана': 'г. Астана', 'Шымкент': 'г. Шымкент', 'Каскелен (Алматинская обл.)': 'Алматинская обл.',
       'Семей': 'Абайская обл.', 'Павлодар': 'Павлодарская обл.', 'Экибастуз': 'Павлодарская обл.', 'Кокшетау': 'Акмолинская обл.',
       'Актау': 'Мангистауская обл.', 'Кызылорда': 'Кызылординская обл.', 'Актобе': 'Актюбинская обл.', 'Аркалык': 'Костанайская обл.',
       'Атырау': 'Атырауская обл.', 'Петропавловск': 'СКО', 'Усть-Каменогорск': 'ВКО', 'Жезказган': 'Улытауская обл.',
       'Талдыкорган': 'Жетысуская обл.', 'Уральск': 'ЗКО', 'Караганда': 'Карагандинская обл.', 'Темиртау': 'Карагандинская обл.',
       'Костанай': 'Костанайская обл.', 'Рудный': 'Костанайская обл.', 'Туркестан': 'Туркестанская обл.', 'Тараз': 'Жамбылская обл.'}
um['region'] = um.city.map(REG).fillna('—')
TYPE_GRP = {'национальный исследовательский': 'национальные/исследовательские', 'национальный': 'национальные/исследовательские',
            'автономный исследовательский': 'национальные/исследовательские', 'международный': 'национальные/исследовательские',
            'региональный государственный': 'региональные государственные', 'педагогический': 'педагогические',
            'медицинский': 'медицинские', 'технический/отраслевой': 'технические/отраслевые', 'аграрный': 'технические/отраслевые',
            'отраслевой': 'технические/отраслевые', 'частный': 'частные', 'филиал зарубежного вуза': 'филиалы зарубежных вузов',
            'искусство': 'искусство и спорт', 'силовой/ведомственный': 'ведомственные (силовые, госуправление)',
            'государственная академия': 'ведомственные (силовые, госуправление)'}
um['type_grp'] = um.type.map(TYPE_GRP).fillna(um.type)
# nu.edu.kz & nuo.edu.kz: nuo — Национальный университет обороны (не NU)
df = df.merge(um, on='domain', how='left')

# ---------- корпус: только записи с текстом, дедупликация
t = df[df.word_count > 0].copy()
t = t.sort_values('word_count', ascending=False)
n_text = len(t)
t = t.drop_duplicates('url_norm')
n_after_url = len(t)
t = t.drop_duplicates('text_hash')
n_after_hash = len(t)

# ---------- уточнение типа контента
NEWS_U = r'(news|novost|новост|zhanal|жаңалық|haberler|etkinlik|duyuru|/media/|/events?/|/event-|/press|/blog|/post/|/sobytiya|/meropriyat|/announc|objavlen|habarlandyru|хабарландыру|/article/\d+$|/20\d\d/\d\d/\d\d/)'
def refine(r):
    c = r.ctype; u = (r.url or '').lower(); ti = (r.title or '').lower(); ex = (r.excerpt or '').lower()
    s = u + ' ' + ti
    isdoc = r.doc_type in ('pdf', 'docx')
    if re.search(r'(/search|[?&]start=|itemlist|/tag/|/tags/|/category/|/author/|/page/\d+|[?&]page=|/archive|sitemap)', u):
        return 'Служебные и навигационные страницы'
    if not isdoc and re.search(NEWS_U, u):
        return 'Новости, события и медиа'
    if isdoc and re.search(r'(образовательн\w*\s+программ|білім\s+беру\s+бағдарлама|educational\s+program|жэпк|ЖЭПК|силлабус|syllabus|каталог\s+элективн|рабоч\w+\s+учебн|оқу\s+жоспар|6[вb]\d{5}|7[мm]\d{5}|8[dд]\d{5})', s + ' ' + ex):
        return 'Образовательные программы и курсы'
    if re.search(r'(положени|приказ|бұйрық|ереже|регламент|policy|guideline|кодекс|codex|правила|қағида|устав|стратеги|strategy|концепци|тұжырымдама|regulation|дамытудың|мемлекеттік\s+бағдарлама|государственн\w+\s+программ|annual.report|отч[её]т|есеп|программа.развития|даму.бағдарлама|development.program|академическ\w*.политик|academic.policy|академиялық.саясат|academic.integrity|академическ\w*.честност|академиялық.адалдық)', s) and not re.search(r'(/article/|journal|vestnik|bulletin|habar|хабаршы|вестник|/jour/)', s):
        return 'Нормативные и стратегические документы'
    if re.search(r'(journal|vestnik|bulletin|habar|хабаршы|вестник|/jour/|/ojs/|/article/(view|download)|repository|repo\.|dspace|elib|bitstream|handle/|research\.nu|/publications?/|proceedings|конференц|материал\w*\s+(международн|республикан|конференц)|сборник|sbornik|thesis|диссерт|автореферат|monograph|монограф|textbook|учебн\\w*\\s+пособ|оқу\\s+құрал|elibrary|библиотек|кітапхана)', s) or re.search(r'(аннотация|abstract|ключевые слова|keywords|түйін сөздер|түйінді сөздер|на правах рукописи|қолжазба құқығында|учебно-методическ|оқу-әдістемелік|doi\.org|удк\s?\d|ұдк|ӘОЖ|әож|irsti|мрнти|ғтар)', ex) or c == 'Научные публикации и журналы':
        return 'Научные публикации и журналы'
    if re.search(r'(/personnel/|/teachers?/|/staff/|sveden|employees|/cv|resume|резюме|/person/|/people/)', u):
        return 'Персоналии и кадры'
    if c in ('Образовательные программы и курсы',) or re.search(r'(-masters|-bachelor|/masters|/bachelor|/programs?/|график\\s+учебн|schedule\\s+of\\s+educational|/mod/|moodle|lms\.|/course|syllabus|силлабус|curriculum|образовательн\w*.программ|білім.беру.бағдарлама|educational.program|бакалавриат|магистратур|докторантур|bachelor|master.s|microqualif|микроквалиф|микробілік|6[вb]\d{5}|7[мm]\d{5})', s):
        return 'Образовательные программы и курсы'
    if c == 'Новости, события и медиа' and not isdoc:
        return 'Новости, события и медиа'
    if re.search(r'(sveden|employees|сотрудник|staff|/cv|resume|резюме|teacher|оқытушы|преподавател|professor|профессор)', s):
        return 'Персоналии и кадры'
    if re.search(r'(лаборатор|laborator|\blab\b|center|centre|центр|орталық|институт|institute|кафедр|department|факультет|faculty|project|проект|жоба|ai-sana|ai sana)', s):
        return 'Подразделения, центры и проекты'
    if isdoc:
        return 'Прочие документы (PDF/DOCX)'
    if r.year_src in ('text_date', 'url') or re.search(r'(прошл[аи]|состоял|провел|өтті|ұйымдастырылды|held|took place|организован)', ex):
        return 'Новости, события и медиа'
    return 'Прочее (общие страницы сайта)'
t['ctype2'] = t.apply(refine, axis=1)

# ---------- AI-релевантность
t['ai_core_terms'] = t.ai_strict + t.ai_abbr + t.t_genai_chatgpt + t.t_llm_nlp + t.t_ml_dl
g = t.groupby('domain').ai_core_terms
floor = g.quantile(0.10).where(g.size() >= 20, 0).round()
t['ai_floor'] = t.domain.map(floor).fillna(0)
t['ai_core_raw'] = t.ai_core_terms
t['ai_core_terms'] = (t.ai_core_terms - t.ai_floor).clip(lower=0)
t['ai_density'] = t.ai_core_terms / t.word_count.clip(lower=1) * 1000
TT = t.title.fillna('')
title_ai = TT.str.contains(r'искусственн\w*\s+интеллект|жасанды\s+интеллект|artificial\s+intelligence|ChatGPT|нейросет|нейрожел|нейрон\w*\s+(сет|желі)|machine\s+learning|deep\s+learning|машинн\w+\s+обучен|машиналық\s+оқыту|генератив|generative|language\s+model', case=False, regex=True) | TT.str.contains(r'(?<![A-Za-z])(AI|GPT|LLM)(?![A-Za-z])|(?<![А-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі])(ИИ|ЖИ)(?![А-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі])', case=True, regex=True)
t['ai_title'] = title_ai
def tier(r):
    full_terms = r.ai_strict + r.t_genai_chatgpt + r.t_llm_nlp + r.t_ml_dl
    if r.ai_title or (r.ai_core_terms >= 5 and full_terms >= 2) or (r.ai_core_terms >= 3 and r.ai_density >= 2 and full_terms >= 1):
        return 'A. Профильный (об ИИ)'
    if r.ai_core_terms >= 1:
        return 'B. Упоминание ИИ'
    return 'C. Без упоминаний ИИ'
t['ai_tier'] = t.apply(tier, axis=1)
t['is_core'] = t.ai_tier.str.startswith('A')

TOP = ['t_genai_chatgpt', 't_llm_nlp', 't_ml_dl', 't_ai_education', 't_academic_integrity', 't_ethics_risks',
       't_policy_regulation', 't_national_initiatives', 't_research', 't_medicine', 't_agriculture_industry', 't_labs_centers', 't_jobs_labour']
TOPNAME = {'t_genai_chatgpt': 'Генеративный ИИ / ChatGPT', 't_llm_nlp': 'LLM и обработка языка', 't_ml_dl': 'Машинное обучение и нейросети',
           't_ai_education': 'ИИ в обучении и преподавании', 't_academic_integrity': 'Академическая честность / плагиат',
           't_ethics_risks': 'Этика и риски ИИ', 't_policy_regulation': 'Политика и регулирование ИИ',
           't_national_initiatives': 'Нац. инициативы (AI-Sana и др.)', 't_research': 'Научные исследования',
           't_medicine': 'Медицина и здоровье', 't_agriculture_industry': 'Агро, промышленность, энергетика',
           't_labs_centers': 'AI-лаборатории и центры', 't_jobs_labour': 'Рынок труда и автоматизация'}
t.to_parquet(os.path.join(DATA, 'corpus.parquet'), index=False)
json.dump({'n_links': len(df), 'n_text': n_text, 'n_after_url': n_after_url, 'n_dedup': n_after_hash}, open(os.path.join(DATA, 'counts.json'), 'w'))
print({'n_links': len(df), 'n_text': n_text, 'n_after_url': n_after_url, 'n_dedup': n_after_hash})
print(t.ai_tier.value_counts())
print(t.ctype2.value_counts())
print(pd.crosstab(t.ctype2, t.ai_tier, margins=True))
