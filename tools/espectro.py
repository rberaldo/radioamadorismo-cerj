# SPDX-License-Identifier: CC-BY-SA-4.0
# Copyright (c) 2026 Rafael Beraldo
"""Gera img/espectro-brasil.pdf: o espectro brasileiro inteiro, de 3 kHz a
300 GHz, com as faixas do radioamador em destaque.

A figura é um documento TikZ à parte (figuras/espectro-brasil.tex, classe
standalone) compilado com LuaLaTeX. A apresentação só inclui o PDF pronto,
sem recompilar o desenho:  \figura{espectro-brasil}
(o latexmkrc também recompila o PDF sempre que o .tex muda).

Os dados vêm do PDFF da Anatel (coluna Brasil), salvos em dados/pdff-brasil.json.

    python3 tools/espectro.py            gera a figura a partir do JSON salvo
    python3 tools/espectro.py --baixar   baixa o PDFF atual da Anatel antes
    python3 tools/espectro.py --sem-pdf  só escreve o .tex, sem compilar

Cada linha da figura é uma faixa da UIT (VLF … EHF), em escala logarítmica.
"""
import json
import os
import shutil
import subprocess
import tempfile
import math
import sys
import urllib.parse
import urllib.request
from datetime import date
from http.cookiejar import CookieJar
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados" / "pdff-brasil.json"
SAIDA = RAIZ / "figuras" / "espectro-brasil.tex"
PDF = RAIZ / "img" / "espectro-brasil.pdf"

# --- Geometria (cm) ----------------------------------------------------------
LARGURA = 11.4     # largura de cada barra (uma década)
ALTURA = 0.30      # altura da barra
PASSO = 0.70       # distância vertical entre linhas
MIN_LARG = 0.025   # largura mínima de uma faixa de radioamador, para aparecer

# Faixas da UIT: (nome, início em kHz, rótulo do intervalo)
LINHAS = [
    ("VLF", 3, "3–30 kHz"),
    ("LF", 30, "30–300 kHz"),
    ("MF", 300, "300 kHz–3 MHz"),
    ("HF", 3_000, "3–30 MHz"),
    ("VHF", 30_000, "30–300 MHz"),
    ("UHF", 300_000, "300 MHz–3 GHz"),
    ("SHF", 3_000_000, "3–30 GHz"),
    ("EHF", 30_000_000, "30–300 GHz"),
]

# Nome de cada faixa de radioamador (pelo início, em kHz)
NOMES = {
    135.7: "2200 m", 472: "630 m", 1800: "160 m", 3500: "80 m",
    5351.5: "60 m", 7000: "40 m", 10100: "30 m", 14000: "20 m",
    18068: "17 m", 21000: "15 m", 24890: "12 m", 28000: "10 m",
    50000: "6 m", 144000: "2 m", 220000: "1,25 m", 430000: "70 cm",
    902000: "33 cm", 1240000: "23 cm", 2300000: "13 cm", 3300000: "9 cm",
    5650000: "5 cm", 10000000: "3 cm", 24000000: "1,2 cm",
    47000000: "6 mm", 76000000: "4 mm", 122250000: "2,5 mm",
    134000000: "2 mm", 241000000: "1 mm",
}
# Faixas que o montanhista usa: rótulo em negrito
DESTAQUE = {"2 m", "70 cm"}
# Deslocamento horizontal (cm) de rótulos que se encostariam
AJUSTE = {"2,5 mm": -0.22, "2 mm": 0.12}

# Radiodifusão para referência, rotulada dentro da barra: (início, fim, rótulo)
REFERENCIAS = [(535, 1705, "rádio AM"), (54_000, 88_000, "TV"),
               (88_000, 108_000, "FM"), (174_000, 216_000, "TV"),
               (470_000, 698_000, "TV")]


