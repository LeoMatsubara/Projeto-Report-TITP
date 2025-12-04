
# ReportLab: cria o PDF e desenha elementos
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# svglib: converte SVG em um 'drawing' que o ReportLab consegue desenhar
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF

# (opcional) para textos longos com quebra automática:
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import getSampleStyleSheet
