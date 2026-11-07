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
acrescenta `engine/` ao caminho de busca do TeX.

## Estrutura

```
presentation.tex          conteúdo dos slides
latexmkrc                 configuração do latexmk (LuaLaTeX, saída em build/)
engine/
  beamerthemecerj.sty     tema: logo, capa, páginas de seção, rodapé
  cerj-cores.sty          paleta CERJ (usada pelo tema e pelas figuras)
  cerj-macros.sty         macros do curso: frequências, indicativos, caixas, fotos
img/
  cerj-logo.png           emblema do CERJ
  espectro-brasil.pdf     espectro brasileiro com as faixas de radioamador
  espectro-brasil.tex     fonte da figura acima (gerada por tools/espectro.py)
tools/
  espectro.py             gera a figura do espectro a partir dos dados da Anatel
dados/
  pdff-brasil.json        plano de faixas da Anatel (PDFF), coluna Brasil
```

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
- `\destaque{termo}` destaca um termo em verde, sem efeito de overlay.
- `\foto{arquivo}{legenda}` põe uma foto na largura da coluna com a legenda
  embaixo. Aceita opções do `\includegraphics` (`\foto[height=4cm]{...}{...}`);
  com `{}` no lugar da legenda, sai só a foto.
- `\legenda{texto}` escreve uma legenda discreta sob qualquer coisa (figura,
  tabela).

## Personalização

**Cores.** Ficam em `engine/cerj-cores.sty`. As cores
`cerjBlue`, `cerjGreen` e `cerjYellow` foram medidas no emblema oficial. As
demais são derivadas delas, porque o azul e o verde puros do emblema ofuscam
quando usados como fundo em projetores.

| Nome | Hex | Uso |
|---|---|---|
| `cerjNavy` | `#131A66` | fundos da capa, seções e título dos slides |
| `cerjBlue` | `#0008FF` | azul do emblema, links |
| `cerjRoyal` | `#2433C8` | blocos de exemplo |
| `cerjGreen` | `#3CEB2E` | barra de progresso, subtítulo da capa |
| `cerjGreenDark` | `#2A9A22` | marcadores, `\alert`, `\destaque` |
| `cerjYellow` | `#F4FB95` | fundo da caixa `atencao` |
| `cerjInk` | `#1D2238` | texto |

**Logo.** O emblema em `img/cerj-logo.png` tem só 150 px, que é a versão
publicada no site do CERJ. Para melhorar a nitidez, substitua o arquivo por
uma versão em alta resolução ou vetorial (PDF) com o mesmo nome de base.

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
