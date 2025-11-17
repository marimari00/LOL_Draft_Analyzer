"""Gera relatório em PDF com seções detalhadas e gráfico de confiança."""
from __future__ import annotations

import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

OUTPUT_PATH = Path("docs/Relatorio_Precisao_SoloQ_Pro.pdf")
PAGE_WIDTH = 612  # 8.5 pol
PAGE_HEIGHT = 792  # 11 pol
MARGIN_LEFT = 64
MARGIN_RIGHT = 64
MARGIN_TOP = 720
MARGIN_BOTTOM = 72


SUMMARY_POINTS = [
    "O motor híbrido combina logistic regression, random forest e gradient boosting com um modelo SGD treinado em 1.000.000 de rascunhos, reduzindo ruído para qualquer fase de draft.",
    "SoloQ e Pro compartilham o mesmo endpoint em backend/draft_api.py; as diferenças de banimento são tratadas apenas no frontend, garantindo paridade de qualidade.",
    "A reponderação pelo blue side prior protege o cálculo contra vieses regionais e estabiliza decisões apresentadas aos treinadores.",
]

TECH_CONTEXT = [
    "Loader do backend inicializa predictor, índices de campeões e atributos, além do bundle models/simulated_sgd.pkl para inferência combinada.",
    "frontend/src/App.js mantém a mesma requisição POST /draft/recommend tanto para SoloQ quanto para Pro, alterando somente os slots de execução.",
    "A simulação mais recente usa data/matches/multi_region_10k.json (9.999 partidas reais) e publica estatísticas consolidadas em data/simulations/simulation_10k_games.json.",
    "O painel HealthDashboard.js já consulta /health e /simulations/summary, expondo a existência e a data da simulação corrente.",
]

QUANT_TABLE = [
    ("Jogos simulados", "1.000.000", "validation/ml_simulation.py"),
    ("Taxa azul prevista", "63,59%", "simulation_10k_games.json"),
    ("Confiança média", "54,24%", "simulation_10k_games.json"),
    ("Modelos ensemble", "LR + RF + GB", "trained_models.pkl"),
    ("Peso do simulador", "35%", "backend/draft_api.py"),
]

CONFIDENCE_BUCKETS = [
    ("Alta (≥60%)", 69427),
    ("Média (55-60%)", 271082),
    ("Baixa (<55%)", 659491),
]

SOLOQ_IMPACT = [
    "Projeções são calculadas somente após dois picks reais por lado, evitando sinais falsos em drafts turbulentos.",
    "Os alertas de composição antecipam ausência de frontline, engage ou mistura de dano antes das últimas escolhas.",
    "A telemetria planejada para SoloQ permitirá medir taxa de aceitação das recomendações e ajustar pesos de archetype debt.",
]

PRO_IMPACT = [
    "As projeções acompanham cronogramas rígidos de pick/ban e alimentam rationale_tags e win_projection diretamente no painel da comissão técnica.",
    "Com o blend de 65/35, o modelo absorve scrims simuladas de forma previsível e reduz surpresas entre etapa de análise e palco.",
    "O HealthDashboard operacionaliza auditoria diária para staff, registrando ausência de modelos ou simulações desatualizadas.",
]

RISK_POINTS = [
    "Dependência de apenas 9.999 partidas reais Diamond+ limita visão sobre patches específicos; novas coletas Challenger e torneios profissionais são prioritárias.",
    "Ainda não existe feedback automático das partidas disputadas pelos usuários do app, o que impede aprendizado supervisionado em produção.",
    "Alterações no peso do simulador requerem recalibração formal; ajustes empíricos podem introduzir oscilações em matchups extremos.",
]

NEXT_STEPS = [
    "Rodar coleta ampliada (Challenger + ligas oficiais) e atualizar data/matches/ a cada trimestre fiscal.",
    "Publicar relatórios de calibração e confiabilidade junto ao endpoint /simulations/summary para cada lote de 1M simulações.",
    "Instrumentar telemetria de aceitação/rejeição das sugestões SoloQ para medir retorno sobre o assistente.",
    "Definir revisão trimestral do blue side prior considerando metas presenciais e torneios com side selection assimétrico.",
]


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


