import pandas as pd, re, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'data')
OUT = os.path.join(HERE, '..', 'outputs')
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
ILL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
def cl(v):
    if isinstance(v,str):
        v=ILL.sub('',v)[:32000]
        return (' '+v) if v.startswith(('=','+','-','@')) else v
    return v
t=pd.read_parquet(os.path.join(DATA,'corpus.parquet'))
TOPN={'t_genai_chatgpt':'Генеративный ИИ/ChatGPT','t_llm_nlp':'LLM и обработка языка','t_ml_dl':'Машинное обучение/нейросети','t_ai_education':'Образование и преподавание','t_academic_integrity':'Академическая честность','t_ethics_risks':'Этика и риски','t_policy_regulation':'Политика и регулирование','t_national_initiatives':'Нац. инициативы (AI-Sana и др.)','t_research':'Научные исследования','t_medicine':'Медицина и здоровье','t_agriculture_industry':'Агро, промышленность, энергетика','t_labs_centers':'AI-лаборатории и центры','t_jobs_labour':'Рынок труда, автоматизация'}
LANG={'kk':'казахский','ru':'русский','en':'английский','de':'немецкий','tr':'турецкий'}
db=pd.DataFrame({
 'ID ссылки':t.link_id,'Домен':t.domain,'Вуз':t.university,'Тип вуза':t.type_grp,'Регион':t.region,
 'Тип контента':t.ctype2,'Уровень ИИ':t.ai_tier,'Язык':t.lang.map(LANG),'Год':t.year,'Источник года':t.year_src.map({'url':'URL','text_date':'дата в тексте','title':'заголовок'}),
 'Формат':t.doc_type.str.upper(),'Слов':t.word_count,'AI-терминов (с поправкой)':t.ai_core_terms,'Заголовок':t.title,'URL':t.url,'Поисковый запрос':t['query'],
 'Начало текста':t.excerpt,'Локальный файл':t.local_file})
for k,v in TOPN.items(): db[v]=(t[k]>0).astype(int)
db=db.sort_values(['Вуз','Уровень ИИ','Год'],na_position='last')
um=pd.read_csv(os.path.join(DATA,'uni_map.csv'))
wb=Workbook()
F=Font(name='Arial',size=10); B=Font(name='Arial',size=10,bold=True); H=Font(name='Arial',size=10,bold=True,color='FFFFFF')
HF=PatternFill('solid',fgColor='1F4E78'); T=Font(name='Arial',size=14,bold=True); I=Font(name='Arial',size=9,italic=True,color='595959')
def header(ws,row,cols,widths=None):
    for j,c in enumerate(cols,1):
        x=ws.cell(row,j,c); x.font=H; x.fill=HF; x.alignment=Alignment(wrap_text=True,vertical='center')
    if widths:
        for j,w in enumerate(widths,1): ws.column_dimensions[get_column_letter(j)].width=w
# ---- База записей
ws=wb.active; ws.title='База записей'
cols=list(db.columns); header(ws,1,cols)
for i,row in enumerate(db.itertuples(index=False),2):
    for j,v in enumerate(row,1):
        if pd.isna(v) if not isinstance(v,str) else False: v=None
        if j==9 and v is not None: v=int(v)
        c=ws.cell(i,j,cl(v)); c.font=F
