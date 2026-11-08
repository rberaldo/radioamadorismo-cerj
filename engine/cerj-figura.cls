% SPDX-License-Identifier: CC-BY-SA-4.0
% Copyright (c) 2026 Rafael Beraldo
%% cerj-figura.cls
%% Classe das figuras TikZ em figuras/: standalone (11pt, tikz) com a fonte
%% (Fira Sans, do metropolis), as cores e as unidades do tema. Incluído sem
%% escala, o PDF fica idêntico a um desenho feito direto no slide.
%%
%% Cada figura começa assim (a 2ª linha acha engine/ compilando da raiz ou de
%% dentro de figuras/; com latexmk nem seria preciso):
%%   \makeatletter\def\input@path{{engine/}{../engine/}}\makeatother
%%   \documentclass{cerj-figura}
%% Opções são repassadas à standalone (ex.: [border=0pt]).
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{cerj-figura}[2026/11/08 v0.2 Figuras TikZ do curso CERJ]

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{standalone}}
\ProcessOptions\relax
\LoadClass[11pt, border=2pt, tikz]{standalone}

\RequirePackage{fontspec}
\setsansfont[BoldFont={Fira Sans}, ItalicFont={Fira Sans Light Italic},
             BoldItalicFont={Fira Sans Italic}]{Fira Sans Light}
\renewcommand{\familydefault}{\sfdefault}

\usetikzlibrary{positioning, arrows.meta, calc}
\RequirePackage{fontawesome5}
\RequirePackage{cerj-cores}
\RequirePackage{cerj-unidades}   % \freq, como nos slides

% Figuras são compiladas a partir da raiz do projeto
\graphicspath{{img/}}


% ---------------------------------------------------------------------------
% Logos de outras organizações
% ---------------------------------------------------------------------------
% \orglogo{arquivo}{alternativa}: logo de img/logos/arquivo.pdf ou .png (ou de
% img/arquivo.png, como o do CERJ) numa caixa de \cerjlogolargura ×
% \cerjlogoaltura. Sem o arquivo, imprime a alternativa (ex.: um ícone).
\newlength{\cerjlogolargura}\setlength{\cerjlogolargura}{1cm}
\newlength{\cerjlogoaltura}\setlength{\cerjlogoaltura}{.8cm}
\newcommand{\cerj@logo}[1]{%
  \includegraphics[width=\cerjlogolargura, height=\cerjlogoaltura, keepaspectratio]{#1}}
\newcommand{\orglogo}[2]{%
  \IfFileExists{img/logos/#1.pdf}{\cerj@logo{logos/#1}}{%
    \IfFileExists{img/logos/#1.png}{\cerj@logo{logos/#1}}{%
      \IfFileExists{img/#1.png}{\cerj@logo{#1}}{#2}}}}

% \orgcartao{arquivo}{alternativa}{nome}: logo e nome lado a lado, alinhados
% em colunas fixas, para usar dentro de um nó TikZ.
\newcommand{\orgcartao}[3]{%
  \makebox[\cerjlogolargura]{$\vcenter{\hbox{\orglogo{#1}{#2}}}$}%
  \hspace{.5em}\makebox[2.1cm][l]{\small\bfseries #3}}

\endinput
