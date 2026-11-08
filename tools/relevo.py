# SPDX-License-Identifier: CC-BY-SA-4.0
# Copyright (c) 2026 Rafael Beraldo
"""Funções comuns aos estudos de alcance (relevo, perfis, linha de visada).

Relevo: Copernicus DEM GLO-30, lido da AWS com o GDAL só na janela pedida; o
recorte fica em cache em build/cache/. Visada com refração padrão (raio efetivo
da Terra = 4/3 do real).
"""
import json
import math
import subprocess
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager

RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / "build" / "cache"
K = 4 / 3
R_TERRA = 6_371_000.0

# Paleta (engine/cerj-cores.sty)
AZUL, AZUL60, AZUL_EMBLEMA = "#003366", "#6685A3", "#3C4398"
VERDE, VERDE_ESCURO, TINTA, PAPEL = "#44AC6A", "#338150", "#001F3D", "#FAFAFA"
VERMELHO, LARANJA = "#B32424", "#B34700"


def baixar_relevo(nome, oeste, sul, leste, norte, resolucao=1 / 3600):
    """Recorta o Copernicus GLO-30 na janela pedida. Devolve (z, lats, lons)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    tif = CACHE / f"{nome}.tif"
    if not tif.exists():
        urls = []
        for la in range(math.floor(sul), math.floor(norte) + 1):
            for lo in range(math.floor(oeste), math.floor(leste) + 1):
                ns = f"{'S' if la < 0 else 'N'}{abs(la):02d}"
                ew = f"{'W' if lo < 0 else 'E'}{abs(lo):03d}"
                n = f"Copernicus_DSM_COG_10_{ns}_00_{ew}_00_DEM"
                urls.append(f"/vsicurl/https://copernicus-dem-30m.s3.amazonaws.com/{n}/{n}.tif")
        vrt = CACHE / f"{nome}.vrt"
        subprocess.run(["gdalbuildvrt", "-q", str(vrt), *urls], check=True)
        subprocess.run(["gdal_translate", "-q", "-projwin", str(oeste), str(norte),
                        str(leste), str(sul), "-tr", str(resolucao), str(resolucao),
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
    z = np.where(np.isnan(z), 0.0, z)           # mar e lacunas no nível do mar
    lons = x0 + dx * (np.arange(w) + 0.5)
    lats = y0 + dy * (np.arange(h) + 0.5)
    return z, lats, lons


def distancia_km(lat0, lon0, lat, lon):
    p1, p2 = math.radians(lat0), math.radians(lat)
    a = (math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2)
         * math.sin(math.radians(lon - lon0) / 2) ** 2)
    return 2 * R_TERRA * math.asin(math.sqrt(a)) / 1000


def indice(lats, lons, la, lo):
    i = np.clip(np.round((la - lats[0]) / (lats[1] - lats[0])).astype(int), 0, len(lats) - 1)
    j = np.clip(np.round((lo - lons[0]) / (lons[1] - lons[0])).astype(int), 0, len(lons) - 1)
    return i, j


def ponto_mais_alto(z, lats, lons, lat, lon, raio_km):
    """Ponto mais alto do terreno a até raio_km de (lat, lon)."""
    km_lat = 110.574
    km_lon = 111.320 * math.cos(math.radians(lat))
    di = max(int(raio_km / (abs(lats[1] - lats[0]) * km_lat)), 1)
    dj = max(int(raio_km / (abs(lons[1] - lons[0]) * km_lon)), 1)
    i0, j0 = indice(lats, lons, np.array([lat]), np.array([lon]))
    ii, jj = np.mgrid[-di:di + 1, -dj:dj + 1]
    dentro = (ii / di) ** 2 + (jj / dj) ** 2 <= 1
    ii = np.clip(ii[dentro] + i0[0], 0, len(lats) - 1)
    jj = np.clip(jj[dentro] + j0[0], 0, len(lons) - 1)
    k = int(np.argmax(z[ii, jj]))
    return float(lats[ii[k]]), float(lons[jj[k]])


def curvatura(d):
    """Quanto o terreno 'desce' a uma distância d (m), pela curvatura da Terra."""
    return d ** 2 / (2 * K * R_TERRA)


def perfil(z, lats, lons, a, b, passo_m=30):
    """Distâncias (m) e elevações de a = (lat, lon) até b = (lat, lon)."""
    total = distancia_km(*a, *b) * 1000
    t = np.linspace(0, 1, max(int(total / passo_m), 2))
    i, j = indice(lats, lons, a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
    return t * total, z[i, j]


def visada(d, elev, alt_inicio, alt_fim):
    """Há linha de visada entre as pontas do perfil? Devolve (ok, linha, terreno)."""
    terreno = elev - curvatura(d)
    h0, h1 = terreno[0] + alt_inicio, terreno[-1] + alt_fim
    linha = h0 + (h1 - h0) * d / d[-1]
    return bool((linha[1:-1] > terreno[1:-1]).all()), linha, terreno


def fontes(tamanho=8):
    """Fira Sans do TeX Live e cores do tema no matplotlib."""
    for nome in ("FiraSans-Light.otf", "FiraSans-Regular.otf"):
        caminho = subprocess.run(["kpsewhich", nome], capture_output=True, text=True).stdout.strip()
        if caminho:
            font_manager.fontManager.addfont(caminho)
    plt.rcParams.update({
        "font.family": "Fira Sans", "font.weight": 300, "font.size": tamanho,
        "axes.edgecolor": AZUL60, "axes.labelcolor": TINTA, "text.color": TINTA,
        "xtick.color": AZUL60, "ytick.color": AZUL60, "axes.linewidth": 0.5,
        "pdf.fonttype": 42})


def br(x, casas=0):
    """Número no formato brasileiro."""
    return f"{x:,.{casas}f}".replace(",", " ").replace(".", ",").replace(" ", ".")
