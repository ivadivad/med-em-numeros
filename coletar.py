"""Coletor dos dados abertos de Pix do BCB (plataforma Olinda).

Uso: python coletar.py <tabela>

Etapa 1 do PLANO.md — a implementar.
"""
import sys

BASE = "https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata"

# (entidade, nome do parametro de data) — o parametro varia entre entidades
TABELAS = {
    "fraude": ("EstatisticasFraudesPix", "Database"),
    "transacoes": ("EstatisticasTransacoesPix", "Database"),
    "municipio": ("TransacoesPixPorMunicipio", "DataBase"),
    "cnae": ("CnaePorteRecebedor", "Database"),
}


def main(argv):
    raise NotImplementedError("etapa 1")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
