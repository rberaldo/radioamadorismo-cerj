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

Relevo: Copernicus DEM GLO-30, lido da AWS com o GDAL só na janela da região e
reamostrado para 90 m; o recorte fica em cache em build/cache/.

    python3 tools/sempre_vivas.py

Premissas: rádio de mão a 1,5 m do chão; antena da repetidora a 20 m do chão.
O RepeaterBook dá a coordenada da cidade, não a do morro onde a repetidora fica,
então a antena vai para o ponto mais alto num raio de 10 km dela (melhor caso
para o rádio). Refração padrão
(raio efetivo da Terra = 4/3 do real). É um cálculo só de linha de visada: não
considera potência, difração nem reflexões, então mostra o melhor caso.
"""
import json
import math
import subprocess
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LightSource, ListedColormap
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
FOTO = RAIZ / "img" / "PN-Sempre-Vivas.jpg"
SAIDA = RAIZ / "img" / "sempre-vivas-alcance.pdf"
CACHE = RAIZ / "build" / "cache"

# Ponto da foto (EXIF: 17°55'42.37" S, 43°50'47.01" O)
LAT0, LON0 = -17.928437, -43.846393
RAIO_KM = 150            # raio das áreas de visada (alcança as 3 repetidoras)
MAPA_KM = 90             # meia largura do mapa
RECORTE_KM = 12          # meia largura do recorte ampliado em volta da foto
RESOLUCAO = 1 / 1200     # 3" de arco, ~90 m
ALTURA_RADIO = 1.5       # rádio de mão, m acima do chão
ALTURA_REPETIDORA = 20   # antena da repetidora, m acima do chão (suposta)
RAIO_SITIO_KM = 10       # procura o ponto mais alto até esta distância da cidade
K = 4 / 3                # refração padrão
R_TERRA = 6_371_000.0

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

# Paleta (engine/cerj-cores.sty)
AZUL, AZUL60, AZUL_EMBLEMA = "#003366", "#6685A3", "#3C4398"
VERDE, VERDE_ESCURO, TINTA, PAPEL = "#44AC6A", "#338150", "#001F3D", "#FAFAFA"
VERMELHO = "#B32424"

KM_LAT = 110.574
KM_LON = 111.320 * math.cos(math.radians(LAT0))


# --- Dados ---------------------------------------------------------------------

def baixar_relevo():
    """Recorta o Copernicus GLO-30 em volta do ponto, a 90 m. Devolve (z, lats, lons)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    tif = CACHE / f"sempre-vivas-dem-{RAIO_KM}km.tif"
    dlat = (RAIO_KM + 10) / KM_LAT
    dlon = (RAIO_KM + 10) / KM_LON
    oeste, leste = LON0 - dlon, LON0 + dlon
    sul, norte = LAT0 - dlat, LAT0 + dlat
    if not tif.exists():
        urls = []
        for la in range(math.floor(sul), math.floor(norte) + 1):
            for lo in range(math.floor(oeste), math.floor(leste) + 1):
                ns = f"{'S' if la < 0 else 'N'}{abs(la):02d}"
                ew = f"{'W' if lo < 0 else 'E'}{abs(lo):03d}"
                n = f"Copernicus_DSM_COG_10_{ns}_00_{ew}_00_DEM"
                urls.append(f"/vsicurl/https://copernicus-dem-30m.s3.amazonaws.com/{n}/{n}.tif")
        vrt = CACHE / "sempre-vivas-dem.vrt"
        subprocess.run(["gdalbuildvrt", "-q", str(vrt), *urls], check=True)
        subprocess.run(["gdal_translate", "-q", "-projwin", str(oeste), str(norte),
                        str(leste), str(sul), "-tr", str(RESOLUCAO), str(RESOLUCAO),
                        "-r", "average", "-co", "COMPRESS=DEFLATE", str(vrt), str(tif)],
                       check=True)
    bruto = tif.with_suffix(".f32")
    if not bruto.exists() or bruto.stat().st_mtime < tif.stat().st_mtime:
        subprocess.run(["gdal_translate", "-q", "-of", "ENVI", "-ot", "Float32",
                        str(tif), str(bruto)], check=True)
    info = json.loads(subprocess.run(["gdalinfo", "-json", str(tif)], check=True,
                                     capture_output=True, text=True).stdout)
    w, h = info["size"]
    x0, dx, _, y0, _, dy = info["geoTransform"]
    z = np.fromfile(bruto, dtype="<f4").reshape(h, w)
    z = np.where(z < -1000, np.nan, z)          # sem dados
    lons = x0 + dx * (np.arange(w) + 0.5)
    lats = y0 + dy * (np.arange(h) + 0.5)
    return z, lats, lons


