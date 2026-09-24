from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output" / "video"
SLIDES = OUT / "slides"
W, H = 1920, 1080
NAVY = "#12324A"
BLUE = "#146C94"
LIGHT = "#F4F7F9"
GREEN = "#2E7D32"
RED = "#B3261E"
GRAY = "#607080"
WHITE = "#FFFFFF"
BLACK = "#111111"
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
MONO = "/System/Library/Fonts/Supplemental/Courier New.ttf"


def font(size, bold=False, mono=False):
    return ImageFont.truetype(MONO if mono else (BOLD if bold else FONT), size)


def wrap(draw, text, box, size=42, color=BLACK, bold=False, spacing=15, bullet=False):
    x, y, width, _height = box
    f = font(size, bold)
    avg = max(1, int(width / (size * 0.54)))
    lines = textwrap.wrap(text, width=avg, break_long_words=False)
    for line in lines:
        prefix = "•  " if bullet and line == lines[0] else "   " if bullet else ""
        draw.text((x, y), prefix + line, font=f, fill=color)
        y += size + spacing
    return y


def base(title, section, number):
    im = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 88), fill=NAVY)
    d.text((70, 26), section.upper(), font=font(27, True), fill=WHITE)
    d.text((W - 70, 28), f"H4.3.1   {number}/10", font=font(23), fill="#D7E5EE", anchor="ra")
    d.text((70, 125), title, font=font(54, True), fill=BLACK)
    d.line((70, 202, W - 70, 202), fill="#C9D4DB", width=3)
    d.text((70, H - 48), "Solventa   Experimento individual de escalabilidad", font=font(22), fill=GRAY)
    d.text((W - 70, H - 48), "Rama experimento-escalabilidad-h4-3-1", font=font(21), fill=GRAY, anchor="ra")
    return im, d


def panel(d, xy, fill=LIGHT, outline="#D5DEE4", radius=24):
    d.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=3)


def save(im, n):
    SLIDES.mkdir(parents=True, exist_ok=True)
    im.save(SLIDES / f"slide-{n:02d}.png")


def title_slide():
    im = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, H), fill=NAVY)
    d.rectangle((0, 0, 22, H), fill="#2C91C2")
    d.text((120, 180), "EXPERIMENTO INDIVIDUAL", font=font(32, True), fill="#89C8E8")
    d.text((120, 260), "Escalabilidad H4.3.1", font=font(78, True), fill=WHITE)
    d.text((120, 375), "Reprocesamiento masivo de perfiles con Open Data", font=font(40), fill="#E6F1F6")
    d.line((120, 465, 1510, 465), fill="#5EAED4", width=5)
    d.text((120, 530), "Comparación de escalamiento vertical y horizontal hasta 1.400 TPS", font=font(34), fill=WHITE)
    d.text((120, 650), "Beraly Ventura", font=font(38, True), fill=WHITE)
    d.text((120, 710), "ISIS2212   Sprint 1", font=font(30), fill="#C8DCE7")
    panel(d, (1340, 610, 1780, 835), fill="#1D4965", outline="#5EAED4")
    d.text((1560, 665), "RESULTADO", font=font(25, True), fill="#89C8E8", anchor="ma")
    d.text((1560, 725), "1.399,42 TPS", font=font(42, True), fill=WHITE, anchor="ma")
    d.text((1560, 790), "Horizontal cumple", font=font(27), fill="#A7D8A9", anchor="ma")
    d.text((120, 970), "Video sin voz preparado para narración", font=font(24), fill="#A9C6D5")
    save(im, 1)


def objective_slide():
    im, d = base("Objetivo y criterios de aceptación", "Problema", 2)
    panel(d, (70, 245, 1040, 890))
    d.text((115, 285), "ASR H4.3.1", font=font(34, True), fill=BLUE)
    y = wrap(d, "Reprocesar al menos 10 millones de perfiles en menos de dos horas al incorporar nuevas fuentes de Open Data.", (115, 350, 850, 200), 42)
    panel(d, (115, y + 30, 990, y + 190), fill="#E7F2F8", outline="#9AC8DD")
    d.text((552, y + 70), "10.000.000 / 7.200 s = 1.388,89 perfiles/s", font=font(34, True), fill=NAVY, anchor="ma")
    d.text((552, y + 125), "Carga máxima del experimento  1.400 TPS", font=font(30), fill=BLUE, anchor="ma")
    d.text((115, 760), "Carga progresiva", font=font(30, True), fill=BLACK)
    d.text((115, 815), "200   →   500   →   800   →   1.100   →   1.400 TPS", font=font(34, True), fill=NAVY)
    items = [("p95", "≤ 400 ms"), ("p99", "≤ 800 ms"), ("Errores", "< 1 %"), ("Descartes", "0 deseable")]
    y = 285
    for name, value in items:
        panel(d, (1130, y, 1810, y + 125), fill=WHITE)
        d.text((1180, y + 34), name, font=font(31, True), fill=NAVY)
        d.text((1760, y + 35), value, font=font(31, True), fill=GREEN, anchor="ra")
        y += 145
    save(im, 2)