def baixar():
    """Baixa a coluna Brasil do PDFF vigente pelo ePDFF da Anatel."""
    url = "https://sistemas.anatel.gov.br/se/modulos/plano"
    abridor = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(CookieJar()))
    pagina = abridor.open(f"{url}/consulta", timeout=60).read().decode()
    edicao = pagina.split("<h2>", 1)[1].split("</h2>", 1)[0].strip()
    faixas = {}
    for num in (1, 2, 3, 4):
        corpo = urllib.parse.urlencode({
            "ID_PLANO_PDFF": 21, "limit": 500, "page": num,
            "consultaExterna": 1}).encode()
        req = urllib.request.Request(
            f"{url}/faixafrequencia/dados", data=corpo,
            headers={"X-Requested-With": "XMLHttpRequest"})
        resp = json.load(abridor.open(req, timeout=300))
        for grupo in resp["plano"].values():
            for c in grupo["brasil"]:
                faixas[(c["VR_FREQUENCIA_INICIAL_KHZ"],
                        c["VR_FREQUENCIA_FINAL_KHZ"])] = [
                    {"nome": s["NO_SERVICO"].strip(),
                     "primario": s["IC_PRIMARIO"] == "1"}
                    for s in c["SERVICOS"]]
        pag = resp["paginacao"]
        if pag["page"] * pag["limit"] >= pag["total"]:
            break
    dados = {
        "meta": {
            "fonte": "Anatel — Plano de Atribuição, Destinação e Distribuição "
                     f"de Faixas de Frequências no Brasil (PDFF), {edicao}; "
                     "coluna Brasil",
            "obtido_em": date.today().isoformat(),
            "url": f"{url}/consulta"},
        "faixas": [{"ini_khz": a, "fim_khz": b, "servicos": s}
                   for (a, b), s in sorted(faixas.items())]}
    DADOS.write_text(json.dumps(dados, ensure_ascii=False, indent=0))
    print(f"{len(faixas)} faixas salvas em {DADOS.relative_to(RAIZ)}")


def categoria(servicos):
    # Primários vêm em MAIÚSCULAS no PDFF; secundários, em "Caixa Mista"
    amador = [s for s in servicos
              if s["nome"].upper().startswith("RADIOAMADOR")]
    if any(s["primario"] for s in amador):
        return "amP"
    if amador:
        return "amS"
    primarios = [s["nome"] for s in servicos if s["primario"]]
    if primarios == ["RADIODIFUSÃO"]:
        return "rd"
    return "outro"


def x(f, ini):
    return LARGURA * math.log10(f / ini)