# --- Geometria -----------------------------------------------------------------

def distancia_km(lat0, lon0, lat, lon):
    p1, p2 = math.radians(lat0), math.radians(lat)
    a = (math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2)
         * math.sin(math.radians(lon - lon0) / 2) ** 2)
    return 2 * R_TERRA * math.asin(math.sqrt(a)) / 1000


def indice(lats, lons, la, lo):
    i = np.clip(np.round((la - lats[0]) / (lats[1] - lats[0])).astype(int), 0, len(lats) - 1)
    j = np.clip(np.round((lo - lons[0]) / (lons[1] - lons[0])).astype(int), 0, len(lons) - 1)
    return i, j


def curvatura(d):
    """Quanto o terreno 'desce' a uma distância d (m), pela curvatura da Terra."""
    return d ** 2 / (2 * K * R_TERRA)


def perfil(z, lats, lons, lat1, lon1, passo_m=90):
    """Distâncias (m) e elevações do ponto da foto até (lat1, lon1)."""
    total = distancia_km(LAT0, LON0, lat1, lon1) * 1000
    t = np.linspace(0, 1, max(int(total / passo_m), 2))
    i, j = indice(lats, lons, LAT0 + t * (lat1 - LAT0), LON0 + t * (lon1 - LON0))
    return t * total, z[i, j]


def visada_no_perfil(d, elev, alt_inicio, alt_fim):
    """Há linha de visada entre as duas pontas do perfil? Devolve também as curvas."""
    terreno = elev - curvatura(d)
    h0, h1 = terreno[0] + alt_inicio, terreno[-1] + alt_fim
    linha = h0 + (h1 - h0) * d / d[-1]
    return bool((linha[1:-1] > terreno[1:-1]).all()), linha, terreno


def ponto_mais_alto(z, lats, lons, lat, lon, raio_km=RAIO_SITIO_KM):
    """Ponto mais alto do terreno a até raio_km de (lat, lon)."""
    di = int(raio_km / (abs(lats[1] - lats[0]) * KM_LAT))
    dj = int(raio_km / (abs(lons[1] - lons[0]) * KM_LON))
    i0, j0 = indice(lats, lons, np.array([lat]), np.array([lon]))
    i0, j0 = i0[0], j0[0]
    ii, jj = np.mgrid[-di:di + 1, -dj:dj + 1]
    dentro = (ii / di) ** 2 + (jj / dj) ** 2 <= 1
    ii, jj = np.clip(ii[dentro] + i0, 0, len(lats) - 1), np.clip(jj[dentro] + j0, 0, len(lons) - 1)
    k = np.nanargmax(z[ii, jj])
    return float(lats[ii[k]]), float(lons[jj[k]])