def github_slide():
    im, d = base("Trabajo aislado en una rama", "Repositorio", 3)
    screenshot = Path("/Users/genesisparada/Downloads/Captura de pantalla 2026-09-24 a la(s) 10.18.27 a. m..png")
    if screenshot.exists():
        shot = Image.open(screenshot).convert("RGB")
        shot.thumbnail((1160, 690))
        sx, sy = 70, 245
        panel(d, (sx - 8, sy - 8, sx + shot.width + 8, sy + shot.height + 8), fill="#FFFFFF")
        im.paste(shot, (sx, sy))
    panel(d, (1300, 245, 1810, 870), fill=LIGHT)
    d.text((1350, 290), "Rama evaluada", font=font(30, True), fill=BLUE)
    wrap(d, "experimento-escalabilidad-h4-3-1", (1350, 350, 400, 180), 32, NAVY, True)
    y = 500
    for text, color in [("• main no fue modificado", GREEN), ("• Código y pruebas versionados", GREEN), ("• Informe y resultados incluidos", GREEN), ("• Commit final 52ef5f5", GREEN)]:
        y = wrap(d, text, (1350, y, 390, 100), 28, color, False, 8) + 22
    save(im, 3)


def code_slide():
    im, d = base("Flujo implementado en NestJS", "Código", 4)
    panel(d, (70, 240, 925, 895), fill="#101820", outline="#304452")
    d.text((105, 270), "perfilamiento.controller.ts", font=font(25, True), fill="#8BD5FF")
    code1 = """@Controller('perfilamiento')
export class PerfilamientoController {
  @Post('reprocesar')
  @HttpCode(200)
  reprocesar(@Body() dto) {
    return this.perfilamientoService
      .reprocesar(dto);
  }
}"""
    d.multiline_text((105, 325), code1, font=font(28, mono=True), fill="#E7EDF1", spacing=13)
    d.text((105, 705), "app.controller.ts", font=font(25, True), fill="#8BD5FF")
    d.multiline_text((105, 755), "@Get('health')\nhealth() { return { status: 'ok' }; }", font=font(27, mono=True), fill="#E7EDF1", spacing=12)
    panel(d, (995, 240, 1810, 895))
    d.text((1040, 285), "Qué realiza cada solicitud", font=font(32, True), fill=BLUE)
    steps = [
        ("1", "Recibe clienteId y señales Open Data"),
        ("2", "Calcula un score de riesgo entre 0 y 100"),
        ("3", "Ejecuta un upsert idempotente en PostgreSQL"),
        ("4", "Devuelve HTTP 200 con el perfil reprocesado"),
    ]
    y = 365
    for num, text in steps:
        d.ellipse((1040, y, 1100, y + 60), fill=BLUE)
        d.text((1070, y + 15), num, font=font(25, True), fill=WHITE, anchor="ma")
        wrap(d, text, (1130, y + 4, 610, 100), 29, BLACK)
        y += 125
    d.text((1040, 825), "GET /health permite validar destinos en el ALB", font=font(27, True), fill=GREEN)
    save(im, 4)


