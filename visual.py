"""Padrao visual dos graficos do projeto.

Uso nos notebooks:

    fig, ax = grafico("Titulo que afirma algo", subtitulo="contexto pra ler o grafico")
    ax.plot(df["Data"], df["coluna"], color=AZUL)
    salvar(fig, "nome-do-grafico.png")

Trocar uma linha aqui muda todos os graficos do projeto.
"""
import os

import matplotlib.pyplot as plt

# paleta categorica em ordem fixa — atribuir nessa ordem, nunca reciclar
AZUL = "#2a78d6"
LARANJA = "#eb6834"
VERDE = "#1baf7a"
AMARELO = "#eda100"
CATEGORICAS = [AZUL, LARANJA, VERDE, AMARELO]

TEXTO = "#0b0b0b"
TEXTO_SECUNDARIO = "#52514e"
CINZA = "#c9c8c0"  # serie de apoio, ex: dado cru atras de uma media movel
GRADE = "#dddddd"

FONTE_FRAUDE = (
    "Fonte: Banco Central do Brasil, Dados Abertos do Pix (EstatisticasFraudesPix)."
)
FONTE_FRAUDE_E_TRANSACOES = (
    "Fonte: Banco Central do Brasil, Dados Abertos do Pix "
    "(EstatisticasFraudesPix e EstatisticasTransacoesPix)."
)

# espacos em polegadas, pra nao depender da altura da figura
_MARGEM = 0.15
_LINHA_TITULO = 0.26
_LINHA_SUBTITULO = 0.19
_RODAPE = 0.32


def grafico(titulo, subtitulo=None, fonte=FONTE_FRAUDE, linhas=1, figsize=None):
    """Cria a figura no padrao do projeto.

    Titulo alinhado a esquerda, subtitulo menor abaixo, fonte no rodape. Sem
    borda de cima e da direita, grade horizontal discreta. Devolve (fig, ax);
    com `linhas` > 1, (fig, lista de eixos) empilhados com o eixo X
    compartilhado.
    """
    if figsize is None:
        figsize = (9, 4.5) if linhas == 1 else (9, 3.6 * linhas)
    fig, eixos = plt.subplots(linhas, 1, figsize=figsize, sharex=linhas > 1)
    lista = [eixos] if linhas == 1 else list(eixos)

    for ax in lista:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", color=GRADE, linewidth=0.8)
        ax.set_axisbelow(True)
        ax.set_prop_cycle(color=CATEGORICAS)

    altura = figsize[1]
    fig.text(0.01, 1 - _MARGEM / altura, titulo, ha="left", va="top",
             fontsize=12, fontweight="bold", color=TEXTO)
    topo = _MARGEM + _LINHA_TITULO * (titulo.count("\n") + 1)

    if subtitulo:
        fig.text(0.01, 1 - topo / altura, subtitulo, ha="left", va="top",
                 fontsize=9, color=TEXTO_SECUNDARIO)
        topo += _LINHA_SUBTITULO * (subtitulo.count("\n") + 1)

    if fonte:
        fig.text(0.01, _MARGEM / 2 / altura, fonte, ha="left", va="bottom",
                 fontsize=7.5, color=TEXTO_SECUNDARIO)

    fig._espaco_reservado = (topo + 0.1, _RODAPE if fonte else _MARGEM)
    return fig, (eixos if linhas == 1 else lista)


def pasta_graficos():
    """../graficos dentro do repositorio; graficos/ quando o notebook roda fora
    dele (no Colab, a pasta de trabalho e /content e ../graficos nao existe)."""
    return "../graficos" if os.path.isdir("../graficos") else "graficos"


def salvar(fig, nome, dpi=150):
    """Ajusta o layout reservando o espaco do cabecalho e do rodape e grava o
    PNG em pasta_graficos(). Devolve o caminho gravado."""
    topo, rodape = getattr(fig, "_espaco_reservado", (0, 0))
    altura = fig.get_figheight()
    fig.tight_layout(rect=[0, rodape / altura, 1, 1 - topo / altura])

    pasta = pasta_graficos()
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, nome)
    fig.savefig(caminho, dpi=dpi)
    return caminho