def area_de_visada(z, lats, lons, lat_obs, lon_obs, alt_obs, alt_alvo):
    """Células de onde um alvo a alt_alvo do chão enxerga o observador (ou vice-versa)."""
    visivel = np.zeros(z.shape, dtype=bool)
    passo = abs(lats[1] - lats[0]) * KM_LAT * 1000          # m por célula, na latitude
    n = int(RAIO_KM * 1.45 * 1000 / passo)                  # cobre o quadrado do mapa
    k = np.arange(1, n + 1)
    d = k * passo
    queda = curvatura(d)
    i0 = (lat_obs - lats[0]) / (lats[1] - lats[0])
    j0 = (lon_obs - lons[0]) / (lons[1] - lons[0])
    escala_j = KM_LAT / KM_LON * abs((lats[1] - lats[0]) / (lons[1] - lons[0]))
    io, jo = indice(lats, lons, np.array([lat_obs]), np.array([lon_obs]))
    h0 = z[io[0], jo[0]] + alt_obs
    visivel[io[0], jo[0]] = True
    for ang in np.linspace(0, 2 * math.pi, int(2 * math.pi * n * 1.1), endpoint=False):
        ii = np.round(i0 - np.sin(ang) * k).astype(int)
        jj = np.round(j0 + np.cos(ang) * k * escala_j).astype(int)
        dentro = (ii >= 0) & (ii < z.shape[0]) & (jj >= 0) & (jj < z.shape[1])
        if not dentro.any():
            continue
        ii, jj, dd, qq = ii[dentro], jj[dentro], d[dentro], queda[dentro]
        terreno = np.nan_to_num(z[ii, jj], nan=-1e4) - qq
        ang_terreno = (terreno - h0) / dd
        ang_alvo = (terreno + alt_alvo - h0) / dd
        horizonte = np.maximum.accumulate(np.concatenate([[-np.inf], ang_terreno[:-1]]))
        visivel[ii, jj] |= ang_alvo >= horizonte
    return visivel


# --- Figura --------------------------------------------------------------------

def fontes():
    for nome in ("FiraSans-Light.otf", "FiraSans-Regular.otf"):
        caminho = subprocess.run(["kpsewhich", nome], capture_output=True, text=True).stdout.strip()
        if caminho:
            font_manager.fontManager.addfont(caminho)
    plt.rcParams.update({
        "font.family": "Fira Sans", "font.weight": 300, "font.size": 8,
        "axes.edgecolor": AZUL60, "axes.labelcolor": TINTA, "text.color": TINTA,
        "xtick.color": AZUL60, "ytick.color": AZUL60, "axes.linewidth": 0.5,
        "pdf.fonttype": 42})


def km(lat, lon):
    return (lon - LON0) * KM_LON, (lat - LAT0) * KM_LAT