def architecture_slide():
    im, d = base("Arquitectura usada en AWS Academy", "Despliegue", 5)
    d.text((115, 275), "Generador", font=font(27, True), fill=GRAY)
    panel(d, (80, 325, 430, 565), fill="#E8F3F8", outline="#9BC8DB")
    d.text((255, 395), "AWS CloudShell", font=font(34, True), fill=NAVY, anchor="ma")
    d.text((255, 455), "k6 0.55.0", font=font(31), fill=BLUE, anchor="ma")
    d.text((255, 510), "200 → 1.400 TPS", font=font(27), fill=BLACK, anchor="ma")
    d.line((430, 445, 650, 445), fill=BLUE, width=8)
    d.polygon([(650, 445), (620, 428), (620, 462)], fill=BLUE)
    panel(d, (650, 325, 1050, 565), fill="#FFF4DE", outline="#E1B970")
    d.text((850, 390), "Application", font=font(31, True), fill=NAVY, anchor="ma")
    d.text((850, 438), "Load Balancer", font=font(31, True), fill=NAVY, anchor="ma")
    d.text((850, 505), "Cheapest-alb", font=font(25), fill=GRAY, anchor="ma")
    for i, x in enumerate((1170, 1430, 1690), 1):
        d.line((1050, 445, x, 445), fill="#8AA0AD", width=4)
        panel(d, (x - 105, 335, x + 105, 555), fill="#EAF4EA", outline="#8AB98A")
        d.text((x, 380), f"API {i}", font=font(30, True), fill=NAVY, anchor="ma")
        d.text((x, 435), "EC2 t2.medium", font=font(22), fill=BLACK, anchor="ma")
        d.text((x, 485), "1 CPU / 1 GiB", font=font(22), fill=GRAY, anchor="ma")
        d.text((x, 525), "● healthy", font=font(22, True), fill=GREEN, anchor="ma")
    d.line((1430, 555, 1430, 680), fill="#8AA0AD", width=5)
    panel(d, (1190, 680, 1670, 875), fill="#F1ECF8", outline="#B4A0CC")
    d.text((1430, 730), "PostgreSQL 16", font=font(34, True), fill=NAVY, anchor="ma")
    d.text((1430, 790), "Cuarta instancia EC2", font=font(27), fill=BLACK, anchor="ma")
    d.text((1430, 840), "Misma base para ambas tácticas", font=font(23), fill=GRAY, anchor="ma")
    d.text((90, 730), "Vertical", font=font(30, True), fill=BLUE)
    d.text((90, 785), "Una instancia; CPU y memoria aumentan.", font=font(28), fill=BLACK)
    d.text((90, 845), "Horizontal", font=font(30, True), fill=BLUE)
    d.text((90, 900), "Tres instancias detrás del balanceador.", font=font(28), fill=BLACK)
    save(im, 5)


def k6_slide():
    im, d = base("Carga progresiva y métricas con k6", "Ejecución", 6)
    panel(d, (70, 240, 1040, 900), fill="#101820", outline="#304452")
    d.text((110, 275), "reprocesamiento.js", font=font(25, True), fill="#8BD5FF")
    code = """executor: 'constant-arrival-rate'
rate: RATE
duration: DURATION
maxVUs: 2000

thresholds:
  p(95) <= 400 ms
  p(99) <= 800 ms
  errores < 1 %

POST /perfilamiento/reprocesar
check: HTTP 200"""
    d.multiline_text((110, 340), code, font=font(31, mono=True), fill="#E7EDF1", spacing=18)
    panel(d, (1120, 240, 1810, 900))
    d.text((1170, 285), "Qué se registra", font=font(33, True), fill=BLUE)
    metrics = [
        ("Throughput", "http_reqs.rate"),
        ("Latencia", "p95 y p99"),
        ("Fallos", "http_req_failed"),
        ("Capacidad", "dropped_iterations"),
    ]
    y = 370
    for name, detail in metrics:
        d.text((1170, y), name, font=font(29, True), fill=NAVY)
        d.text((1170, y + 47), detail, font=font(27), fill=GRAY)
        d.line((1170, y + 90, 1750, y + 90), fill="#D7DFE4", width=2)
        y += 115
    panel(d, (1170, 825, 1760, 900), fill="#EAF4EA", outline="#8AB98A")
    d.text((1465, 848), "15 s por nivel para proteger créditos", font=font(24, True), fill=GREEN, anchor="ma")
    save(im, 6)


