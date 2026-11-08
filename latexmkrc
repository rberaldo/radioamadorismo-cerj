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

# --- Figuras TikZ --------------------------------------------------------------
# Cada figuras/X.tex (classe standalone) vira img/X.pdf; os auxiliares ficam em
# build/figuras/. Só recompila a figura mais nova que o PDF (ou quando muda o
# preâmbulo comum, as cores ou um logo). Roda a cada `latexmk` e, no -pvc, antes
# de cada recompilação: como \figura registra figuras/X.tex como dependência da
# apresentação, salvar uma figura já dispara o -pvc.
use File::Copy qw(copy);
use File::Path qw(make_path);

sub compilar_figuras {
    my @comuns = ('engine/cerj-figuras.sty', 'engine/cerj-cores.sty', glob('img/logos/*'));
    make_path('build/figuras');
    for my $fonte (glob 'figuras/*.tex') {
        my ($nome) = $fonte =~ m{^figuras/(.+)\.tex$};
        my $pdf = "img/$nome.pdf";
        my $feito = -e $pdf ? (stat $pdf)[9] : 0;
        next unless grep { (stat $_)[9] > $feito } ($fonte, @comuns);
        print "Figura: $fonte -> $pdf\n";
        if (system('lualatex', '-interaction=nonstopmode', '-halt-on-error',
                   '-output-directory=build/figuras', $fonte) == 0) {
            copy("build/figuras/$nome.pdf", $pdf);
        } else {
            warn "Falha ao compilar $fonte (veja build/figuras/$nome.log)\n";
        }
    }
    return 0;
}

compilar_figuras();
$compiling_cmd = 'internal compilar_figuras';

$max_repeat = 5;
$clean_ext = 'nav snm vrb synctex.gz run.xml xdv';

# Visualizador no macOS (Skim recarrega sozinho em -pvc; Preview não)
$pdf_previewer = 'open %S';