@dataclass
class PDFBuilder:
    """Constrói páginas em PDF com comandos básicos."""

    pages: List[str]
    current: List[str] | None = None

    def start_page(self) -> None:
        if self.current is not None:
            self.finish_page()
        self.current = []

    def finish_page(self) -> None:
        if self.current:
            self.pages.append("\n".join(self.current))
        self.current = []

    def text(self, x: float, y: float, message: str, font: str = "F1", size: int = 11) -> None:
        if self.current is None:
            raise RuntimeError("Página não inicializada")
        safe = _escape(message)
        self.current.append("BT")
        self.current.append(f"/{font} {size} Tf")
        self.current.append(f"{x:.2f} {y:.2f} Td")
        self.current.append(f"({safe}) Tj")
        self.current.append("ET")

    def line(self, x1: float, y1: float, x2: float, y2: float) -> None:
        if self.current is None:
            raise RuntimeError("Página não inicializada")
        self.current.append(f"{x1:.2f} {y1:.2f} m")
        self.current.append(f"{x2:.2f} {y2:.2f} l S")

    def rect(self, x: float, y: float, width: float, height: float, stroke: bool = True) -> None:
        if self.current is None:
            raise RuntimeError("Página não inicializada")
        cmd = "S" if stroke else "n"
        self.current.append(f"{x:.2f} {y:.2f} {width:.2f} {height:.2f} re {cmd}")

    def fill_rect(self, x: float, y: float, width: float, height: float, gray: float = 0.9) -> None:
        if self.current is None:
            raise RuntimeError("Página não inicializada")
        self.current.append(f"{gray:.2f} g")
        self.current.append(f"{x:.2f} {y:.2f} {width:.2f} {height:.2f} re f")
        self.current.append("0 g")


