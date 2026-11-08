# Radioamadorismo para Montanhistas

Slides do curso de radioamadorismo para montanhistas do
[Centro Excursionista Rio de Janeiro (CERJ)](https://cerj.org.br),
feitos em LaTeX com Beamer e o tema
[metropolis](https://github.com/matze/mtheme), adaptado às cores do CERJ.

## Requisitos

- Uma distribuição TeX recente (TeX Live 2024 ou mais nova, ou MacTeX) com
  LuaLaTeX e `latexmk`.
- Pacotes usados: `beamer`, `beamertheme-metropolis`, `polyglossia`,
  `fontspec`, `fira`, `tcolorbox`, `siunitx`, `booktabs`, `fontawesome5`,
  `natbib`, `xurl`, `appendixnumberbeamer`, `pgf/tikz`, `standalone`.
  Todos fazem parte da instalação completa do TeX Live.
- Só para regerar as figuras de `tools/` (opcional): Python 3 com `numpy`,
  `matplotlib` e `Pillow`, e os utilitários do GDAL (`gdal_translate`,
  `gdalinfo`) para o relevo.

## Como compilar

```sh
latexmk          # gera build/presentation.pdf
latexmk -pvc     # recompila automaticamente a cada salvamento
latexmk -c       # apaga arquivos auxiliares
latexmk -C       # apaga tudo em build/, inclusive o PDF
```

O arquivo `latexmkrc` configura o LuaLaTeX, a pasta de saída `build/` e
acrescenta `engine/` ao caminho de busca do TeX. Ele também compila as figuras
TikZ de `figuras/` (veja abaixo). O `latexmk -pvc` percebe mudanças em qualquer
arquivo de `slides/`, `engine/` e `figuras/`.

## Estrutura

```
presentation.tex          preâmbulo, metadados, links e a ordem das partes
slides/                   o conteúdo, uma parte por arquivo, incluídos por \input
  01-historia-pessoal.tex … 09-encerramento.tex, 90-anexos.tex
latexmkrc                 configuração do latexmk (LuaLaTeX, saída em build/)
engine/
  beamerthemecerj.sty     tema: logo, capa, páginas de seção, rodapé
  cerj-cores.sty          paleta CERJ (tema, figuras e gráficos em Python)
  cerj-unidades.sty       números e unidades (\freq), comuns a slides e figuras
  cerj-macros.sty         macros do curso: links, citações, \figura, caixas, fotos
  cerj-figura.cls         classe das figuras TikZ (standalone, fonte, cores, logos)
figuras/                  fontes TikZ, uma figura por arquivo
  espectro-brasil.tex     espectro brasileiro (gerado por tools/espectro.py)
  propagacao.tex          introdução à propagação, em 3 passos
  organizacoes.tex        entidades do radioamadorismo × do montanhismo
  baofeng.tex             anatomia do Baofeng UV-5R, 4 passos sobre as fotos
  repetidora.tex          como funciona uma repetidora
img/                      só imagens prontas: fotos, logos e os PDFs das figuras
  cerj-logo.png           emblema do CERJ
  logos/                  logos de IARU, LABRE, LABRE-RJ, UIAA, CBME e FEEMERJ
  *.pdf                   saída de figuras/*.tex e de tools/*.py (não edite: é regerada)
tools/
  espectro.py             escreve figuras/espectro-brasil.tex a partir dos dados da Anatel
  relevo.py               relevo (Copernicus), perfis e linha de visada
  estilo.py               paleta (lida de cerj-cores.sty), fonte e figura do tamanho do slide
  sempre_vivas.py         estudo de alcance no PN das Sempre-Vivas (img/sempre-vivas-alcance.pdf)
  caledonia.py            alcance da PY1MAC, no alto da Caledônia (img/caledonia-alcance.pdf)
dados/
  pdff-brasil.json        plano de faixas da Anatel (PDFF), coluna Brasil
```

## Figuras TikZ

Cada desenho TikZ fica num arquivo próprio em `figuras/`, com a classe
`cerj-figura` (`standalone` com a fonte, as cores e as unidades do tema). O
`latexmkrc` compila cada `figuras/X.tex` para `img/X.pdf`, só quando a figura
mudou, e a apresentação inclui o PDF pronto. Assim a apresentação não recompila
os desenhos a cada passada.

- `\figura{X}` inclui `img/X.pdf` sem escala (também os PDFs gerados por
  `tools/`).
- `\figurapassos{X}{n}` inclui uma figura de *n* páginas, uma por passo do
  slide (página *k* no passo *k*). Na fonte, desenhe cada passo como uma
  página (veja `figuras/propagacao.tex`).
- Para uma figura nova, crie `figuras/X.tex` copiando o cabeçalho de uma das
  existentes e use `\figura{X}` no slide. O `latexmk -pvc` percebe quando você
  salva a figura e recompila tudo.

## Tipos de slide

| Tipo | Como usar |
|---|---|
| Capa escura com logo | `\cerjtitleframe` (ou `\maketitle` para capa clara) |
| Sumário | `\tableofcontents` |
| Página de seção | automática a cada `\section{...}` |
| Lista com revelação progressiva | `\begin{itemize}[<+->]` |
| Duas colunas, texto e imagem | ambiente `columns` com `\foto{arquivo}{legenda}` |
| Foto em tela cheia com legenda | `\cerjfullimage{arquivo}{legenda}` |
| Tabela | `tabular` com `booktabs` |
| Blocos | `block`, `alertblock`, `exampleblock` |
| Caixas de destaque | ambientes `dica`, `atencao`, `regulamento` |
| Listas de ✓ e ✗ | ambientes `certos` e `errados` (prós e contras) |
| Lista numerada | `enumerate` |
| Frase de impacto | `\begin{frame}[standout]` |
| Encerramento com contatos | `standout` com `\cerjlogo` |
| Anexos fora da contagem | depois de `\appendix` |

Macros de texto:

- `\freq{146,520}` imprime 146,520 MHz e `\freqrange{144}{148}` imprime
  144 a 148 MHz; para outras unidades, `\qty{88,5}{\hertz}` (siunitx).
- `\indicativo{PY1XXX}` imprime um indicativo de chamada em monoespaçado.
- `\alert{termo}` destaca um termo em laranja e negrito (o `\alert` do Beamer,
  ajustado pelo tema); `\destaque{termo}` faz o mesmo sem overlay, para
  dentro de tabelas.
- `\foto{arquivo}{legenda}` põe uma foto na largura da coluna com a legenda
  embaixo. Aceita opções do `\includegraphics` (`\foto[height=4cm]{...}{...}`);
  com `{}` no lugar da legenda, sai só a foto.
- `\legenda{texto}` escreve uma legenda discreta sob qualquer coisa (figura,
  tabela).
- `\linkexterno{\linkX}{texto}` faz um link com o ícone de "abre fora"; os
  endereços ficam no bloco de links do preâmbulo (`\linkCERJ` etc.). Nas
  referências, `\mostrarlink{\linkX}` mostra o próprio endereço, sem ícone.
- `\asterisco` marca um ponto do texto com um * e `\comentario{texto}` escreve
  "* texto" ali mesmo, com a fonte do `\legenda` (a posição fica por sua conta).

## Personalização

**Cores.** Ficam em `engine/cerj-cores.sty` e vêm de duas fontes: o papel
timbrado oficial do CERJ (Azul CERJ `#003366` e seus tons misturados ao
branco) e o emblema (cores medidas nos pixels de `img/cerj-logo.png`). O verde
e o creme do emblema são claros demais para texto sobre branco, por isso o
texto usa versões escurecidas.

| Nome | Hex | Origem | Uso |
|---|---|---|---|
| `cerjNavy` | `#003366` | papel timbrado | fundos da capa, seções e título dos slides |
| `cerjNavy80` | `#335C85` | papel timbrado | título dos blocos de exemplo |
| `cerjNavy60` | `#6685A3` | papel timbrado | |
| `cerjNavy40` | `#99ADC2` | papel timbrado | contornos |
| `cerjNavy20` | `#CCD6E0` | papel timbrado | texto claro sobre o azul, barra de progresso |
| `cerjNavy10` | `#E6EBF0` | papel timbrado | fundo dos blocos e da caixa `regulamento` |
| `cerjBlue` | `#3C4398` | emblema | texto dos blocos de exemplo |
| `cerjGreen` | `#44AC6A` | emblema | barra de progresso, subtítulo da capa, links nos slides de fundo azul |
| `cerjGreenVivid` | `#11B255` | emblema | |
| `cerjYellow` | `#F6EFAB` | emblema | fundo da caixa `atencao` |
| `cerjGreenDark` | `#338150` | derivada | marcadores, links e citações |
| `cerjOrange` | `#B34700` | derivada | `\alert` (complementar do azul, para chamar atenção) |
| `cerjOrangeLight` | `#F5A15A` | derivada | `\alert` nos slides de fundo azul |
| `cerjRed` | `#B32424` | derivada | "não": listas de contras, bloqueio de sinal, sem visada |
| `cerjInk` | `#001F3D` | derivada | texto |
| `cerjMuted` | `#647789` | derivada | legendas e comentários |
| `cerjPaper` | `#FAFAFA` | derivada | fundo dos slides (quase branco, ofusca menos no projetor) |

**Logo.** `img/cerj-logo.png` é o emblema em alta resolução (2858 × 2378 px,
fundo transparente).

**Imagens.** Fotos ficam em `img/`; use `\foto{nome}{legenda}` ou
`\cerjfullimage{nome}{legenda}`.

## Licença

O conteúdo deste repositório (slides, código LaTeX e textos) está licenciado
sob a [Creative Commons Atribuição-CompartilhaIgual 4.0 Internacional
(CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/deed.pt-br).
O texto legal completo está em [`LICENSE`](LICENSE).

Você pode copiar, redistribuir e adaptar o material, inclusive para fins
comerciais, desde que dê o crédito apropriado e distribua as adaptações sob a
mesma licença.

**Exceção:** o emblema do CERJ (`img/cerj-logo.png`) é marca do Centro
Excursionista Rio de Janeiro e **não** está coberto pela licença CC BY-SA.
Ele foi incluído apenas para identificar o curso. Em trabalhos derivados que
não sejam do CERJ, remova-o ou obtenha autorização do clube.

Pelo mesmo motivo, os logos em `img/logos/` (IARU, LABRE, LABRE-RJ, UIAA,
CBME e FEEMERJ) são marcas das respectivas organizações, usados apenas para
identificá-las, e também ficam fora da licença CC BY-SA.

### Conteúdo de terceiros

Também ficam fora da licença CC BY-SA, com os direitos de seus autores:

| Arquivo | Origem |
|---|---|
| `img/caledonia-William.jpeg` | foto de William de Abreu, usada com permissão |
| `img/talkabout.png` | anúncio do kit Motorola Talkabout T110br |
| `img/Repeater-Book-RJ.png` | captura de tela do [RepeaterBook](https://www.repeaterbook.com) |
| `img/espectro-simulacao.png` | captura de tela do simulador da [Mini Physics](https://www.miniphysics.com) |
| `img/antenna1.png` | detalhe da capa da revista *Antenna*, n. 1, 1926 |

Os dados usados pelas figuras de `tools/` têm licença própria:

- Relevo (`sempre-vivas-alcance.pdf`, `caledonia-alcance.pdf`): Copernicus DEM
  GLO-30, © DLR e.V. 2010–2014 e © Airbus Defence and Space GmbH 2014–2018,
  fornecido no âmbito do COPERNICUS pela União Europeia e pela ESA.
- Coordenadas dos picos: © colaboradores do OpenStreetMap, licença ODbL.
- Repetidoras: [RepeaterBook](https://www.repeaterbook.com), três registros
  consultados à mão, com o link de cada um em `tools/sempre_vivas.py`.
- Espectro (`espectro-brasil.pdf`): PDFF da Anatel, dado público.

Autor: Rafael Beraldo.
