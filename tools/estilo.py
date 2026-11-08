# SPDX-License-Identifier: CC-BY-SA-4.0
# Copyright (c) 2026 Rafael Beraldo
"""Aparência dos gráficos em Python, igual à dos slides: a paleta lida de
engine/cerj-cores.sty, a fonte Fira Sans do TeX Live, números no formato
brasileiro e a figura do tamanho exato da área útil do slide.
"""
import re
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt
from matplotlib import font_manager

RAIZ = Path(__file__).resolve().parent.parent
PALETA = RAIZ / "engine" / "cerj-cores.sty"

# Área útil de um slide 16:9 abaixo do título (medida com \textwidth e
# \textheight): uma figura deste tamanho entra com \figura{...} sem escala.
LARGURA_SLIDE_CM, ALTURA_SLIDE_CM = 14.0, 6.5


def paleta():
    """Cores do tema, {nome: '#RRGGBB'}, lidas das linhas \\definecolor da paleta."""
    texto = PALETA.read_text()
    cores = {nome: f"#{hexa}" for nome, hexa in
             re.findall(r"\\definecolor\{(\w+)\}\{HTML\}\{([0-9A-Fa-f]{6})\}", texto)}
    if not cores:
        raise RuntimeError(f"Nenhuma cor encontrada em {PALETA}")
    return cores


C = paleta()
NAVY, NAVY60, NAVY20, BLUE = C["cerjNavy"], C["cerjNavy60"], C["cerjNavy20"], C["cerjBlue"]
GREEN, GREEN_DARK, RED = C["cerjGreen"], C["cerjGreenDark"], C["cerjRed"]
INK, MUTED, PAPER = C["cerjInk"], C["cerjMuted"], C["cerjPaper"]


def fontes(tamanho=8):
    """Fira Sans (a do metropolis, no TeX Live) e as cores do tema no matplotlib."""
    for nome in ("FiraSans-Light.otf", "FiraSans-Regular.otf"):
        caminho = subprocess.run(["kpsewhich", nome], capture_output=True, text=True).stdout.strip()
        if caminho:
            font_manager.fontManager.addfont(caminho)
    plt.rcParams.update({
        "font.family": "Fira Sans", "font.weight": 300, "font.size": tamanho,
        "axes.edgecolor": NAVY60, "axes.labelcolor": INK, "text.color": INK,
        "xtick.color": NAVY60, "ytick.color": NAVY60, "axes.linewidth": 0.5,
        "pdf.fonttype": 42})


def figura_slide():
    """Figura do tamanho da área útil do slide, com o fundo dos slides."""
    fig = plt.figure(figsize=(LARGURA_SLIDE_CM / 2.54, ALTURA_SLIDE_CM / 2.54))
    fig.patch.set_facecolor(PAPER)
    return fig


def eixo_perfil(ax, tamanho=6.5):
    """Acabamento comum dos perfis altimétricos: sem molduras de cima e da direita."""
    ax.tick_params(labelsize=tamanho, length=2, width=0.4, pad=1)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.set_facecolor(PAPER)


def br(x, casas=0):
    """Número no formato brasileiro: 1.234,5."""
    return f"{x:,.{casas}f}".replace(",", " ").replace(".", ",").replace(" ", ".")
