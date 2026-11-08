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

# Deixa engine/ visível para \usetheme{cerj}, \usepackage{cerj-macros} e a
# classe cerj-figura (vale também para os lualatex das figuras, abaixo)
ensure_path('TEXINPUTS', './engine//');

# --- Figuras TikZ --------------------------------------------------------------
# Cada figuras/X.tex (classe cerj-figura) vira img/X.pdf; os auxiliares ficam em
# build/figuras/. Só recompila a figura mais nova que o PDF, ou quando muda algo
# de que todas dependem: a classe, as cores, as unidades, os logos e as fotos.
# Roda a cada `latexmk` e, no -pvc, antes de cada recompilação: como \figura
# registra figuras/X.tex como dependência da apresentação, salvar uma figura
# já dispara o -pvc.
use File::Copy qw(copy);
use File::Path qw(make_path);

sub compilar_figuras {
    my @comuns = (glob('engine/cerj-figura.cls engine/cerj-cores.sty engine/cerj-unidades.sty'),
                  glob('img/logos/* img/*.png img/*.jpg'));
    make_path('build/figuras');
    for my $fonte (glob 'figuras/*.tex') {
        my ($nome) = $fonte =~ m{^figuras/(.+)\.tex$};
        my $pdf = "img/$nome.pdf";
        my $feito = -e $pdf ? (stat $pdf)[9] : 0;
        next unless grep { (stat $_)[9] > $feito } ($fonte, @comuns);
        print "Figura: $fonte -> $pdf\n";
        # batchmode: nada no terminal; erros ficam em build/figuras/$nome.log
        if (system('lualatex', '-interaction=batchmode', '-halt-on-error',
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

# Visualizador: Skim/Preview no macOS, o padrão do sistema no Linux
$pdf_previewer = $^O eq 'darwin' ? 'open %S' : 'xdg-open %S';
