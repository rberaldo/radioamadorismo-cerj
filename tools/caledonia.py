# SPDX-License-Identifier: CC-BY-SA-4.0
# Copyright (c) 2026 Rafael Beraldo
"""Gera img/caledonia-alcance.pdf: a repetidora PY1MAC, suposta no alto do Pico
da Caledônia (Nova Friburgo), tem linha de visada até o alto do Morro do Gato
(Parque Estadual dos Três Picos) e até a Praça XV, no Rio?

Mapa de relevo com as duas linhas e, ao lado, os dois perfis altimétricos.

    python3 tools/caledonia.py

Premissas: antena da repetidora a 15 m do chão, no cume da Caledônia (o
RepeaterBook só dá a cidade); rádio de mão a 1,5 m do chão nos destinos.
Coordenadas dos picos: OpenStreetMap. O resto das premissas está em relevo.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from matplotlib.colors import LightSource, ListedColormap

from estilo import (RAIZ, NAVY, NAVY20, GREEN, GREEN_DARK, RED, INK, PAPER,
                    fontes, figura_slide, eixo_perfil, br)
from relevo import projecao, baixar_relevo, passo_km, ponto_mais_alto, perfil, visada

SAIDA = RAIZ / "img" / "caledonia-alcance.pdf"

# PY1MAC: saída 145,350 MHz, entrada 144,750 (-0,6), sem subtom (RepeaterBook)
REPETIDORA = ("PY1MAC", -22.3535326, -42.5870700)   # cume da Caledônia, OpenStreetMap
ALTURA_REPETIDORA = 15
ALTURA_RADIO = 1.5
# (nome, lat, lon, procura o cume a até tantos km; 0 = usa o ponto como está)
DESTINOS = [
    ("Morro do Gato", -22.3299181, -42.7031413, 0.3),   # cume norte, OpenStreetMap
    ("Praça XV, Rio", -22.9030, -43.1740, 0),
]
# Janela do relevo (oeste, sul, leste, norte)
JANELA = (-43.30, -22.98, -42.48, -22.22)


def desenhar():
    fontes(8)
    z, lats, lons = baixar_relevo("caledonia-dem", *JANELA)
    nome_rep, lat_r, lon_r = REPETIDORA
    lat_r, lon_r = ponto_mais_alto(z, lats, lons, lat_r, lon_r, 0.3)
    km = projecao(JANELA[1], JANELA[0])          # origem no canto sudoeste do mapa

    estudos = []
    for nome, lat, lon, raio in DESTINOS:
        if raio:
            lat, lon = ponto_mais_alto(z, lats, lons, lat, lon, raio)
        d, elev = perfil(z, lats, lons, (lat_r, lon_r), (lat, lon))
        ok, linha, terreno = visada(d, elev, ALTURA_REPETIDORA, ALTURA_RADIO)
        estudos.append((nome, lat, lon, d, ok, linha, terreno))
        print(f"{nome}: {d[-1] / 1000:.1f} km, visada: {ok}")

    fig = figura_slide()
    g = fig.add_gridspec(2, 2, width_ratios=[5.2, 8.8], left=0.01, right=0.99,
                         top=0.91, bottom=0.12, wspace=0.2, hspace=0.62)

    # Mapa
    ax = fig.add_subplot(g[:, 0])
    x1, y1 = km(JANELA[3], JANELA[2])
    passo_m = passo_km(lats) * 1000
    sombra = LightSource(azdeg=315, altdeg=40).hillshade(z, vert_exag=2, dx=passo_m, dy=passo_m)
    ax.imshow(sombra, cmap="gray", extent=(0, x1, 0, y1), origin="upper", vmin=-0.6, vmax=1.3,
              interpolation="bilinear")
    ax.imshow(np.where(z <= 0, 1.0, np.nan), cmap=ListedColormap([NAVY20]),     # mar
              extent=(0, x1, 0, y1), origin="upper", interpolation="nearest")
    xr, yr = km(lat_r, lon_r)
    for nome, lat, lon, d, ok, linha, terreno in estudos:
        x, y = km(lat, lon)
        ax.plot([xr, x], [yr, y], lw=0.9, color=GREEN_DARK if ok else RED,
                ls="-" if ok else (0, (3, 1.5)))
        ax.plot(x, y, "o", ms=3, color=INK, mec=PAPER, mew=0.4)
        dx = 1.5 if x < 0.6 * x1 else -1.5     # rótulo para dentro do mapa
        ax.text(x + dx, y - 1.5, nome, fontsize=6.5, va="top", ha="left" if dx > 0 else "right")
    ax.plot(xr, yr, "^", ms=5, color=NAVY, mec=PAPER, mew=0.5)
    ax.text(xr, yr + 2.5, nome_rep, fontsize=6.5, color=NAVY, ha="center", va="bottom",
            weight="regular")
    ax.set_xlim(0, x1)
    ax.set_ylim(0, y1)
    ax.set_xticks([])
    ax.set_yticks([])

    # Perfis
    for k, (nome, lat, lon, d, ok, linha, terreno) in enumerate(estudos):
        ax = fig.add_subplot(g[k, 1])
        dk = d / 1000
        base = min(0, terreno.min()) - 50
        ax.fill_between(dk, base, terreno, color=GREEN, alpha=0.35, lw=0)
        ax.plot(dk, terreno, lw=0.6, color=GREEN_DARK)
        ax.plot(dk, linha, lw=0.9, color=GREEN_DARK if ok else RED, ls="-" if ok else (0, (4, 2)))
        if not ok:
            ax.fill_between(dk, linha, terreno, where=linha < terreno, color=RED, alpha=0.3, lw=0)
        ax.plot(0, linha[0], "^", ms=4, color=NAVY)
        ax.plot(dk[-1], linha[-1], "o", ms=3, color=INK)
        resultado = "com visada" if ok else "sem visada"
        ax.set_title(f"{nome_rep} → {nome}: {br(dk[-1])} km, {resultado}", fontsize=7,
                     loc="left", pad=2, color=GREEN_DARK if ok else RED, weight="regular")
        ax.set_xlim(0, dk[-1])
        ax.set_ylim(base, max(terreno.max(), linha.max()) + 150)
        ax.set_ylabel("altitude (m)", fontsize=6, labelpad=1)
        eixo_perfil(ax, 6)
    ax.set_xlabel("distância da repetidora (km)", fontsize=6.5, labelpad=1)

    fig.savefig(SAIDA, facecolor=PAPER)
    print(f"{SAIDA.relative_to(RAIZ)} gerado")


if __name__ == "__main__":
    desenhar()
