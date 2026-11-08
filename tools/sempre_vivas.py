# SPDX-License-Identifier: CC-BY-SA-4.0
# Copyright (c) 2026 Rafael Beraldo
"""Gera img/sempre-vivas-alcance.pdf: por que o rádio quase não alcança nada
no Parque Nacional das Sempre-Vivas (MG).

Mosaico em três painéis:
  1. a foto (img/PN-Sempre-Vivas.jpg);
  2. mapa de relevo com o que um rádio de mão enxerga a partir do ponto da foto
     (verde, com um recorte ampliado) e o alcance das três repetidoras mais
     próximas (azul);
  3. perfil altimétrico da foto até a repetidora mais próxima, com a linha de
     visada e os trechos em que o terreno a corta.

    python3 tools/sempre_vivas.py

Premissas: rádio de mão a 1,5 m do chão; antena da repetidora a 20 m do chão.
O RepeaterBook dá a coordenada da cidade, não a do morro onde a repetidora fica,
então a antena vai para o ponto mais alto num raio de 10 km dela (melhor caso
para o rádio). Relevo a 90 m. O resto das premissas está em relevo.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, ListedColormap
from PIL import Image

from estilo import (RAIZ, NAVY, NAVY60, BLUE, GREEN, GREEN_DARK, RED, INK, PAPER,
                    fontes, figura_slide, eixo_perfil, br)
from relevo import (janela, projecao, baixar_relevo, passo_km, distancia_km, indice,
                    ponto_mais_alto, perfil, visada, area_de_visada)

FOTO = RAIZ / "img" / "PN-Sempre-Vivas.jpg"
SAIDA = RAIZ / "img" / "sempre-vivas-alcance.pdf"

# Ponto da foto (EXIF: 17°55'42.37" S, 43°50'47.01" O)
LAT0, LON0 = -17.928437, -43.846393
RAIO_KM = 150            # raio do relevo (alcança as 3 repetidoras)
MAPA_KM = 90             # meia largura do mapa
RECORTE_KM = 12          # meia largura do recorte ampliado em volta da foto
ALTURA_RADIO = 1.5       # rádio de mão, m acima do chão
ALTURA_REPETIDORA = 20   # antena da repetidora, m acima do chão (suposta)
RAIO_SITIO_KM = 10       # procura o ponto mais alto até esta distância da cidade

# As três repetidoras de 2 m mais próximas, escolhidas no mapa do RepeaterBook
# (consultado em 8/11/2026). Só indicativo, frequência e coordenada.
REPETIDORAS = [
    # Listada em Santo Antônio do Itambé; supomos que fique no Pico do Itambé (2.062 m),
    # que é o ponto mais alto perto da cidade e o melhor cenário para o rádio.
    {"indicativo": "PY4RDM", "cidade": "Pico do Itambé", "saida_mhz": 146.910,
     "lat": -18.4557, "lon": -43.3005,
     "fonte": "https://www.repeaterbook.com/row_repeaters/details.php?state_id=BR&ID=1419"},
    {"indicativo": "PY4MCL", "cidade": "Montes Claros", "saida_mhz": 146.630,
     "lat": -16.723420, "lon": -43.865265,
     "fonte": "https://www.repeaterbook.com/row_repeaters/details.php?state_id=BR&ID=15010"},
    {"indicativo": "PY4PIR", "cidade": "Pirapora", "saida_mhz": 145.210,
     "lat": -17.348869, "lon": -44.946809,
     "fonte": "https://www.repeaterbook.com/row_repeaters/details.php?state_id=BR&ID=13208"},
]
LUGARES = [("Diamantina", -18.2494, -43.6008)]


def desenhar():
    fontes(8)
    z, lats, lons = baixar_relevo(f"sempre-vivas-dem-{RAIO_KM}km",
                                  *janela(LAT0, LON0, RAIO_KM + 10), resolucao=1 / 1200)
    km = projecao(LAT0, LON0)
    celula_km = passo_km(lats)
    alcance = RAIO_KM * 1.45          # raios longos o bastante para cobrir o quadrado

    # Áreas de visada: da foto (rádio de mão) e de cada repetidora
    foto = area_de_visada(z, lats, lons, LAT0, LON0, ALTURA_RADIO, ALTURA_RADIO, alcance)
    cobertura = np.zeros(z.shape, dtype=bool)
    for rep in REPETIDORAS:
        rep["lat"], rep["lon"] = ponto_mais_alto(z, lats, lons, rep["lat"], rep["lon"],
                                                 RAIO_SITIO_KM)
        rep["cobertura"] = area_de_visada(z, lats, lons, rep["lat"], rep["lon"],
                                          ALTURA_REPETIDORA, ALTURA_RADIO, alcance)
        cobertura |= rep["cobertura"]
        rep["distancia_km"] = distancia_km(LAT0, LON0, rep["lat"], rep["lon"])
        dd, ee = perfil(z, lats, lons, (LAT0, LON0), (rep["lat"], rep["lon"]), passo_m=90)
        rep["visada"] = visada(dd, ee, ALTURA_RADIO, ALTURA_REPETIDORA)[0]
    REPETIDORAS.sort(key=lambda r: r["distancia_km"])
    io, jo = indice(lats, lons, np.array([LAT0]), np.array([LON0]))
    foto_coberta = bool(cobertura[io[0], jo[0]])
    area_foto = foto.sum() * celula_km ** 2

    alvo = REPETIDORAS[0]
    d, elev = perfil(z, lats, lons, (LAT0, LON0), (alvo["lat"], alvo["lon"]), passo_m=90)
    ok, linha, terreno = visada(d, elev, ALTURA_RADIO, ALTURA_REPETIDORA)

    fig = figura_slide()
    g = fig.add_gridspec(2, 3, width_ratios=[4.6, 3.9, 4.4], height_ratios=[3.9, 2.0],
                         left=0.075, right=0.99, top=0.99, bottom=0.12, wspace=0.07, hspace=0.3)

    # 1. Foto
    ax = fig.add_subplot(g[0, 0])
    img = Image.open(FOTO)
    img.thumbnail((1400, 1400))
    ax.imshow(img)
    ax.set_axis_off()

    # 2. Mapa: camadas desenhadas por camadas_mapa(), também usada no recorte
    x0, y0 = km(lats[-1], lons[0])
    x1, y1 = km(lats[0], lons[-1])
    ext = (x0, x1, y0, y1)
    passo_m = celula_km * 1000
    sombra = LightSource(azdeg=315, altdeg=40).hillshade(z, vert_exag=3, dx=passo_m, dy=passo_m)

    def camadas_mapa(ax):
        ax.imshow(sombra, cmap="gray", extent=ext, origin="upper", vmin=-0.6, vmax=1.3,
                  interpolation="bilinear")
        ax.imshow(np.where(cobertura, 1, np.nan), cmap=ListedColormap([BLUE]),
                  alpha=0.7, extent=ext, origin="upper", interpolation="nearest")
        ax.imshow(np.where(foto, 1, np.nan), cmap=ListedColormap([GREEN]),
                  extent=ext, origin="upper", interpolation="nearest")
        ax.set_xticks([])
        ax.set_yticks([])

    ax = fig.add_subplot(g[0, 1])
    camadas_mapa(ax)
    ax.add_patch(plt.Circle((0, 0), 50, fill=False, lw=0.4, ls=(0, (3, 2)), color=NAVY))
    ax.text(50 * 0.71 + 2, 50 * 0.71 + 2, "50 km", fontsize=6, color=NAVY)
    for nome, lat, lon in LUGARES:
        x, y = km(lat, lon)
        ax.plot(x, y, "s", ms=2, color=INK)
        ax.text(x, y - 4, nome, fontsize=6, va="top", ha="center")
    for rep in REPETIDORAS:
        x, y = km(rep["lat"], rep["lon"])
        if max(abs(x), abs(y)) <= MAPA_KM:
            ax.plot(x, y, "^", ms=3.5, color=NAVY, mec=PAPER, mew=0.4)
            ax.text(x, y - 5, rep["indicativo"], fontsize=6, color=NAVY, ha="center", va="top")
        else:
            # Fora do mapa: seta na borda, apontando para a repetidora
            f = (MAPA_KM - 6) / max(abs(x), abs(y))
            ax.annotate("", xy=(x * f, y * f), xytext=(x * f * 0.86, y * f * 0.86),
                        arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=0.6,
                                        mutation_scale=5))
            ax.text(x * f * 0.68, y * f * 0.68,
                    f"{rep['indicativo']}\n{br(rep['distancia_km'])} km", fontsize=5.5,
                    color=NAVY, ha="center", va="center", linespacing=0.9)
    xa, ya = km(alvo["lat"], alvo["lon"])
    ax.plot([0, xa], [0, ya], lw=0.6, color=RED)
    ax.plot(0, 0, "o", ms=3, color=RED, mec=PAPER, mew=0.5)
    ax.set_xlim(-MAPA_KM, MAPA_KM)
    ax.set_ylim(-MAPA_KM, MAPA_KM)

    # Recorte ampliado em volta da foto, onde a área de alcance aparece
    ins = ax.inset_axes([0.015, 0.015, 0.38, 0.38])
    camadas_mapa(ins)
    ins.plot(0, 0, "o", ms=2.5, color=RED, mec=PAPER, mew=0.4)
    ins.set_xlim(-RECORTE_KM, RECORTE_KM)
    ins.set_ylim(-RECORTE_KM, RECORTE_KM)
    for lado in ins.spines.values():
        lado.set_edgecolor(INK)
        lado.set_linewidth(0.6)
    ins.text(0.04, 0.96, f"{2 * RECORTE_KM} km", fontsize=5.5, color=INK, va="top",
             transform=ins.transAxes)
    ax.add_patch(plt.Rectangle((-RECORTE_KM, -RECORTE_KM), 2 * RECORTE_KM, 2 * RECORTE_KM,
                               fill=False, lw=0.5, color=INK))

    # Números e legenda ao lado do mapa
    ax = fig.add_subplot(g[0, 2])
    ax.set_axis_off()
    n_vis = sum(r["visada"] for r in REPETIDORAS)
    distancias = ", ".join(br(r["distancia_km"]) for r in REPETIDORAS)
    linhas = [
        ("Ao alcance do HT", f"{br(area_foto)} km² em volta"),
        ("Repetidoras mais próximas", f"{distancias} km"),
        ("Alguma alcança a foto?*", "nenhuma" if n_vis == 0 else f"{n_vis} de {len(REPETIDORAS)}"),
    ]
    y = 0.99
    for titulo, valor in linhas:
        ax.text(0, y, titulo, fontsize=6.5, color=NAVY60, va="top", transform=ax.transAxes)
        ax.text(0, y - 0.075, valor, fontsize=8, weight="regular", va="top",
                transform=ax.transAxes)
        y -= 0.22
    for k, (cor, alfa, texto) in enumerate([
            (GREEN, 1, "alcance do HT"),
            (BLUE, 0.7, "alcance das repetidoras*")]):
        yy = 0.27 - k * 0.15
        ax.add_patch(plt.Rectangle((0, yy), 0.06, 0.06, color=cor, alpha=alfa,
                                   transform=ax.transAxes))
        ax.text(0.09, yy + 0.03, texto, fontsize=6.5, va="center", transform=ax.transAxes,
                linespacing=0.95)
    ax.text(0, -0.03, f"* antena a {ALTURA_REPETIDORA} m no ponto mais alto\na até "
            f"{RAIO_SITIO_KM} km da cidade (melhor caso)", fontsize=5.5, color=NAVY60,
            va="bottom", transform=ax.transAxes)

    # 3. Perfil até a repetidora mais próxima
    ax = fig.add_subplot(g[1, :])
    dk = d / 1000
    base = terreno.min() - 50
    ax.fill_between(dk, base, terreno, color=GREEN, alpha=0.35, lw=0)
    ax.plot(dk, terreno, lw=0.6, color=GREEN_DARK)
    ax.plot(dk, linha, lw=0.8, color=GREEN_DARK if ok else RED, ls="-" if ok else (0, (4, 2)))
    if not ok:
        ax.fill_between(dk, linha, terreno, where=linha < terreno, color=RED, alpha=0.3, lw=0)
        excesso = terreno - linha
        k = int(np.argmax(excesso[1:-1])) + 1
        ax.annotate(f"este morro, a {br(dk[k], 1)} km, fica {br(excesso[k])} m\n"
                    "acima da linha e corta o sinal",
                    xy=(dk[k], terreno[k]), xytext=(dk[k] + 4, terreno[k] + 170),
                    fontsize=6.5, color=RED, va="bottom",
                    arrowprops=dict(arrowstyle="-", color=RED, lw=0.5))
    ax.plot(0, linha[0], "o", ms=3, color=RED)
    ax.plot(dk[-1], linha[-1], "^", ms=3.5, color=NAVY)
    ax.text(0.5, linha[0] + 15, "foto", fontsize=6.5, va="bottom")
    ax.text(dk[-1], linha[-1] + 15, f"{alvo['indicativo']} ({alvo['cidade']}) ",
            fontsize=6.5, va="bottom", ha="right")
    ax.set_xlim(0, dk[-1])
    ax.set_ylim(base, max(terreno.max(), linha.max()) + 120)
    ax.set_xlabel("distância (km)", fontsize=7, labelpad=1)
    ax.set_ylabel("altitude (m)", fontsize=7, labelpad=1)
    eixo_perfil(ax)

    fig.savefig(SAIDA, facecolor=PAPER)
    print(f"{SAIDA.relative_to(RAIZ)} gerado")
    print(f"  visada da foto: {area_foto:.0f} km²; foto coberta por alguma repetidora: {foto_coberta}")
    for r in REPETIDORAS:
        print(f"  {r['indicativo']}: {r['distancia_km']:.1f} km, visada até a foto: {r['visada']}, "
              f"cobertura {r['cobertura'].sum() * celula_km ** 2:.0f} km²")


if __name__ == "__main__":
    desenhar()