N=len(db)+1
widths=[10,20,34,24,18,30,22,11,7,13,8,8,10,50,50,40,60,40]+[12]*len(TOPN)
for j,w in enumerate(widths,1): ws.column_dimensions[get_column_letter(j)].width=w
ws.freeze_panes='C2'; ws.auto_filter.ref=f"A1:{get_column_letter(len(cols))}{N}"
col={c:get_column_letter(j) for j,c in enumerate(cols,1)}
R=lambda c: f"'База записей'!${col[c]}$2:${col[c]}${N}"
A='A. Профильный (об ИИ)'
# ---- Сводка
s=wb.create_sheet('Сводка',0)
s['A1']='ИИ на сайтах вузов Казахстана — сводка корпуса'; s['A1'].font=T
s['A2']='Сбор: ноябрь 2026 (Serper/Google + Constructor, локальный парсинг). Все показатели считаются формулами по листу «База записей».'; s['A2'].font=I
rows=[('Записей в корпусе (после дедупликации)',f'=COUNTA({R("ID ссылки")})','0'),
('Вузов в корпусе',f'=SUMPRODUCT(({R("Домен")}<>"")/COUNTIF({R("Домен")},{R("Домен")}&""))','0'),
('A — профильный AI-контент',f'=COUNTIF({R("Уровень ИИ")},"{A}")','#,##0'),
('Доля профильного AI-контента','=B6/B4','0.0%'),
('B — упоминание ИИ',f'=COUNTIF({R("Уровень ИИ")},"B. Упоминание ИИ")','#,##0'),
('C — без упоминаний ИИ',f'=COUNTIF({R("Уровень ИИ")},"C. Без упоминаний ИИ")','#,##0'),
('Документы PDF/DOCX с текстом',f'=COUNTIF({R("Формат")},"PDF")+COUNTIF({R("Формат")},"DOCX")','#,##0'),
('AI-профильные записи с определённым годом',f'=COUNTIFS({R("Уровень ИИ")},"{A}",{R("Год")},">0")','#,##0'),
('Справочно: собрано ссылок (до очистки)',14675,'#,##0'),
('Справочно: ссылок с извлечённым текстом',12741,'#,##0'),
('Справочно: файлов без текста сохранено локально (data_kz_v2/files)',461,'#,##0')]
s['A3']='Показатель'; s['B3']='Значение'
for c in ('A3','B3'): s[c].font=H; s[c].fill=HF
for i,(a,b,fmt) in enumerate(rows,4):
    s.cell(i,1,a).font=F; x=s.cell(i,2,b); x.font=F; x.number_format=fmt
    if isinstance(b,int): x.font=Font(name='Arial',size=10,color='0000FF')
s.cell(15,1,'Синие числа — значения из журнала сбора (вне базы).').font=I
s.column_dimensions['A'].width=62; s.column_dimensions['B'].width=14
# ---- generic crosstab helper
def ctab(name,title,rowlabels,rowcol,colvals,colcol,note=None,share_of_total=True):
    w=wb.create_sheet(name); w['A1']=title; w['A1'].font=T
    if note: w['A2']=note; w['A2'].font=I
    hdr=['']+colvals+['Всего']; header(w,3,hdr,[42]+[14]*(len(colvals)+1))
    for i,rl in enumerate(rowlabels,4):
        w.cell(i,1,rl).font=F
        for j,cv in enumerate(colvals,2):
            f=f'=COUNTIFS({R(rowcol)},$A{i},{R(colcol)},"{cv}")' if colcol else ''
            x=w.cell(i,j,f); x.font=F; x.number_format='#,##0'
        x=w.cell(i,len(colvals)+2,f'=SUM(B{i}:{get_column_letter(len(colvals)+1)}{i})'); x.font=B; x.number_format='#,##0'
    return w
CT=sorted(t.ctype2.unique().tolist())
w=ctab('Типы контента','Типы контента × уровень AI-релевантности',CT,'Тип контента',[A,'B. Упоминание ИИ','C. Без упоминаний ИИ'],'Уровень ИИ')
n=len(CT); w.cell(3,6,'Доля A').font=H; w.cell(3,6).fill=HF
for i in range(4,4+n):
    x=w.cell(i,6,f'=IF(E{i}=0,0,B{i}/E{i})'); x.number_format='0%'; x.font=F
LG=['казахский','русский','английский']
w=ctab('Языки','Языки AI-профильных записей по типу контента и типу вуза',CT,'Тип контента',LG,'Язык','Только уровень A. Немецкий/турецкий (<1%) не показаны.')
for i,rl in enumerate(CT,4):
    for j,cv in enumerate(LG,2):
        w.cell(i,j,f'=COUNTIFS({R("Тип контента")},$A{i},{R("Язык")},"{cv}",{R("Уровень ИИ")},"{A}")')
TG=sorted(t.type_grp.dropna().unique().tolist()); r0=4+len(CT)+2
w.cell(r0-1,1,'По типу вуза').font=B
for i,rl in enumerate(TG,r0):
    w.cell(i,1,rl).font=F
    for j,cv in enumerate(LG,2):
        x=w.cell(i,j,f'=COUNTIFS({R("Тип вуза")},$A{i},{R("Язык")},"{cv}",{R("Уровень ИИ")},"{A}")'); x.font=F
    w.cell(i,5,f'=SUM(B{i}:D{i})').font=B
