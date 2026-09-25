"""Coletor dos dados abertos de Pix do BCB (plataforma Olinda).

Uso: python coletar.py <tabela>
"""
import sys
import urllib.error
import urllib.request

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


def main(argv):
    raise NotImplementedError("etapa 1")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