def result_slide(vertical_mode=True):
    n = 7 if vertical_mode else 8
    title = "Resultado del escalamiento vertical" if vertical_mode else "Resultado del escalamiento horizontal"
    im, d = base(title, "Resultados", n)
    headers = ["Configuración", "TPS", "Logrados", "p95 ms", "p99 ms", "Descartes"]
    if vertical_mode:
        rows = [
            ["1 CPU / 1 GiB", "800", "799,85", "29,56", "62,37", "0"],
            ["1 CPU / 1 GiB", "1.400", "877,55", "4.187,90", "4.904,78", "6.993"],
            ["2 CPU / 2 GiB", "800", "799,84", "21,20", "40,71", "0"],
            ["2 CPU / 2 GiB", "1.400", "965,38", "3.064,70", "3.236,13", "5.675"],
        ]
        status, status_color = "NO CUMPLE A 1.400 TPS", RED
        note = "Aumentar recursos mejora la capacidad, pero la instancia única se satura en los niveles altos."
    else:
        rows = [
            ["3 × 1 CPU / 1 GiB", "200", "199,96", "9,54", "15,81", "0"],
            ["3 × 1 CPU / 1 GiB", "800", "799,59", "9,49", "30,08", "0"],
            ["3 × 1 CPU / 1 GiB", "1.100", "1.099,59", "8,25", "18,40", "0"],
            ["3 × 1 CPU / 1 GiB", "1.400", "1.399,42", "9,56", "40,65", "0"],
        ]
        status, status_color = "CUMPLE EN TODOS LOS NIVELES", GREEN
        note = "La configuración horizontal sostiene la carga ofrecida, sin errores ni iteraciones descartadas."
    x0, y0 = 70, 265
    widths = [380, 190, 260, 260, 260, 250]
    x = x0
    for h, w in zip(headers, widths):
        d.rectangle((x, y0, x + w, y0 + 90), fill=NAVY, outline="#D9D9D9", width=2)
        d.text((x + w / 2, y0 + 32), h, font=font(24, True), fill=WHITE, anchor="ma")
        x += w
    for ridx, row in enumerate(rows):
        x = x0
        y = y0 + 90 + ridx * 100
        fill = WHITE if ridx % 2 == 0 else "#EEF4F7"
        for cidx, (value, w) in enumerate(zip(row, widths)):
            d.rectangle((x, y, x + w, y + 100), fill=fill, outline="#D9D9D9", width=2)
            d.text((x + (18 if cidx == 0 else w / 2), y + 37), value, font=font(25, cidx == 0), fill=BLACK, anchor="la" if cidx == 0 else "ma")
            x += w
    panel(d, (70, 745, 1810, 855), fill="#FCECEB" if vertical_mode else "#EAF4EA", outline=status_color)
    d.text((940, 778), status, font=font(35, True), fill=status_color, anchor="ma")
    d.text((940, 910), note, font=font(28), fill=BLACK, anchor="ma")
    save(im, n)


def comparison_slide():
    im, d = base("Comparación a la carga máxima", "Decisión", 9)
    d.text((480, 275), "Vertical 2 CPU / 2 GiB", font=font(32, True), fill=RED, anchor="ma")
    d.text((1440, 275), "Horizontal 3 instancias", font=font(32, True), fill=GREEN, anchor="ma")
    metrics = [
        ("TPS logrados", "965,38", "1.399,42"),
        ("p95", "3.064,70 ms", "9,56 ms"),
        ("p99", "3.236,13 ms", "40,65 ms"),
        ("Errores", "0 %", "0 %"),
        ("Descartes", "5.675", "0"),
    ]
    y = 350
    for label, left, right in metrics:
        d.text((960, y + 30), label, font=font(27, True), fill=GRAY, anchor="ma")
        panel(d, (150, y, 760, y + 95), fill="#FCECEB", outline="#E5A6A2")
        panel(d, (1160, y, 1770, y + 95), fill="#EAF4EA", outline="#9FC89F")
        d.text((455, y + 27), left, font=font(32, True), fill=RED, anchor="ma")
        d.text((1465, y + 27), right, font=font(32, True), fill=GREEN, anchor="ma")
        y += 120
    panel(d, (250, 930, 1670, 1000), fill=NAVY, outline=NAVY)
    d.text((960, 948), "Recomendación  Escalamiento horizontal como táctica principal", font=font(30, True), fill=WHITE, anchor="ma")
    save(im, 9)