def br(x, casas=0):
    """Número no formato brasileiro."""
    return f"{x:,.{casas}f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def desenhar(z, lats, lons):
    fontes()
    passo_km = abs(lats[1] - lats[0]) * KM_LAT

    # Áreas de visada: da foto (rádio de mão) e de cada repetidora
    foto = area_de_visada(z, lats, lons, LAT0, LON0, ALTURA_RADIO, ALTURA_RADIO)
    cobertura = np.zeros(z.shape, dtype=bool)
    for rep in REPETIDORAS:
        rep["lat"], rep["lon"] = ponto_mais_alto(z, lats, lons, rep["lat"], rep["lon"])
        rep["cobertura"] = area_de_visada(z, lats, lons, rep["lat"], rep["lon"],
                                          ALTURA_REPETIDORA, ALTURA_RADIO)
        cobertura |= rep["cobertura"]
        rep["distancia_km"] = distancia_km(LAT0, LON0, rep["lat"], rep["lon"])
        dd, ee = perfil(z, lats, lons, rep["lat"], rep["lon"])
        rep["visada"] = visada_no_perfil(dd, ee, ALTURA_RADIO, ALTURA_REPETIDORA)[0]
    REPETIDORAS.sort(key=lambda r: r["distancia_km"])
    io, jo = indice(lats, lons, np.array([LAT0]), np.array([LON0]))
    foto_coberta = bool(cobertura[io[0], jo[0]])
    area_foto = foto.sum() * passo_km ** 2

    alvo = REPETIDORAS[0]
    d, elev = perfil(z, lats, lons, alvo["lat"], alvo["lon"])
    ok, linha, terreno = visada_no_perfil(d, elev, ALTURA_RADIO, ALTURA_REPETIDORA)

    # Tamanho exato da área do slide (14 cm × ~6,6 cm abaixo do título): entra sem escala
    fig = plt.figure(figsize=(14.0 / 2.54, 6.5 / 2.54))
    fig.patch.set_facecolor(PAPEL)
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
    passo_m = passo_km * 1000
    sombra = LightSource(azdeg=315, altdeg=40).hillshade(
        np.nan_to_num(z, nan=np.nanmean(z)), vert_exag=3, dx=passo_m, dy=passo_m)

    def camadas_mapa(ax):
        ax.imshow(sombra, cmap="gray", extent=ext, origin="upper", vmin=-0.6, vmax=1.3,
                  interpolation="bilinear")
        ax.imshow(np.where(cobertura, 1, np.nan), cmap=ListedColormap([AZUL_EMBLEMA]),
                  alpha=0.7, extent=ext, origin="upper", interpolation="nearest")
        ax.imshow(np.where(foto, 1, np.nan), cmap=ListedColormap([VERDE]),
                  extent=ext, origin="upper", interpolation="nearest")
        ax.set_xticks([])
        ax.set_yticks([])

    ax = fig.add_subplot(g[0, 1])
    camadas_mapa(ax)
    ax.add_patch(plt.Circle((0, 0), 50, fill=False, lw=0.4, ls=(0, (3, 2)), color=AZUL))
    ax.text(50 * 0.71 + 2, 50 * 0.71 + 2, "50 km", fontsize=6, color=AZUL)
    for nome, lat, lon in LUGARES:
        x, y = km(lat, lon)
        ax.plot(x, y, "s", ms=2, color=TINTA)
        ax.text(x, y - 4, nome, fontsize=6, va="top", ha="center")
    for rep in REPETIDORAS:
        x, y = km(rep["lat"], rep["lon"])
        if max(abs(x), abs(y)) <= MAPA_KM:
            ax.plot(x, y, "^", ms=3.5, color=AZUL, mec=PAPEL, mew=0.4)
            ax.text(x, y - 5, rep["indicativo"], fontsize=6, color=AZUL, ha="center", va="top")
        else:
            # Fora do mapa: seta na borda, apontando para a repetidora
            f = (MAPA_KM - 6) / max(abs(x), abs(y))
            ax.annotate("", xy=(x * f, y * f), xytext=(x * f * 0.86, y * f * 0.86),
                        arrowprops=dict(arrowstyle="-|>", color=AZUL, lw=0.6,
                                        mutation_scale=5))
            ax.text(x * f * 0.68, y * f * 0.68,
                    f"{rep['indicativo']}\n{br(rep['distancia_km'])} km", fontsize=5.5,
                    color=AZUL, ha="center", va="center", linespacing=0.9)
    xa, ya = km(alvo["lat"], alvo["lon"])
    ax.plot([0, xa], [0, ya], lw=0.6, color=VERMELHO)
    ax.plot(0, 0, "o", ms=3, color=VERMELHO, mec=PAPEL, mew=0.5)
    ax.set_xlim(-MAPA_KM, MAPA_KM)
    ax.set_ylim(-MAPA_KM, MAPA_KM)

    # Recorte ampliado em volta da foto, onde a área de alcance aparece
    ins = ax.inset_axes([0.015, 0.015, 0.38, 0.38])
    camadas_mapa(ins)
    ins.plot(0, 0, "o", ms=2.5, color=VERMELHO, mec=PAPEL, mew=0.4)
    ins.set_xlim(-RECORTE_KM, RECORTE_KM)
    ins.set_ylim(-RECORTE_KM, RECORTE_KM)
    for lado in ins.spines.values():
        lado.set_edgecolor(TINTA)
        lado.set_linewidth(0.6)
    ins.text(0.04, 0.96, f"{2 * RECORTE_KM} km", fontsize=5.5, color=TINTA, va="top",
             transform=ins.transAxes)
    ax.add_patch(plt.Rectangle((-RECORTE_KM, -RECORTE_KM), 2 * RECORTE_KM, 2 * RECORTE_KM,
                               fill=False, lw=0.5, color=TINTA))

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
        ax.text(0, y, titulo, fontsize=6.5, color=AZUL60, va="top", transform=ax.transAxes)
        ax.text(0, y - 0.075, valor, fontsize=8, weight="regular", va="top",
                transform=ax.transAxes)
        y -= 0.22
    for k, (cor, alfa, texto) in enumerate([
            (VERDE, 1, "alcance do HT"),
            (AZUL_EMBLEMA, 0.7, "alcance das repetidoras*")]):
        yy = 0.27 - k * 0.15
        ax.add_patch(plt.Rectangle((0, yy), 0.06, 0.06, color=cor, alpha=alfa,
                                   transform=ax.transAxes))
        ax.text(0.09, yy + 0.03, texto, fontsize=6.5, va="center", transform=ax.transAxes,
                linespacing=0.95)
    ax.text(0, -0.03, f"* antena a {ALTURA_REPETIDORA} m no ponto mais alto\na até "
            f"{RAIO_SITIO_KM} km da cidade (melhor caso)", fontsize=5.5, color=AZUL60,
            va="bottom", transform=ax.transAxes)

    # 3. Perfil até a repetidora mais próxima
    ax = fig.add_subplot(g[1, :])
    dk = d / 1000
    base = np.nanmin(terreno) - 50
    ax.fill_between(dk, base, terreno, color=VERDE, alpha=0.35, lw=0)
    ax.plot(dk, terreno, lw=0.6, color=VERDE_ESCURO)
    ax.plot(dk, linha, lw=0.8, color=VERDE_ESCURO if ok else VERMELHO,
            ls="-" if ok else (0, (4, 2)))
    if not ok:
        ax.fill_between(dk, linha, terreno, where=linha < terreno, color=VERMELHO,
                        alpha=0.3, lw=0)
        excesso = np.nan_to_num(terreno - linha, nan=-1e4)
        k = int(np.argmax(excesso[1:-1])) + 1
        ax.annotate(f"este morro, a {br(dk[k], 1)} km, fica {br(excesso[k])} m\nacima da linha e corta o sinal",
                    xy=(dk[k], terreno[k]), xytext=(dk[k] + 4, terreno[k] + 170),
                    fontsize=6.5, color=VERMELHO, va="bottom",
                    arrowprops=dict(arrowstyle="-", color=VERMELHO, lw=0.5))
    ax.plot(0, linha[0], "o", ms=3, color=VERMELHO)
    ax.plot(dk[-1], linha[-1], "^", ms=3.5, color=AZUL)
    ax.text(0.5, linha[0] + 15, "foto", fontsize=6.5, va="bottom")
    ax.text(dk[-1], linha[-1] + 15, f"{alvo['indicativo']} ({alvo['cidade']}) ",
            fontsize=6.5, va="bottom", ha="right")
    ax.set_xlim(0, dk[-1])
    ax.set_ylim(base, max(np.nanmax(terreno), linha.max()) + 120)
    ax.set_xlabel("distância (km)", fontsize=7, labelpad=1)
    ax.set_ylabel("altitude (m)", fontsize=7, labelpad=1)
    ax.tick_params(labelsize=6.5, length=2, width=0.4, pad=1)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.set_facecolor(PAPEL)

    fig.savefig(SAIDA, facecolor=PAPEL)
    print(f"{SAIDA.relative_to(RAIZ)} gerado")
    print(f"  visada da foto: {area_foto:.0f} km²; foto coberta por alguma repetidora: {foto_coberta}")
    for r in REPETIDORAS:
        print(f"  {r['indicativo']}: {r['distancia_km']:.1f} km, visada até a foto: {r['visada']}, "
              f"cobertura {r['cobertura'].sum() * passo_km ** 2:.0f} km²")


if __name__ == "__main__":
    desenhar(*baixar_relevo())
