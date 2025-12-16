
# -*- coding: utf-8 -*-
from pathlib import Path
import logging
import pandas as pd
from typing import Optional
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import Color
from PyPDF2 import PdfReader, PdfWriter
import re

# -------------------------------------------------------------------
# Utilidades básicas
# -------------------------------------------------------------------

# Mapa de meses (case-insensitive)
PT_MONTHS = {
    'janeiro': 'Janeiro', 'fevereiro': 'Fevereiro', 'março': 'Março', 'marco': 'Março',
    'abril': 'Abril', 'maio': 'Maio', 'junho': 'Junho', 'julho': 'Julho',
    'agosto': 'Agosto', 'setembro': 'Setembro', 'outubro': 'Outubro',
    'novembro': 'Novembro', 'dezembro': 'Dezembro'
}

def infer_mes_ano_from_safe_name(safe_name: str) -> tuple[str | None, str | None]:
    """
    Extrai (mes, ano) de nomes como:
    'Relatório Junho 2025 - ... .csv' ou 'Relatorio junho 2025 ...'
    Retorna (None, None) se não encontrar.
    """
    if not safe_name:
        return None, None

    name = safe_name.lower()
    # tenta padrão '... <mes> <ano> ...'
    m = re.search(r'\b(' + '|'.join(PT_MONTHS.keys()) + r')\b\s+(\d{4})', name)
    if m:
        mes_key = m.group(1)
        ano = m.group(2)
        mes = PT_MONTHS.get(mes_key, mes_key.capitalize())
        return mes, ano

    # fallback: tenta 'mes_ref_<mes>_<ano>' etc.
    m2 = re.search(r'(janeiro|fevereiro|mar[cç]o|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)[\W_]+(\d{4})', name)
    if m2:
        mes_key = m2.group(1).replace('ç', 'c')
        ano = m2.group(2)
        mes = PT_MONTHS.get(mes_key, mes_key.capitalize())
        return mes, ano

    return None, None

PAGE_W, PAGE_H = A4

def mmx(x_mm: float) -> float: return x_mm * mm
def mmy(y_mm: float) -> float: return y_mm * mm