def conclusion_slide():
    im, d = base("Conclusión, limitaciones y entrega", "Cierre", 10)
    panel(d, (70, 245, 1060, 865), fill=LIGHT)
    d.text((120, 285), "Conclusión", font=font(34, True), fill=BLUE)
    bullets = [
        "Horizontal sostuvo 1.399,42 TPS.",
        "p95 9,56 ms y p99 40,65 ms.",
        "0 % de errores y cero descartes.",
        "Equivale a 10,08 millones de perfiles en dos horas si se sostiene.",
    ]
    y = 355
    for item in bullets:
        y = wrap(d, item, (120, y, 850, 100), 32, BLACK, False, 10, True) + 24
    d.text((120, 705), "Decisión", font=font(31, True), fill=BLUE)
    wrap(d, "Usar escalamiento horizontal; vertical únicamente como ajuste inicial.", (120, 755, 850, 120), 27, GREEN, True)
    panel(d, (1130, 245, 1810, 865), fill=WHITE)
    d.text((1180, 285), "Limitaciones declaradas", font=font(32, True), fill=BLUE)
    limits = ["15 segundos por nivel", "Una corrida AWS por configuración", "PostgreSQL en EC2, no RDS", "Sin canal en línea para medir degradación", "Lógica de negocio aún mínima"]
    y = 360
    for item in limits:
        y = wrap(d, item, (1180, y, 560, 95), 29, BLACK, False, 8, True) + 20
    panel(d, (1130, 820, 1810, 920), fill="#E7F2F8", outline="#9AC8DD")
    d.text((1470, 850), "Código, datos e informe en la rama", font=font(26, True), fill=NAVY, anchor="ma")
    d.text((960, 970), "Fin del video   Añade aquí tu voz y el enlace final de entrega", font=font(27, True), fill=GRAY, anchor="ma")
    save(im, 10)


def write_script():
    script = """GUION SINCRONIZADO  VIDEO H4.3.1  DURACIÓN 4:30

00:00–00:15
Hola, soy Beraly Ventura. Presentaré el experimento individual de escalabilidad H4.3.1 del proyecto Solventa.

00:15–00:40
El escenario exige reprocesar 10 millones de perfiles en menos de dos horas cuando se incorporan nuevas fuentes de Open Data. Esto requiere cerca de 1.389 perfiles por segundo, por lo que la carga máxima se fijó en 1.400 TPS. Los criterios fueron p95 menor o igual a 400 milisegundos, p99 menor o igual a 800 y menos del uno por ciento de errores.

00:40–01:05
El trabajo está en la rama experimento-escalabilidad-h4-3-1. Main no fue modificado. La rama contiene el código, las pruebas, los datos obtenidos y el informe.

01:05–01:40
Se implementó POST perfilamiento reprocesar. Cada solicitud recibe señales Open Data, calcula un score y realiza un upsert idempotente en PostgreSQL. También se agregó GET health para que el balanceador verifique la disponibilidad de cada instancia.

01:40–02:10
El despliegue se ejecutó en AWS Academy, región us-east-1. Se utilizaron tres EC2 t2.medium para la aplicación, una cuarta EC2 con PostgreSQL 16 y un Application Load Balancer. En la configuración horizontal, los tres destinos estuvieron saludables.

02:10–02:35
k6 se ejecutó desde CloudShell con tasa constante y niveles de 200, 500, 800, 1.100 y 1.400 TPS. Se midieron throughput, p95, p99, errores e iteraciones descartadas. Cada nivel duró 15 segundos para proteger los créditos del laboratorio.

02:35–03:05
En vertical, aumentar de una a dos CPU mejoró la capacidad, pero no permitió sostener 1.400 TPS. Con dos CPU y dos GiB se lograron 965,38 TPS, p95 de 3.064,70 milisegundos, p99 de 3.236,13 y 5.675 iteraciones descartadas. Esta táctica no cumplió.

03:05–03:35
En horizontal, tres instancias sostuvieron 1.399,42 TPS. La p95 fue 9,56 milisegundos y la p99 40,65. No hubo errores ni iteraciones descartadas. Esta configuración cumplió todos los criterios en todos los niveles.

03:35–04:05
La comparación muestra que el escalamiento horizontal conserva el throughput y mantiene latencias muy inferiores a los límites. Se recomienda horizontal como táctica principal y vertical solo como ajuste inicial.

04:05–04:30
La tasa máxima equivale aproximadamente a 10,08 millones de perfiles en dos horas si se sostiene. Las pruebas duraron 15 segundos, PostgreSQL estuvo en EC2 y aún no existe el canal en línea completo. Una validación futura debe durar dos horas, repetirse varias veces e incluir RDS y la lógica definitiva. El código, los datos y el informe están disponibles en la rama del experimento.
"""
    (OUT / "Guion_video_H4_3_1.txt").write_text(script, encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    title_slide(); objective_slide(); github_slide(); code_slide(); architecture_slide(); k6_slide()
    result_slide(True); result_slide(False); comparison_slide(); conclusion_slide(); write_script()
    print(SLIDES)


if __name__ == "__main__":
    main()