# Динамика
w=wb.create_sheet('Динамика'); w['A1']='Динамика по годам (датированные записи)'; w['A1'].font=T
w['A2']='2026 — по 13 ноября. Абсолютные числа смещены к недавним годам; надёжнее доля A среди датированных.'; w['A2'].font=I
hdr=['Год','Датированных записей','Из них A (профильные)','Доля A','Вузов с A-записями','Генеративный ИИ среди A','Академическая честность среди A']
header(w,3,hdr,[8,20,20,10,18,22,24])
yrs=list(range(2015,2027))
for i,y in enumerate(yrs,4):
    w.cell(i,1,str(y)).font=F
    w.cell(i,2,f'=COUNTIF({R("Год")},{y})')
    w.cell(i,3,f'=COUNTIFS({R("Год")},{y},{R("Уровень ИИ")},"{A}")')
    w.cell(i,4,f'=IF(B{i}=0,0,C{i}/B{i})').number_format='0%'
    w.cell(i,5,int(t[(t.year==y)&t.is_core].domain.nunique())).font=Font(name='Arial',size=10,color='0000FF')
    w.cell(i,6,f'=IF(C{i}=0,0,COUNTIFS({R("Год")},{y},{R("Уровень ИИ")},"{A}",{R("Генеративный ИИ/ChatGPT")},1)/C{i})').number_format='0%'
    w.cell(i,7,f'=IF(C{i}=0,0,COUNTIFS({R("Год")},{y},{R("Уровень ИИ")},"{A}",{R("Академическая честность")},1)/C{i})').number_format='0%'
w.cell(4+len(yrs)+1,1,'Столбец «Вузов» (синий) посчитан в Python — число уникальных доменов за год.').font=I
# Темы
w=wb.create_sheet('Темы'); w['A1']='Тематические маркеры среди AI-профильных записей'; w['A1'].font=T
w['A2']='Одна запись может нести несколько маркеров. Маркеры словарные (ru/kk/en).'; w['A2'].font=I
header(w,3,['Тема','Записей A с темой','Доля от всех A','Вузов с темой'],[36,18,14,14])
for i,(k,v) in enumerate(TOPN.items(),4):
    w.cell(i,1,v).font=F
    w.cell(i,2,f'=COUNTIFS({R(v)},1,{R("Уровень ИИ")},"{A}")')
    w.cell(i,3,f"=B{i}/Сводка!$B$6").number_format='0.0%'
    w.cell(i,4,int(t[t.is_core&(t[k]>0)].domain.nunique())).font=Font(name='Arial',size=10,color='0000FF')
# Вузы
w=wb.create_sheet('Вузы'); w['A1']='Вузы: AI-контент по каждому вузу'; w['A1'].font=T
w['A2']='Сортировка по числу профильных записей. Тип и город — справочник автора.'; w['A2'].font=I
hdr=['Домен','Вуз','Город','Тип вуза','Регион','Записей','A — профильные','Доля A','Каз (A)','Рус (A)','Англ (A)','Норм. документы с ИИ (A/B)','Есть AI-Sana','Есть ChatGPT Edu']
header(w,3,hdr,[22,44,18,26,18,10,14,9,9,9,9,16,12,14])
TG2={'national':0}
from collections import Counter
cnt=t[t.is_core].groupby('domain').size()
um['region']=um.city.map(dict(zip(t.city,t.region)) if 'city' in t else {})
order=um.assign(c=um.domain.map(cnt).fillna(0)).sort_values('c',ascending=False)
pol=json.load(open(os.path.join(DATA,'policy.json')))
sana=set(t[t.title.fillna('').str.contains('sana',case=False)|t.excerpt.fillna('').str.contains(r'ai[\s-]?sana',case=False)|t.url.str.contains('sana',case=False)].domain)
tg=dict(zip(t.domain,t.type_grp)); rg=dict(zip(t.domain,t.region))
for i,r in enumerate(order.itertuples(),4):
    vals=[r.domain,r.university,r.city,tg.get(r.domain,''),rg.get(r.domain,'')]
    for j,v in enumerate(vals,1): w.cell(i,j,v).font=F
    w.cell(i,6,f'=COUNTIF({R("Домен")},$A{i})')
    w.cell(i,7,f'=COUNTIFS({R("Домен")},$A{i},{R("Уровень ИИ")},"{A}")')
    w.cell(i,8,f'=IF(F{i}=0,0,G{i}/F{i})').number_format='0%'
    for j,lg in zip((9,10,11),LG): w.cell(i,j,f'=COUNTIFS({R("Домен")},$A{i},{R("Уровень ИИ")},"{A}",{R("Язык")},"{lg}")')
    w.cell(i,12,f'=COUNTIFS({R("Домен")},$A{i},{R("Тип контента")},"Нормативные и стратегические документы",{R("Уровень ИИ")},"<>C. Без упоминаний ИИ")')
    w.cell(i,13,'да' if r.domain in sana else '').font=F
    w.cell(i,14,'да' if r.domain in pol['edu_domains'] else '').font=F
