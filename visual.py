"""Padrao visual dos graficos do projeto.

Uso nos notebooks:

    fig, ax = grafico("Titulo que afirma algo", subtitulo="contexto pra ler o grafico")
    ax.plot(df["Data"], df["coluna"], color=AZUL)
    salvar(fig, "nome-do-grafico.png")

Trocar uma linha aqui muda todos os graficos do projeto.
"""
import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

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

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

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


def numero_br(valor, _posicao=None):
    """17.5 -> '17,5'; 1750 -> '1.750'. Formato de numero dos eixos."""
    texto = f"{valor:,.2f}".rstrip("0").rstrip(".")
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def mes_br(valor, _posicao=None):
    """Data do eixo (numero de dias do matplotlib) -> 'jan/22'."""
    data = mdates.num2date(valor)
    return f"{MESES[data.month - 1]}/{data:%y}"


def eixo_milhoes(ax):
    """Eixo Y em milhoes ('3,5 mi'), no lugar do '1e6' que o matplotlib poe no
    canto quando os valores sao grandes."""
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _p: f"{numero_br(v / 1e6)} mi" if v else "0")
    )


def _formatar_eixos(fig):
    """Datas em portugues no X e numeros com virgula decimal no Y, sem mexer em
    eixo que o notebook ja formatou por conta propria (ex: eixo_milhoes)."""
    for ax in fig.axes:
        if isinstance(ax.xaxis.get_major_formatter(), (mdates.AutoDateFormatter, mdates.ConciseDateFormatter)):
            ax.xaxis.set_major_formatter(mticker.FuncFormatter(mes_br))
        if type(ax.yaxis.get_major_formatter()) is mticker.ScalarFormatter:
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(numero_br))


def pasta_graficos():
    """../graficos dentro do repositorio; graficos/ quando o notebook roda fora
    dele (no Colab, a pasta de trabalho e /content e ../graficos nao existe)."""
    return "../graficos" if os.path.isdir("../graficos") else "graficos"


def salvar(fig, nome, dpi=150):
    """Formata os eixos (datas e numeros em portugues), ajusta o layout
    reservando o espaco do cabecalho e do rodape e grava o PNG em
    pasta_graficos(). Devolve o caminho gravado."""
    _formatar_eixos(fig)
    topo, rodape = getattr(fig, "_espaco_reservado", (0, 0))
    altura = fig.get_figheight()
    fig.tight_layout(rect=[0, rodape / altura, 1, 1 - topo / altura])

    pasta = pasta_graficos()
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, nome)
    fig.savefig(caminho, dpi=dpi)
    return caminho
