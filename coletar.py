"""Coletor dos dados abertos de Pix do BCB (plataforma Olinda).

Uso: python coletar.py <tabela>
"""
import json
import sys
import urllib.error
import urllib.request
from datetime import date

BASE = "https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata"

# (entidade, nome do parametro de data) — o parametro varia entre entidades
TABELAS = {
    "fraude": ("EstatisticasFraudesPix", "Database"),
    "transacoes": ("EstatisticasTransacoesPix", "Database"),
    "municipio": ("TransacoesPixPorMunicipio", "DataBase"),
    "cnae": ("CnaePorteRecebedor", "Database"),
}


def requisitar(url, timeout=30):
    """Faz um GET e devolve (status, corpo). Nunca levanta excecao."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resposta:
            return resposta.status, resposta.read().decode("utf-8")
    except urllib.error.HTTPError as erro:
        return erro.code, erro.read().decode("utf-8", errors="replace")
    except OSError:
        return None, None


def desembrulhar(corpo):
    """Remove o comentario /* ... */ que embrulha a resposta da Olinda.

    Devolve None se o corpo estiver vazio ou nao for JSON valido (ex: HTML
    de pagina de erro).
    """
    if not corpo:
        return None

    texto = corpo
    if texto.lstrip().startswith("/*"):
        fim = texto.find("*/")
        if fim != -1:
            texto = texto[fim + 2 :]

    try:
        return json.loads(texto)
    except (json.JSONDecodeError, ValueError):
        return None


def montar_url(entidade, parametro, valor):
    """Monta a URL no formato exigido pela Olinda: Entidade(Param=@Param)."""
    return (
        f"{BASE}/{entidade}({parametro}=@{parametro})"
        f"?@{parametro}='{valor}'&$format=json"
    )


def gerar_meses(desde, ate=None):
    """Lista de AAAAMM de `desde` ate `ate`, inclusive, mes a mes.

    `ate` default: mes corrente.
    """
    if ate is None:
        hoje = date.today()
        ate = hoje.year * 100 + hoje.month

    ano, mes = divmod(desde, 100)
    fim_ano, fim_mes = divmod(ate, 100)

    meses = []
    while (ano, mes) <= (fim_ano, fim_mes):
        meses.append(ano * 100 + mes)
        mes += 1
        if mes > 12:
            mes = 1
            ano += 1
    return meses


def main(argv):
    raise NotImplementedError("etapa 1")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