w.freeze_panes='C4'; w.auto_filter.ref=f"A3:N{3+len(order)}"
# Политики
w=wb.create_sheet('Политики ИИ'); w['A1']='Нормативный слой: политики использования ИИ'; w['A1'].font=T
header(w,3,['Уровень','Вуз','Домен','Документ / основание','URL'],[30,42,20,60,70])
inst=[('qmu.edu.kz','Политика применения искусственного интеллекта (рус/каз/англ)','https://qmu.edu.kz/ru/zhizn-v-kmu/akademicheskaya-politika/politika-primeneniya-ii/'),
('atyrau.edu.kz','Ответственное использование ИИ — раздел «Академическая честность»','https://atyrau.edu.kz/ru/AcademicIntegrity/Section/artificial-intelligence'),
('kaznai.kz','Проект положения о применении технологий ИИ (окт. 2026)','https://kaznai.kz/wp-content/uploads/2026/10/proekt-polozhenija-o-primenenii-ii.pdf'),
('auezov.edu.kz','Statement on the Use of Artificial Intelligence','https://nu.auezov.edu.kz/images/doc/AIisNUeng.pdf'),
('ku.edu.kz','Документ о применении ИИ (каз., тип требует проверки)','https://ku.edu.kz/ru/doc/get?id=2736')]
nm=dict(zip(um.domain,um.university)); r=4
for d,doc,u in inst:
    for j,v in enumerate(['Общеуниверситетская политика',nm.get(d),d,doc,u],1): w.cell(r,j,v).font=F
    r+=1
jd=['aiu.kz','almau.edu.kz','ayu.edu.kz','bolashaq.edu.kz','buketov.edu.kz','dulaty.kz','enu.kz','iitu.edu.kz','kaznaru.edu.kz','kaztbu.edu.kz','mtgu.edu.kz']
for d in jd:
    for j,v in enumerate(['Политика ген. ИИ в научном журнале',nm.get(d),d,'Страница журнала о генеративном ИИ',''],1): w.cell(r,j,v).font=F
    r+=1
for d in pol['edu_domains']:
    for j,v in enumerate(['Внедрение ChatGPT Edu',nm.get(d),d,'Семинары/обучение ChatGPT Edu',''],1): w.cell(r,j,v).font=F
    r+=1
# Методология
w=wb.create_sheet('Методология'); w['A1']='Методология и определения'; w['A1'].font=T; w.column_dimensions['A'].width=28; w.column_dimensions['B'].width=110
M=[('Выборка','129 доменов вузов (список марта 2026, сверен с univision.kz); 102 сайта дали тексты.'),
('Запросы','48 запросов (18 рус, 16 англ, 14 каз) с site:<домен>, Serper (Google), ноябрь 2026; включают поиск PDF/DOC/PPT/XLS.'),
('Парсинг','Constructor (2 235 стр.) + локально: trafilatura (HTML), pypdf (PDF), python-docx (DOCX).'),
('Дедупликация','По нормализованному URL, затем по хешу первых 20 000 символов текста.'),
('Уровень ИИ','A — ИИ в заголовке или ≥5 AI-терминов (≥2 полных терминов); B — ≥1 термин; C — нет. Поправка на шаблон сайта: вычитается 10-й процентиль числа терминов по домену (≥20 страниц).'),
('Язык','Доля кириллицы + казахские буквы (әғқңөұүһі), сверка с lingua: совпадение 93,3%.'),
('Год','Из пути URL, первой даты в начале текста (кроме строк копирайта) или заголовка; определён для 34% записей A.'),
('Тип контента','Правила по URL, заголовку и началу текста; ручная проверка 3×50 записей, финальная точность 88%.'),
('Ограничения','Видимость в поиске ≠ вся активность вуза; выдача ≈10 результатов на запрос; язык страниц следует языку запроса; справочник вузов — авторский.')]
for i,(a,b) in enumerate(M,3):
    w.cell(i,1,a).font=B; x=w.cell(i,2,b); x.font=F; x.alignment=Alignment(wrap_text=True)
for ws_ in wb.worksheets:
    for row in ws_.iter_rows():
        for c in row:
            if c.font and c.font.name!='Arial': c.font=Font(name='Arial',size=10,bold=c.font.b,italic=c.font.i,color=c.font.color)
wb.save(os.path.join(OUT,'kz_ai_universities_database.xlsx')); print('saved', N)
