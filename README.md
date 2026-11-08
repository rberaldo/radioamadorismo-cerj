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
  `appendixnumberbeamer`, `pgf/tikz`, `mwe` (imagens de exemplo).
  Todos fazem parte da instalação completa do TeX Live.

## Como compilar

```sh
latexmk          # gera build/presentation.pdf
latexmk -pvc     # recompila automaticamente a cada salvamento
latexmk -c       # apaga arquivos auxiliares
latexmk -C       # apaga tudo em build/, inclusive o PDF
```

O arquivo `latexmkrc` configura o LuaLaTeX, a pasta de saída `build/` e
acrescenta `engine/` ao caminho de busca do TeX. Ele também compila as figuras
TikZ de `figuras/` (veja abaixo).

## Estrutura

```
presentation.tex          conteúdo dos slides
latexmkrc                 configuração do latexmk (LuaLaTeX, saída em build/)
engine/
  beamerthemecerj.sty     tema: logo, capa, páginas de seção, rodapé
  cerj-cores.sty          paleta CERJ (usada pelo tema e pelas figuras)
  cerj-macros.sty         macros do curso: frequências, indicativos, caixas, fotos
  cerj-figuras.sty        preâmbulo comum das figuras TikZ (fonte, cores, logos)
figuras/                  fontes TikZ, uma figura por arquivo (classe standalone)
  espectro-brasil.tex     espectro brasileiro (gerado por tools/espectro.py)
img/                      só imagens prontas: fotos e os PDFs das figuras
  cerj-logo.png           emblema do CERJ
  *.pdf                   saída de figuras/*.tex (não edite: é regerada)
tools/
  espectro.py             gera a figura do espectro a partir dos dados da Anatel
dados/
  pdff-brasil.json        plano de faixas da Anatel (PDFF), coluna Brasil
```

## Figuras TikZ

Cada desenho TikZ fica num arquivo próprio em `figuras/`, com a classe
`standalone` e o preâmbulo comum `engine/cerj-figuras.sty` (mesma fonte, cores
e tamanhos do tema). O `latexmkrc` compila cada `figuras/X.tex` para
`img/X.pdf`, só quando a figura mudou, e a apresentação inclui o PDF pronto.
Assim a apresentação não recompila os desenhos a cada passada.

- `\figura{X}` inclui `img/X.pdf` sem escala.
- `\figurapassos{X}{n}` inclui uma figura de *n* páginas, uma por passo do
  slide (página *k* no passo *k*). Na fonte, desenhe cada passo como uma
  página.
- Para uma figura nova, crie `figuras/X.tex` copiando o cabeçalho de uma das
  existentes e use `\figura{X}` no slide. O `latexmk -pvc` percebe quando você
  salva a figura e recompila tudo.

## Modelos de slide incluídos

`presentation.tex` traz um exemplo de cada tipo, pronto para copiar:

| Modelo | Como usar |
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
| Lista numerada | `enumerate` |
| Frase de impacto | `\begin{frame}[standout]` |
| Encerramento com contatos | `standout` com `\cerjlogo` |
| Anexos fora da contagem | depois de `\appendix` |

Macros de texto:

- `\freq{146.520}` imprime 146,520 MHz e `\freqrange{144}{148}` imprime
  144 a 148 MHz.
- `\indicativo{PY1XXX}` imprime um indicativo de chamada em monoespaçado.
- `\alert{termo}` destaca um termo em verde e negrito (o `\alert` do Beamer,
  ajustado pelo tema).
- `\foto{arquivo}{legenda}` põe uma foto na largura da coluna com a legenda
  embaixo. Aceita opções do `\includegraphics` (`\foto[height=4cm]{...}{...}`);
  com `{}` no lugar da legenda, sai só a foto.
- `\legenda{texto}` escreve uma legenda discreta sob qualquer coisa (figura,
  tabela).

## Personalização

**Cores.** Ficam em `engine/cerj-cores.sty` e vêm de duas fontes: o papel
timbrado oficial do CERJ (Azul CERJ `#003366` e seus tons misturados ao
branco) e o emblema (cores medidas nos pixels de `img/cerj-logo.png`). O verde
e o creme do emblema são claros demais para texto sobre branco, por isso o
texto usa versões escurecidas.

| Nome | Hex | Origem | Uso |
|---|---|---|---|
| `cerjAzul` (= `cerjNavy`) | `#003366` | papel timbrado | fundos da capa, seções e título dos slides |
| `cerjAzul80` (= `cerjRoyal`) | `#335C85` | papel timbrado | título dos blocos de exemplo |
| `cerjAzul60` | `#6685A3` | papel timbrado | |
| `cerjAzul40` | `#99ADC2` | papel timbrado | contornos |
| `cerjAzul20` | `#CCD6E0` | papel timbrado | texto claro sobre o azul, barra de progresso |
| `cerjAzul10` | `#E6EBF0` | papel timbrado | fundo dos blocos e da caixa `regulamento` |
| `cerjBlue` | `#3C4398` | emblema | links |
| `cerjGreen` | `#44AC6A` | emblema | barra de progresso, subtítulo da capa |
| `cerjGreenVivid` | `#11B255` | emblema | |
| `cerjYellow` | `#F6EFAB` | emblema | fundo da caixa `atencao` |
| `cerjGreenDark` | `#338150` | derivada | marcadores, `\alert` |
| `cerjInk` | `#001F3D` | derivada | texto |
| `cerjPaper` | `#FAFAFA` | derivada | fundo dos slides (quase branco, ofusca menos no projetor) |

**Logo.** `img/cerj-logo.png` é o emblema em alta resolução (2858 × 2378 px,
fundo transparente).

**Imagens.** Coloque suas fotos em `img/` e troque os nomes
`example-image-*` usados nos slides de exemplo.

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

Autor: Rafael Beraldo.
