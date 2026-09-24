from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output" / "pdf" / "Informe_Experimento_H4_3_1.pdf"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="Title2", parent=styles["Title"], alignment=TA_CENTER, textColor=colors.HexColor("#12324A"), spaceAfter=12))
styles.add(ParagraphStyle(name="H2x", parent=styles["Heading2"], textColor=colors.HexColor("#146C94"), spaceBefore=10, spaceAfter=6))
styles.add(ParagraphStyle(name="Bodyx", parent=styles["BodyText"], fontSize=9, leading=12, spaceAfter=6))
styles.add(ParagraphStyle(name="Smallx", parent=styles["BodyText"], fontSize=7.4, leading=9))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#607080"))
    canvas.drawString(15 * mm, 10 * mm, "Solventa - Experimento H4.3.1")
    canvas.drawRightString(282 * mm, 10 * mm, f"Pagina {doc.page}")
    canvas.restoreState()


def table(rows, widths):
    data = [[Paragraph(str(cell), styles["Smallx"]) for cell in row] for row in rows]
    result = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12324A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#AAB8C2")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F6F8")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return result


vertical = [
    ["CPU / memoria", "TPS", "Logrados", "p95 ms", "p99 ms", "Errores %", "Descartadas"],
    ["1 / 1 GiB", 200, "199,88", "11,11", "57,65", "0,000", 0],
    ["1 / 1 GiB", 500, "493,56", "634,84", "1.571,83", "0,000", 95],
    ["1 / 1 GiB", 800, "799,85", "29,56", "62,37", "0,000", 0],
    ["1 / 1 GiB", 1100, "919,85", "1.637,24", "1.715,96", "0,000", 1852],
    ["1 / 1 GiB", 1400, "877,55", "4.187,90", "4.904,78", "0,000", 6993],
    ["2 / 2 GiB", 200, "199,99", "6,32", "14,46", "0,000", 0],
    ["2 / 2 GiB", 500, "499,91", "6,72", "49,47", "0,000", 0],
    ["2 / 2 GiB", 800, "799,84", "21,20", "40,71", "0,000", 0],
    ["2 / 2 GiB", 1100, "1.001,19", "1.019,29", "1.431,81", "0,000", 1096],
    ["2 / 2 GiB", 1400, "965,38", "3.064,70", "3.236,13", "0,000", 5675],
]

horizontal = [
    ["Instancias", "CPU / memoria c/u", "TPS", "Logrados", "p95 ms", "p99 ms", "Errores %", "Descartadas"],
    [3, "1 / 1 GiB", 200, "199,96", "9,54", "15,81", "0,000", 0],
    [3, "1 / 1 GiB", 500, "499,86", "8,48", "19,30", "0,000", 0],
    [3, "1 / 1 GiB", 800, "799,59", "9,49", "30,08", "0,000", 0],
    [3, "1 / 1 GiB", 1100, "1.099,59", "8,25", "18,40", "0,000", 0],
    [3, "1 / 1 GiB", 1400, "1.399,42", "9,56", "40,65", "0,000", 0],
]

story = [
    Paragraph("Experimento individual de escalabilidad H4.3.1", styles["Title2"]),
    Paragraph("Reprocesamiento masivo de perfiles / Open Data", styles["Heading2"]),
    Paragraph("Objetivo: evaluar escalamiento vertical y horizontal con carga progresiva hasta 1.400 TPS. Criterios: p95 <= 400 ms, p99 <= 800 ms y errores < 1%.", styles["Bodyx"]),
    Paragraph("Implementacion", styles["H2x"]),
    Paragraph("Se implemento POST /perfilamiento/reprocesar, un escenario k6 de tasa constante, composiciones Docker para ambas tacticas, balanceo Nginx local y GET /health para el balanceador AWS. Todo esta en la rama experimento-escalabilidad-h4-3-1; main no fue modificado.", styles["Bodyx"]),
    Paragraph("Entorno AWS", styles["H2x"]),
    Paragraph("AWS Academy, us-east-1. Tres EC2 t2.medium para la aplicacion en tres zonas, una EC2 para PostgreSQL 16 y Application Load Balancer Cheapest-alb. k6 0.55.0 se ejecuto desde CloudShell durante 15 s por nivel. Commit desplegado: 12bc015.", styles["Bodyx"]),
    Paragraph("Riesgo de correspondencia del ASR", styles["H2x"]),
    Paragraph("El repositorio no contenia el flujo completo de perfilamiento ni un canal en linea. El endpoint agrega una operacion minima y realista sobre PostgreSQL para representar reprocesamiento. Por tanto, los resultados validan la tactica y el arnes experimental, no la capacidad definitiva de una futura logica de negocio completa.", styles["Bodyx"]),
    PageBreak(),
    Paragraph("Resultados AWS - escalamiento vertical", styles["H2x"]),
    table(vertical, [28*mm, 18*mm, 22*mm, 22*mm, 22*mm, 20*mm, 23*mm]),
    Spacer(1, 8),
    Paragraph("Con 2 CPU/2 GiB se sostuvo hasta 800 TPS dentro de los criterios. A 1.100 y 1.400 TPS la instancia unica excedio p95/p99 y descarto iteraciones. El t2.medium limita el experimento vertical a 2 vCPU fisicos.", styles["Bodyx"]),
    PageBreak(),
    Paragraph("Resultados AWS - escalamiento horizontal", styles["H2x"]),
    table(horizontal, [20*mm, 34*mm, 18*mm, 22*mm, 20*mm, 20*mm, 20*mm, 23*mm]),
    Spacer(1, 10),
    Paragraph("A 1.400 TPS, tres instancias lograron 1.399,42 TPS, p95 9,56 ms, p99 40,65 ms, 0% de errores y cero descartes. Los tres destinos estaban saludables en el ALB.", styles["Bodyx"]),
    Paragraph("Analisis y decision", styles["H2x"]),
    Paragraph("La hipotesis queda respaldada en AWS: el escalamiento horizontal supera claramente a una sola instancia incluso despues de duplicar sus recursos. Se recomienda horizontal como tactica principal y vertical como ajuste inicial. La tasa maxima equivale aproximadamente a 10,08 millones de perfiles en dos horas si se sostiene.", styles["Bodyx"]),
    Paragraph("Limitaciones", styles["H2x"]),
    Paragraph("Las corridas AWS duraron 15 s para ajustarse al presupuesto academico. Falta una prueba de estabilidad de dos horas, incorporar la logica completa futura y medir simultaneamente el canal en linea cuando exista. PostgreSQL se ejecuto en EC2, no en RDS.", styles["Bodyx"]),
    Paragraph("Evidencia y reproduccion", styles["H2x"]),
    Paragraph("Los valores exactos estan versionados en experiments/h4.3.1/AWS_RESULTADOS.tsv y el procedimiento en experiments/h4.3.1/README.md. Los JSON crudos quedaron en AWS CloudShell como ~/h431-aws-results.tgz. Para el video: mostrar las tres instancias saludables, el ALB, el codigo, ejecutar k6 y presentar las tablas de este informe.", styles["Bodyx"]),
]

OUT.parent.mkdir(parents=True, exist_ok=True)
doc = SimpleDocTemplate(str(OUT), pagesize=landscape(A4), leftMargin=15*mm, rightMargin=15*mm, topMargin=14*mm, bottomMargin=16*mm, title="Experimento H4.3.1")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)
