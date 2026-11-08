# SPDX-License-Identifier: CC-BY-SA-4.0
# Copyright (c) 2026 Rafael Beraldo
"""Relevo e linha de visada, para os estudos de alcance (sempre_vivas.py,
caledonia.py).

Relevo: Copernicus DEM GLO-30, lido da AWS com o GDAL só na janela pedida e
reamostrado; o recorte fica em cache em build/cache/. Visada com refração
padrão (raio efetivo da Terra = 4/3 do real). É um cálculo só de linha de
visada: não considera potência, difração nem reflexões, então mostra o melhor
caso.
"""
import json
import math
import subprocess
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / "build" / "cache"
K = 4 / 3                 # refração padrão
R_TERRA = 6_371_000.0
KM_LAT = 110.574          # km por grau de latitude


def km_lon(lat):
    """km por grau de longitude, nesta latitude."""
    return 111.320 * math.cos(math.radians(lat))


def janela(lat, lon, raio_km):
    """(oeste, sul, leste, norte) de um quadrado de raio_km em volta do ponto."""
    dlat, dlon = raio_km / KM_LAT, raio_km / km_lon(lat)
    return lon - dlon, lat - dlat, lon + dlon, lat + dlat


def projecao(lat0, lon0):
    """Função (lat, lon) -> (x, y) em km, com a origem no ponto dado."""
    kl = km_lon(lat0)
    return lambda lat, lon: ((lon - lon0) * kl, (lat - lat0) * KM_LAT)


# --- Relevo --------------------------------------------------------------------

def baixar_relevo(nome, oeste, sul, leste, norte, resolucao=1 / 3600):
    """Recorta o Copernicus GLO-30 na janela (graus). Devolve (z, lats, lons).

    resolucao em graus: 1/3600 = 1" (~30 m), 1/1200 = 3" (~90 m). Mar e lacunas
    ficam no nível do mar (0).
    """
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
    z = np.where((z < -1000) | np.isnan(z), 0.0, z)
    lons = x0 + dx * (np.arange(w) + 0.5)
    lats = y0 + dy * (np.arange(h) + 0.5)
    return z, lats, lons


def passo_km(lats):
    """Tamanho de uma célula do relevo, em km (na latitude)."""
    return abs(lats[1] - lats[0]) * KM_LAT


# --- Geometria -----------------------------------------------------------------

def distancia_km(lat0, lon0, lat, lon):
    p1, p2 = math.radians(lat0), math.radians(lat)
    a = (math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2)
         * math.sin(math.radians(lon - lon0) / 2) ** 2)
    return 2 * R_TERRA * math.asin(math.sqrt(a)) / 1000


def indice(lats, lons, la, lo):
    """Índices (i, j) das células mais próximas de vetores de lat/lon."""
    i = np.clip(np.round((la - lats[0]) / (lats[1] - lats[0])).astype(int), 0, len(lats) - 1)
    j = np.clip(np.round((lo - lons[0]) / (lons[1] - lons[0])).astype(int), 0, len(lons) - 1)
    return i, j


def ponto_mais_alto(z, lats, lons, lat, lon, raio_km):
    """Ponto mais alto do terreno a até raio_km de (lat, lon)."""
    di = max(int(raio_km / passo_km(lats)), 1)
    dj = max(int(raio_km / (abs(lons[1] - lons[0]) * km_lon(lat))), 1)
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


def area_de_visada(z, lats, lons, lat_obs, lon_obs, alt_obs, alt_alvo, alcance_km):
    """Células, até alcance_km, de onde um alvo a alt_alvo do chão enxerga o
    observador a alt_obs do chão (e vice-versa). Varre o horizonte em raios."""
    visivel = np.zeros(z.shape, dtype=bool)
    passo = passo_km(lats) * 1000                            # m por célula
    n = int(alcance_km * 1000 / passo)
    k = np.arange(1, n + 1)
    d = k * passo
    queda = curvatura(d)
    i0 = (lat_obs - lats[0]) / (lats[1] - lats[0])
    j0 = (lon_obs - lons[0]) / (lons[1] - lons[0])
    escala_j = KM_LAT / km_lon(lat_obs) * abs((lats[1] - lats[0]) / (lons[1] - lons[0]))
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
        terreno = z[ii, jj] - qq
        ang_terreno = (terreno - h0) / dd
        ang_alvo = (terreno + alt_alvo - h0) / dd
        horizonte = np.maximum.accumulate(np.concatenate([[-np.inf], ang_terreno[:-1]]))
        visivel[ii, jj] |= ang_alvo >= horizonte
    return visivel