def register_fonts(fonts_dir: Path):
    """Registra as fontes TTF (para acentuação correta)."""
    pdfmetrics.registerFont(TTFont('OpenSans_Cond_Bold',   str(fonts_dir / 'OpenSans_Condensed-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('OpenSans_Cond_Light',  str(fonts_dir / 'OpenSans_Condensed-Light.ttf')))
    pdfmetrics.registerFont(TTFont('OpenSans_Cond_Medium', str(fonts_dir / 'OpenSans_Condensed-Medium.ttf')))

def load_processed_csv(csv_path: Path) -> pd.DataFrame:
    """Lê o CSV tratado pelo módulo 2."""
    df = pd.read_csv(csv_path, sep=';', dtype=str)
    df.columns = [c.strip() for c in df.columns]
    return df.fillna('')

# -------------------------------------------------------------------
# Descoberta e mapeamento de perguntas
# -------------------------------------------------------------------
def detect_question_columns(df: pd.DataFrame):
    """Retorna colunas de perguntas (exclui metadados). Ajuste se necessário."""
    meta = {'name', 'sis_id', 'submitted'}
    return [c for c in df.columns if c not in meta]

def slugify_question(col: str) -> str:
    """Cria um alias curto e estável para a pergunta a partir do cabeçalho completo."""
    import re, unicodedata
    s = col.replace('\n', ' ').strip()
    s = ''.join(ch for ch in unicodedata.normalize('NFD', s) if unicodedata.category(ch) != 'Mn')
    s = re.sub(r'[^a-z0-9 ]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    base = '_'.join(s.split()[:5])
    return base[:50]

def build_question_map(df: pd.DataFrame):
    """
    Retorna: {alias: {'csv_col': <nome original do CSV>, 'display': <texto completo da pergunta>}}
    Mantém 'display' exatamente igual ao cabeçalho original (com acentuação e \n).
    """
    q_cols = detect_question_columns(df)
    question_map = {}
    for i, col in enumerate(q_cols, start=1):
        alias_tail = slugify_question(col)
        alias = f"q{i:02d}_{alias_tail}"
        question_map[alias] = {'csv_col': col, 'display': col}
    return question_map

# -------------------------------------------------------------------
# Estilos tipográficos
# -------------------------------------------------------------------
TEXT_DARK_70 = Color(0.384, 0.384, 0.384)
def get_styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle(
        name='Question',
        fontName='OpenSans_Cond_Medium',
        fontSize=8,
        leading=11,
        spaceAfter=0,
        wordWrap='LTR',
        splitLongWords=True,
        textColor=TEXT_DARK_70
    ))
    ss.add(ParagraphStyle(
        name='Answer',
        fontName='OpenSans_Cond_Light',
        fontSize=8,
        leading=11,
        spaceAfter=0,
        textColor=TEXT_DARK_70,
        wordWrap='LTR',
        splitLongWords=True
    ))
    return ss

# -------------------------------------------------------------------
# Layout do cabeçalho e grade (duas colunas) de perguntas
# -------------------------------------------------------------------
# Cabeçalho: (x_mm, y_mm, fonte, tamanho)
FIELD_MAP = {
    'name':      (33, 270, 'OpenSans_Cond_Medium', 12),
    'sis_id':    (33, 264, 'OpenSans_Cond_Medium', 11),
    'submitted': (160, 270, 'OpenSans_Cond_Medium', 11),
}

# Parâmetros da grade (ajuste milimetricamente conforme seu template)
GRID = {
    'x_left': 5,        # coluna da pergunta
    'w_left': 135,
    'gutter': 0,        # espaçamento entre colunas
    'x_right': None,    # será calculado dinamicamente
    'w_right': 65,
    'y_start': 255,     # início da primeira linha
    'row_h': 15.5,      # altura por linha
    'rows_per_page': 15,# quantidade de linhas por página
}

# --- Altura sob demanda (override por pergunta) ---
# Chave: número da pergunta (ex.: 10 para 'q10')
LINE_HEIGHT_OVERRIDE = {
    10: 20.0,  # mm -> Q10 ocupa 2x a altura padrão (~15.5 * 2)
}

def q_index_from_alias(alias: str) -> int:
    """Extrai o número NN do alias 'qNN_...'."""
    try:
        return int(alias[1:3])
    except Exception:
        return -1  # fallback seguro

def format_mes_ano(mes: str | None, ano: str | None) -> str:
    m = (mes or '').strip()
    a = (ano or '').strip()
    return f"{m} de {a}" if m and a else ""

def draw_header(c: canvas.Canvas, row: pd.Series, mes: str | None = None, ano: str | None = None, safe_name: str | None = None):
    """
    Desenha nome, sis_id, submitted e 'Mes de Ano' abaixo.
    Se mes/ano não vierem, tenta inferir do safe_name.
    """
    # se não veio mes/ano, inferir do safe_name
    if (not mes or not ano) and safe_name:
        mes_inf, ano_inf = infer_mes_ano_from_safe_name(safe_name)
        mes = mes or mes_inf
        ano = ano or ano_inf

    # cor do texto (já configurada nos estilos; aqui para drawString)
    c.setFillColor(TEXT_DARK_70)

    def draw_text(key_csv, x_mm, y_mm, font, size):
        c.setFont(font, size)
        val = str(row.get(key_csv, '')).strip()
        c.drawString(mmx(x_mm), mmy(y_mm), val)

    draw_text('name',      *FIELD_MAP['name'])
    draw_text('sis_id',    *FIELD_MAP['sis_id'])
    draw_text('submitted', *FIELD_MAP['submitted'])

    mes_ano = format_mes_ano(mes, ano)
    if mes_ano:
        x_sub, y_sub, _, _ = FIELD_MAP['submitted']
        c.setFont('OpenSans_Cond_Medium', 11)
        c.drawString(mmx(x_sub), mmy(y_sub - 6), mes_ano)

from typing import Optional

def draw_questions_grid(
    c: canvas.Canvas,
    styles,
    question_map: dict,
    row: pd.Series,
    start_index: int = 0,
    max_rows: Optional[int] = None,
    show_boundary: bool = False
):
    """
    Desenha perguntas/respostas em duas colunas, linha por linha,
    usando altura sob demanda para perguntas com override (ex.: Q10).
    """
    def qnum(alias: str) -> int:
        return int(alias[1:3])
    ordered = sorted(question_map.keys(), key=qnum)

    rows_limit = max_rows or GRID['rows_per_page']

    # Medidas base
    xL, wL = GRID['x_left'], GRID['w_left']
    wR     = GRID['w_right']
    gutter = GRID.get('gutter', 0.0)
    xR     = GRID['x_right'] if GRID['x_right'] is not None else (xL + wL + gutter)

    
    # Começa do topo da área e vai descendo conforme a altura efetiva de cada linha
    y_top = GRID['y_start']

    drawn = 0
    for idx in range(start_index, min(start_index + rows_limit, len(ordered))):
        alias   = ordered[idx]
        col_csv = question_map[alias]['csv_col']
        q_text  = (question_map[alias]['display'] or alias).replace('\u200b', '').strip()
        a_text  = str((row.get(col_csv, '') or '')).replace('\u200b', '').strip()

        # Número da pergunta (qNN) e altura efetiva (override para Q10)
        q_idx        = q_index_from_alias(alias)
        rh_default   = GRID['row_h']
        rh_effective = LINE_HEIGHT_OVERRIDE.get(q_idx, rh_default)

        # Paddings e altura interna (garante pelo menos 1 linha de leading)
        pad_x  = 0.6  # mm
        pad_y  = 0.4  # mm
        inner_h = rh_effective - 2 * pad_y
        min_h   = max(styles['Question'].leading, styles['Answer'].leading) * 0.3528  # pt -> mm
        inner_h = max(inner_h, min_h + 0.2)

        inner_wL = wL - 2 * pad_x
        inner_wR = wR - 2 * pad_x

        # --- Coordenadas corretas: desenhar do topo para baixo ---
        y_bottom = y_top - rh_effective  # base da linha atual

        # Card encostado (pergunta + resposta)
        card_x = xL
        card_w = (wL + gutter + wR)
        c.roundRect(mmx(card_x), mmy(y_bottom), mmx(card_w), mmy(rh_effective), 1.2, stroke=0, fill=0)

        # Frames dentro do card (usar y_bottom + padding)
        frame_q = Frame(
            mmx(xL + pad_x), mmy(y_bottom + pad_y),
            mmx(inner_wL),   mmy(inner_h),
            showBoundary=0
        )
        frame_q.addFromList([Paragraph(q_text, styles['Question'])], c)

        frame_a = Frame(
            mmx(xR + pad_x), mmy(y_bottom + pad_y),
            mmx(inner_wR),   mmy(inner_h),
            showBoundary=0
        )
        frame_a.addFromList([Paragraph(a_text, styles['Answer'])], c)

        # Avança para a próxima linha (novo topo é a base da linha atual)
        y_top = y_bottom
        drawn += 1

    # Retorna quantas linhas foram desenhadas e o novo topo (para uso futuro, se necessário)
    return drawn, y_top

# -------------------------------------------------------------------
# Geração de overlays (teste unitario e para todos)
# -------------------------------------------------------------------

def build_overlay_one_row(csv_path: Path,
                          fonts_dir: Path, 
                          output_dir: Path, 
                          show_boundary: bool = False, 
                          mes: str | None = None, 
                          ano: str | None = None,
                          safe_name: str | None = None
                          ):
    """
    Gera overlay de teste para APENAS 1 docente (primeira linha).
    """

    df = load_processed_csv(csv_path)
    question_map = build_question_map(df)
    if df.empty:
        raise ValueError("CSV está vazio.")

    row = df.iloc[0]
    docente = str(row.get('name', 'docente')).replace('/', '-').strip()

    # Debug opcional
    logging.info(f"Docente: {docente}")
    logging.info(f"Total de perguntas detectadas: {len(question_map)}")

    # PDF overlay
    register_fonts(fonts_dir)
    styles = get_styles()
    output_dir.mkdir(parents=True, exist_ok=True)

    # se não veio mes/ano, inferir do safe_name
    if (not mes or not ano) and safe_name:
        mes_inf, ano_inf = infer_mes_ano_from_safe_name(safe_name)
        mes = mes or mes_inf
        ano = ano or ano_inf

    # nome do overlay inclui mes/ano se disponíveis
    suffix = f"_{mes}_{ano}" if mes and ano else ""
    overlay_path = output_dir / f'overlay_{docente}{suffix}.pdf'

    c = canvas.Canvas(str(overlay_path), pagesize=A4)

    # Cabeçalho e grade (primeira página)
    draw_header(c, row, mes=mes, ano=ano, safe_name=safe_name)
    #draw_calibration_guides(c)         # << guia visual
    draw_questions_grid(c, styles, question_map, row, start_index=0, max_rows=GRID['rows_per_page'], show_boundary=show_boundary)

    # Caso haja mais perguntas que rows_per_page, paginar
    total_q = len(question_map)
    idx = GRID['rows_per_page']
    while idx < total_q:
        c.showPage()
        draw_header(c, row, mes=mes, ano=ano, safe_name=safe_name)  # opcional repetir o cabeçalho
        draw_questions_grid(c, styles, question_map, row, start_index=idx, max_rows=GRID['rows_per_page'], show_boundary=show_boundary)
        idx += GRID['rows_per_page']

    c.save()
    logging.info(f"Overlay gerado: {overlay_path}")

def build_overlays_all_rows(csv_path: Path, 
                            fonts_dir: Path, 
                            output_dir: Path, 
                            show_boundary: bool = False,
                            mes: str | None = None,
                            ano: str | None = None,
                            safe_name: str | None = None
                            ):
    """
    Gera overlays para TODOS os docentes (cada linha do CSV).
    """
    df = load_processed_csv(csv_path)
    question_map = build_question_map(df)
    register_fonts(fonts_dir)
    styles = get_styles()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if (not mes or not ano) and safe_name:
        mes_inf, ano_inf = infer_mes_ano_from_safe_name(safe_name)
        mes = mes or mes_inf
        ano = ano or ano_inf

    for _, row in df.iterrows():
        docente = str(row.get('name', 'docente')).replace('/', '-').strip()
        suffix = f"_{mes}_{ano}" if mes and ano else ""
        overlay_path = output_dir / f'overlay_{docente}{suffix}.pdf'

        c = canvas.Canvas(str(overlay_path), pagesize=A4)

        # Página 1
        draw_header(c, row, mes=mes, ano=ano, safe_name=safe_name)
        draw_questions_grid(c, styles, question_map, row, start_index=0, max_rows=GRID['rows_per_page'], show_boundary=show_boundary)

        # Paginação se necessário
        total_q = len(question_map)
        idx = GRID['rows_per_page']
        while idx < total_q:
            c.showPage()
            draw_header(c, row, mes=mes, ano=ano, safe_name=safe_name)  # opcional
            draw_questions_grid(c, styles, question_map, row, start_index=idx, max_rows=GRID['rows_per_page'], show_boundary=show_boundary)
            idx += GRID['rows_per_page']

        c.save()
        logging.info(f"Overlay gerado: {overlay_path}")

# -------------------------------------------------------------------
# Merge com template (1ª página mesclada, demais anexadas)
# -------------------------------------------------------------------
def merge_first_page_then_append(template_pdf: Path, overlay_pdf: Path, output_pdf: Path):
    """
    Mescla a PRIMEIRA página do overlay com a PRIMEIRA página do template (background/figma).
    Demais páginas do overlay (se houver) são anexadas sem template.
    """
    templ = PdfReader(str(template_pdf))
    over  = PdfReader(str(overlay_pdf))
    writer = PdfWriter()

    # 1) Mesclar primeira página
    base = templ.pages[0]
    first_over = over.pages[0]
    # A ordem "base.merge_page(first_over)" desenha o overlay por cima do template
    base.merge_page(first_over)  # PyPDF2 >= 3
    writer.add_page(base)

    # 2) Anexar demais páginas do overlay (se houver)
    for i in range(1, len(over.pages)):
        writer.add_page(over.pages[i])

    # 3) Salvar
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    with output_pdf.open('wb') as f:
        writer.write(f)


def merge_all_overlays_with_template(template_pdf: Path, overlays_dir: Path, output_dir: Path,
                                     mes: str | None = None, ano: str | None = None):
    """
    Itera todos os PDFs de overlay em overlays_dir, aplica o merge com o template e salva em output_dir.
    Se mes/ano forem fornecidos, usa no nome do arquivo final.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    overlays = sorted(overlays_dir.glob('overlay_*.pdf'))

    if not overlays:
        logging.warning("Nenhum overlay encontrado para mesclar.")
        return

    for overlay_pdf in overlays:    
        # extrai docente e tenta inferir mes/ano do nome do overlay
        stem = overlay_pdf.stem  # ex.: 'overlay_Joao Silva_Junho_2025'
        m_mes_ano = re.search(r'_(janeiro|fevereiro|mar[cç]o|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)_(\d{4})$', stem, re.IGNORECASE)
        if m_mes_ano:
            mes_key = m_mes_ano.group(1).lower().replace('ç', 'c')
            ano_det = m_mes_ano.group(2)
            mes_det = PT_MONTHS.get(mes_key, mes_key.capitalize())
            mes_f = mes or mes_det
            ano_f = ano or ano_det
        else:
            mes_f = mes
            ano_f = ano
        docente = stem.replace('overlay_', '').replace(f'_{mes_f}_{ano_f}', '').strip() if mes_f and ano_f else stem.replace('overlay_', '').strip()
        final_name = f"Relatório {mes_f} {ano_f} - {docente}.pdf" if mes_f and ano_f else f"Relatório - {docente}.pdf"

        output_pdf = output_dir / final_name
        merge_first_page_then_append(template_pdf, overlay_pdf, output_pdf)
        logging.info(f"Mesclado: {output_pdf}")