class ReportLayout:
    def __init__(self, builder: PDFBuilder):
        self.builder = builder
        self.page_number = 0
        self.cursor_y = 0.0
        self.builder.start_page()
        self._new_page()

    def _new_page(self) -> None:
        if self.page_number:
            self._footer()
            self.builder.start_page()
        self.page_number += 1
        self.cursor_y = MARGIN_TOP
        self._header()

    def _header(self) -> None:
        title = "Draft Analyzer | Relatório Executivo"
        self.builder.text(MARGIN_LEFT, PAGE_HEIGHT - 48, title, font="F2", size=11)
        self.builder.line(MARGIN_LEFT, PAGE_HEIGHT - 54, PAGE_WIDTH - MARGIN_RIGHT, PAGE_HEIGHT - 54)

    def _footer(self) -> None:
        footer = f"Página {self.page_number}"
        self.builder.text(PAGE_WIDTH / 2 - 24, MARGIN_BOTTOM - 24, footer, size=10)

    def _ensure_space(self, needed: float) -> None:
        if self.cursor_y - needed < MARGIN_BOTTOM:
            self._new_page()

    def add_heading(self, text: str) -> None:
        self._ensure_space(40)
        self.builder.text(MARGIN_LEFT, self.cursor_y, text, font="F2", size=18)
        self.cursor_y -= 28
        self.builder.line(MARGIN_LEFT, self.cursor_y + 12, PAGE_WIDTH - MARGIN_RIGHT, self.cursor_y + 12)

    def add_paragraphs(self, paragraphs: Iterable[str], line_height: int = 15) -> None:
        for paragraph in paragraphs:
            self._add_wrapped_text(paragraph, line_height)
            self.cursor_y -= 6

    def add_bullets(self, points: Sequence[str]) -> None:
        for point in points:
            wrapped = textwrap.wrap(point, width=90)
            for idx, line in enumerate(wrapped):
                self._ensure_space(16)
                prefix = "- " if idx == 0 else "  "
                self.builder.text(MARGIN_LEFT, self.cursor_y, prefix + line)
                self.cursor_y -= 14
            self.cursor_y -= 2

    def _add_wrapped_text(self, text: str, line_height: int) -> None:
        wrapped = textwrap.wrap(text, width=95)
        for line in wrapped:
            self._ensure_space(line_height)
            self.builder.text(MARGIN_LEFT, self.cursor_y, line)
            self.cursor_y -= line_height

    def add_table(self, headers: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
        row_height = 20
        col_widths = [220, 110, 150]
        table_width = sum(col_widths)
        self._ensure_space((len(rows) + 1) * row_height + 20)
        y = self.cursor_y
        self.builder.fill_rect(MARGIN_LEFT, y - row_height, table_width, row_height, gray=0.85)
        x = MARGIN_LEFT
        for idx, header in enumerate(headers):
            self.builder.text(x + 4, y - 14, header, font="F2", size=11)
            self.builder.rect(x, y - row_height, col_widths[idx], row_height)
            x += col_widths[idx]
        y -= row_height
        for row in rows:
            x = MARGIN_LEFT
            for idx, cell in enumerate(row):
                self.builder.text(x + 4, y - 14, cell)
                self.builder.rect(x, y - row_height, col_widths[idx], row_height)
                x += col_widths[idx]
            y -= row_height
        self.cursor_y = y - 12

    def add_chart(self) -> None:
        chart_height = 220
        chart_width = 360
        self._ensure_space(chart_height + 40)
        base_y = self.cursor_y - chart_height + 30
        base_x = MARGIN_LEFT
        max_value = max(value for _, value in CONFIDENCE_BUCKETS)
        self.builder.line(base_x, base_y, base_x, base_y + chart_height - 60)
        self.builder.line(base_x, base_y, base_x + chart_width, base_y)
        bar_width = 70
        gap = 40
        current_x = base_x + 20
        for label, value in CONFIDENCE_BUCKETS:
            height = (value / max_value) * (chart_height - 80)
            self.builder.fill_rect(current_x, base_y, bar_width, height, gray=0.7)
            self.builder.rect(current_x, base_y, bar_width, height)
            self.builder.text(current_x, base_y + height + 14, f"{value:,}".replace(",", "."), size=10)
            self.builder.text(current_x, base_y - 16, label, size=10)
            current_x += bar_width + gap
        self.cursor_y = base_y - 40
        caption = "Distribuição de confiança das previsões do ensemble"
        self.builder.text(MARGIN_LEFT, self.cursor_y, caption, font="F2", size=11)
        self.cursor_y -= 30

    def add_split_columns(self, left: Sequence[str], right: Sequence[str]) -> None:
        column_width_chars = 42
        line_height = 14

        def _lines(items: Sequence[str]) -> int:
            total = 0
            for entry in items:
                wrapped = textwrap.wrap(entry, column_width_chars) or [entry]
                total += len(wrapped) + 1
            return total

        needed = (max(_lines(left), _lines(right)) + 1) * line_height
        self._ensure_space(needed)
        left_x = MARGIN_LEFT
        right_x = PAGE_WIDTH / 2 + 10
        left_y = self.cursor_y
        right_y = self.cursor_y
        for item in left:
            for idx, line in enumerate(textwrap.wrap(item, column_width_chars)):
                self.builder.text(left_x, left_y, ("- " if idx == 0 else "  ") + line)
                left_y -= line_height
            left_y -= 4
        for item in right:
            for idx, line in enumerate(textwrap.wrap(item, column_width_chars)):
                self.builder.text(right_x, right_y, ("- " if idx == 0 else "  ") + line)
                right_y -= line_height
            right_y -= 4
        self.cursor_y = min(left_y, right_y) - 10


def build_report() -> PDFBuilder:
    builder = PDFBuilder(pages=[])
    layout = ReportLayout(builder)

    layout.add_heading("Relatório de Precisão do Motor de Recomendações")
    layout.add_paragraphs([
        "Destinatários: Conselho de Administração",
        "Data: 17/11/2025",
        "Objetivo: Avaliar a precisão e a governança do motor de recomendações para modos SoloQ e Pro.",
    ])

    layout.add_heading("1. Resumo Executivo")
    layout.add_bullets(SUMMARY_POINTS)

    layout.add_heading("2. Diagnóstico Técnico Atual")
    layout.add_bullets(TECH_CONTEXT)

    layout.add_heading("3. Indicadores Quantitativos")
    layout.add_table(["Indicador", "Valor", "Fonte"], QUANT_TABLE)
    layout.add_chart()

    layout.add_heading("4. Impacto Diferenciado: SoloQ vs Pro")
    layout.add_split_columns(SOLOQ_IMPACT, PRO_IMPACT)

    layout.add_heading("5. Governança e Observabilidade")
    layout.add_paragraphs([
        "O painel de saúde consolidado expõe status dos modelos carregados, backlog de telemetria e recência da calibração. A integração do endpoint /simulations/summary permite que auditorias confirmem se o lote de 1.000.000 de simulações está disponível antes de sessões oficiais.",
        "Os logs de telemetria gravados em data/telemetry/prediction_log.jsonl alimentam relatórios de calibração e compõem trilha de auditoria para investigações futuras.",
    ])

    layout.add_heading("6. Riscos e Limitações Atuais")
    layout.add_bullets(RISK_POINTS)

    layout.add_heading("7. Próximas Ações Recomendadas")
    layout.add_bullets(NEXT_STEPS)

    layout.add_heading("Conclusão")
    layout.add_paragraphs([
        "A lógica de recomendações apresenta ganho comprovado de precisão e auditabilidade ao unir dados reais, simulações em larga escala e mecanismos de governança. A expansão da coleta e o fortalecimento da telemetria garantirão que SoloQ e Pro mantenham vantagem competitiva sustentável.",
    ])

    builder.finish_page()
    return builder


def _encode_page(content: str) -> bytes:
    return content.encode("latin-1", errors="replace")


def generate_pdf() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    builder = build_report()
    total_pages = len(builder.pages)
    page_obj_numbers = [5 + i * 2 for i in range(total_pages)]
    content_obj_numbers = [6 + i * 2 for i in range(total_pages)]

    objects: List[bytes] = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")

    kids_refs = " ".join(f"{num} 0 R" for num in page_obj_numbers)
    objects.append(f"2 0 obj << /Type /Pages /Count {total_pages} /Kids [ {kids_refs} ] >> endobj\n".encode("ascii"))

    objects.append(b"3 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")
    objects.append(b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >> endobj\n")

    for idx, content in enumerate(builder.pages):
        page_number = idx + 1
        page_obj_num = page_obj_numbers[idx]
        content_obj_num = content_obj_numbers[idx]
        page_obj = (
            f"{page_obj_num} 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Contents {content_obj_num} 0 R /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> >> endobj\n"
        ).encode("ascii")
        objects.append(page_obj)

        encoded = _encode_page(content)
        stream = f"{content_obj_num} 0 obj << /Length {len(encoded)} >> stream\n".encode("ascii")
        stream += encoded + b"\nendstream\nendobj\n"
        objects.append(stream)

    with OUTPUT_PATH.open("wb") as pdf:
        pdf.write(b"%PDF-1.4\n")
        pdf.write(b"%\xff\xff\xff\xff\n")
        offsets = [0]
        for obj in objects:
            offsets.append(pdf.tell())
            pdf.write(obj)
        xref_pos = pdf.tell()
        pdf.write(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        pdf.write(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf.write(f"{offset:010d} 00000 n \n".encode("ascii"))
        trailer = "trailer << /Size {size} /Root 1 0 R >>\n".format(size=len(objects) + 1)
        pdf.write(trailer.encode("ascii"))
        pdf.write(b"startxref\n")
        pdf.write(f"{xref_pos}\n".encode("ascii"))
        pdf.write(b"%%EOF")


if __name__ == "__main__":
    generate_pdf()
    print(f"PDF gerado em {OUTPUT_PATH}")
