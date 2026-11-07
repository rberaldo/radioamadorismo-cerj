# SPDX-License-Identifier: CC-BY-SA-4.0
# latexmkrc — compila presentation.tex com LuaLaTeX, saída em build/
#
#   latexmk          compila
#   latexmk -pvc     modo contínuo (recompila ao salvar)
#   latexmk -C       apaga build/ (inclui o PDF)
#   latexmk -c       apaga só os arquivos auxiliares

$pdf_mode = 4;    # 4 = lualatex
$lualatex = 'lualatex -interaction=nonstopmode -file-line-error -synctex=1 %O %S';

@default_files = ('presentation.tex');
$out_dir = 'build';

# Deixa engine/ visível para \usetheme{cerj} e \usepackage{cerj-macros}
ensure_path('TEXINPUTS', './engine//');

$max_repeat = 5;
$clean_ext = 'nav snm vrb synctex.gz run.xml xdv';

# Visualizador no macOS (Skim recarrega sozinho em -pvc; Preview não)
$pdf_previewer = 'open %S';