def gerar():
    dados = json.loads(DADOS.read_text())
    faixas = [(f["ini_khz"], f["fim_khz"], categoria(f["servicos"]))
              for f in dados["faixas"]]

    # Junta faixas de radioamador contíguas num só "bloco" com nome
    blocos = []
    for a, b, cat in faixas:
        if cat in ("amP", "amS"):
            if blocos and blocos[-1][1] == a:
                blocos[-1][1] = b
            else:
                blocos.append([a, b])
    for bl in blocos:
        if bl[0] not in NOMES:
            sys.exit(f"Faixa de radioamador sem nome: {bl[0]} kHz. "
                     "Acrescente-a em NOMES.")

    out = []
    p = out.append
    meta = dados["meta"]
    p("% !TEX program = lualatex")
    p(f"% Gerado por tools/espectro.py. Não edite à mão.\n"
      f"% Fonte: {meta['fonte']}\n% Obtido em {meta['obtido_em']}: "
      f"{meta['url']}")
    # Mesma fonte (Fira Sans, do metropolis), tamanhos (11pt) e cores do tema:
    # incluído sem escala, o PDF fica idêntico a um desenho feito no slide.
    p(r"\documentclass[11pt, border=2pt]{standalone}")
    p(r"% Acha engine/ compilando da raiz ou de dentro de figuras/")
    p(r"\makeatletter\def\input@path{{engine/}{../engine/}}\makeatother")
    p(r"\usepackage{cerj-figuras}")
    p(r"\begin{document}")
    p(r"\begin{tikzpicture}[x=1cm, y=1cm, font=\sffamily]")
    p(r"  \tikzset{amP/.style={fill=cerjGreenDark},"
      r" amS/.style={fill=cerjGreen!55!cerjPaper},"
      r" rd/.style={fill=cerjBlue!35!cerjPaper},"
      r" outro/.style={fill=cerjAzul10},"
      r" rot/.style={font=\sffamily\tiny, inner sep=1pt},"
      r" ham/.style={rot, text=cerjGreenDark, anchor=south}}")
    for i, (nome, ini, intervalo) in enumerate(LINHAS):
        fim = ini * 10
        y = -i * PASSO
        p(f"  % --- {nome} ---")
        p(f"  \\node[anchor=east, font=\\sffamily\\scriptsize\\bfseries,"
          f" text=cerjNavy, inner sep=0pt] at (-0.15,{y + 0.22:.3f})"
          f" {{{nome}}};")
        p(f"  \\node[anchor=east, rot, text=cerjInk!70!cerjPaper,"
          f" inner sep=0pt] at (-0.15,{y + 0.02:.3f}) {{{intervalo}}};")
        # Fundo cinza e radiodifusão
        for a, b, cat in faixas:
            a2, b2 = max(a, ini), min(b, fim)
            if a2 >= b2 or cat in ("amP", "amS"):
                continue
            p(f"  \\fill[{cat}] ({x(a2, ini):.4f},{y:.3f}) rectangle"
              f" ({x(b2, ini):.4f},{y + ALTURA:.3f});")
        # Divisões entre faixas (linhas finas brancas)
        divisoes = sorted({a for a, _, _ in faixas if ini < a < fim})
        if divisoes:
            p("  \\foreach \\d in {" + ",".join(
                f"{x(a, ini):.4f}" for a in divisoes) + "}")
            p(f"    \\draw[cerjPaper, line width=0.15pt] (\\d,{y:.3f})"
              f" -- (\\d,{y + ALTURA:.3f});")
        # Radioamador por cima, com largura mínima para aparecer
        for a, b, cat in faixas:
            a2, b2 = max(a, ini), min(b, fim)
            if a2 >= b2 or cat not in ("amP", "amS"):
                continue
            xa, xb = x(a2, ini), x(b2, ini)
            if xb - xa < MIN_LARG:
                meio = (xa + xb) / 2
                xa, xb = meio - MIN_LARG / 2, meio + MIN_LARG / 2
            p(f"  \\fill[{cat}] ({xa:.4f},{y:.3f}) rectangle"
              f" ({xb:.4f},{y + ALTURA:.3f});")
        # Nomes das faixas de radioamador, acima da barra
        for a, b in blocos:
            a2, b2 = max(a, ini), min(b, fim)
            if a2 >= b2 or a < ini:
                continue
            nome_fx = NOMES[a]
            texto = (f"\\textbf{{{nome_fx}}}" if nome_fx in DESTAQUE
                     else nome_fx)
            meio = (x(a2, ini) + x(b2, ini)) / 2 + AJUSTE.get(nome_fx, 0)
            p(f"  \\node[ham] at ({meio:.4f},{y + ALTURA:.3f}) {{{texto}}};")
        # Referências de radiodifusão, dentro da barra
        for a, b, rotulo in REFERENCIAS:
            if ini <= a and b <= fim:
                meio = (x(a, ini) + x(b, ini)) / 2
                p(f"  \\node[rot, text=cerjNavy] at ({meio:.4f},"
                  f"{y + ALTURA / 2:.3f}) {{{rotulo}}};")
        # Contorno da barra
        p(f"  \\draw[cerjAzul40, line width=0.3pt] (0,{y:.3f})"
          f" rectangle ({LARGURA},{y + ALTURA:.3f});")

    # Legenda
    y = -len(LINHAS) * PASSO + 0.28
    itens = [("amP", "radioamador (primário)"),
             ("amS", "radioamador (secundário)"),
             ("rd", "radiodifusão (rádio e TV)"),
             ("outro", "outros serviços")]
    xl = 0.0
    larguras = [2.95, 3.15, 3.2, 2.0]
    for (cat, texto), w in zip(itens, larguras):
        p(f"  \\fill[{cat}] ({xl:.2f},{y:.3f}) rectangle"
          f" ({xl + 0.3:.2f},{y + 0.18:.3f});")
        p(f"  \\node[rot, anchor=west, text=cerjInk] at ({xl + 0.35:.2f},"
          f"{y + 0.09:.3f}) {{{texto}}};")
        xl += w
    p(f"  \\node[rot, anchor=north east, text=cerjInk!60!cerjPaper] at"
      f" ({LARGURA},{y - 0.08:.3f}) {{Fonte: Anatel, PDFF (Res.\\ 789/2026),"
      f" coluna Brasil. Escala logarítmica em cada linha.}};")
    p(r"\end{tikzpicture}")
    p(r"\end{document}")
    p("")
    p("%%% Local Variables:")
    p("%%% TeX-engine: luatex")
    p("%%% End:")
    SAIDA.write_text("\n".join(out) + "\n")
    print(f"{SAIDA.relative_to(RAIZ)}: {len(blocos)} faixas de radioamador")


def compilar():
    """Compila o .tex numa pasta temporária e copia só o PDF para img/."""
    pdf = PDF
    env = dict(os.environ, TEXINPUTS=f"{RAIZ / 'engine'}//:")
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run(
            ["lualatex", "-interaction=nonstopmode", "-halt-on-error",
             f"-output-directory={tmp}", str(SAIDA)],
            cwd=RAIZ, env=env, capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(r.stdout[-2000:] + "\nFalha ao compilar " + str(SAIDA))
        shutil.copy(Path(tmp) / SAIDA.with_suffix(".pdf").name, pdf)
    print(f"{pdf.relative_to(RAIZ)} compilado")


if __name__ == "__main__":
    if "--baixar" in sys.argv:
        baixar()
    gerar()
    if "--sem-pdf" not in sys.argv:
        compilar()
