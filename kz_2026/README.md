# Казахстан 2026: ИИ на сайтах университетов

Сбор данных — ноябрь 2026 года. Охват: 129 вузов Казахстана, 48 поисковых запросов на казахском, русском и английском языках.

## Итоговые цифры

| Этап | Записей | Вузов |
|---|---|---|
| Ссылок собрано (Serper) | 14 675 | 112 |
| Удалось извлечь текст | 12 741 | 102 |
| После дедупликации | 11 111 | 102 |
| Профильный ИИ-контент (уровень A) | 6 792 (61,1%) | 99 |

Основные выводы:
- Вузов, у которых есть датированные ИИ-материалы: 18 в 2022 году, 81 в 2026-м.
- Общевузовская политика по ИИ опубликована у 5 вузов.
- Политика по генеративному ИИ есть в журналах 11 вузов.
- ChatGPT Edu внедрён в 22 вузах, программа AI-Sana — в 57.

Сводные таблицы и полная база — в `outputs/kz_ai_universities_database.xlsx`.

## Структура

```
kz_2026/
├── pipeline/
│   ├── parse_kz_local.py    # локальный парсер: HTML (trafilatura), PDF (pypdf), DOCX (python-docx),
│   │                        # теги ключевых слов ИИ, сохранение нечитаемых файлов
│   └── build_features.py    # признаки: язык (lingua + казахские буквы), год, ИИ-термины, темы
├── analysis/
│   ├── analyze_corpus.py    # дедупликация, уровни A/B/C, тип контента, вузы → data/corpus.parquet
│   └── build_xlsx.py        # Excel-база со сводкой → outputs/
├── data/
│   ├── domains_kz_universities_v2_all.csv   # 129 доменов вузов
│   ├── kz_unis_v2_part1-4.csv               # те же домены, разбитые на 4 пакета для сервера
│   ├── queries_new_v2_25.txt                # 25 новых запросов (плюс 24 из исходного keys_genai_kz_en__ru_ ai3.txt)
│   ├── uni_map.csv                          # справочник вузов: тип, город
│   ├── uni_stats.csv                        # статистика по вузам
│   ├── policy.json                          # найденные политики ИИ
│   ├── counts.json                          # объёмы данных на каждом этапе
│   └── corpus.parquet                       # итоговый корпус, 11 111 записей
└── outputs/
    └── kz_ai_universities_database.xlsx      # база записей и сводки (9 листов)
```

## Что не входит в репозиторий

Файлы слишком большие для GitHub (лимит 100 МБ на файл), поэтому хранятся локально:
- `data_kz_v2/local_parsed.jsonl` — 530 МБ
- `data_kz_v2/files/` — 461 документ, 3 ГБ
- `kz_ai_v2_final.json` — 556 МБ
- `kz_ai_v2_final.csv` — 157 МБ
- `analysis/features.parquet`

Их можно выложить архивом в GitHub Releases или на Zenodo.

## Как воспроизвести

```bash
python -m venv .venv && .venv/bin/pip install requests trafilatura pypdf python-docx pandas pyarrow lingua-language-detector openpyxl
.venv/bin/python kz_2026/pipeline/parse_kz_local.py         # нужны export_serper_collection_*.json в data_kz_v2/
.venv/bin/python kz_2026/pipeline/build_features.py local 0 999999
mkdir -p kz_2026/work && cp analysis/features.parquet kz_2026/work/
.venv/bin/python kz_2026/analysis/analyze_corpus.py
.venv/bin/python kz_2026/analysis/build_xlsx.py
```
