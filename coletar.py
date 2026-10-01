"""Coletor dos dados abertos de Pix do BCB (plataforma Olinda).

Uso: python coletar.py <tabela>
"""
import argparse
import csv
import json
import os
import sys
import time
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

# primeiro mes com dado disponivel, por tabela
DESDE_PADRAO = {
    "fraude": 202201,
    "transacoes": 202011,
    "municipio": 202011,
    "cnae": 202011,
}

# coluna(s) que identificam uma linha de forma unica, por tabela — usado na
# deduplicacao. A Olinda devolve, numa unica consulta, todos os meses a
# partir do parametro pedido (nao so aquele mes); por isso o mesmo mes pode
# vir embutido em mais de uma consulta do sweep, e em meses recentes (ainda
# sendo atualizados pelo BCB) os valores podem divergir entre uma consulta e
# outra feitas na mesma coleta. Tabelas sem entrada aqui caem no fallback:
# deduplicar pelo conteudo inteiro da linha.
CHAVE_UNICA = {
    "fraude": ("AnoMes",),
    "transacoes": ("AnoMes",),
}

TENTATIVAS = 3
ESPERA_BASE = 1  # segundos; cresce a cada nova tentativa


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


def coletar_mes(tabela, mes):
    """Busca os dados de um mes. Devolve (linhas, situacao).

    situacao: "ok", "vazio", "erro_400" ou "falha_rede".
    Reentrega em erro 500 e em falha de rede (status None — timeout ou conexao
    recusada), com espera crescente. Erro 400 nao reentrega, porque parametro
    errado nao melhora tentando de novo.
    """
    entidade, parametro = TABELAS[tabela]
    url = montar_url(entidade, parametro, mes)

    for tentativa in range(TENTATIVAS):
        status, corpo = requisitar(url)

        if status == 400:
            return [], "erro_400"

        if status == 200:
            dados = desembrulhar(corpo)
            linhas = dados.get("value", []) if dados else []
            return linhas, ("ok" if linhas else "vazio")

        if status in (500, None) and tentativa < TENTATIVAS - 1:
            time.sleep(ESPERA_BASE * (tentativa + 1))
            continue

        return [], "falha_rede"

    return [], "falha_rede"


def _normalizar(valor):
    """None e "" contam como iguais; tudo vira texto pra comparar.

    A API devolve AnoMes como número, o CSV relido devolve como texto.
    Sem normalizar, o consolidado dobra a cada rodada.
    """
    if valor is None or valor == "":
        return ""
    return str(valor)


def impressao_digital(linha, colunas):
    """Chave unica a partir do conteudo da linha, insensivel a tipo.

    `colunas` vem de fora (a uniao de todas as linhas do lote) para que uma
    coluna ausente e uma coluna vazia gerem a mesma chave.
    """
    return tuple(_normalizar(linha.get(coluna)) for coluna in sorted(colunas))


def deduplicar(linhas, colunas_chave=None):
    """Remove linhas repetidas. Fica a ultima ocorrencia de cada chave.

    Sem `colunas_chave`, a chave e o conteudo inteiro da linha (duas linhas
    so colidem se forem identicas). Com `colunas_chave`, a chave e so essas
    colunas — util quando a mesma linha pode vir com valores levemente
    diferentes em consultas diferentes (ver `CHAVE_UNICA`).
    """
    colunas = set()
    for linha in linhas:
        colunas.update(linha)

    vistas = {}
    for linha in linhas:
        chave = impressao_digital(linha, colunas_chave or colunas)
        vistas[chave] = linha
    return list(vistas.values())


def coletar_tabela(tabela, desde=None):
    """Varre todos os meses de uma tabela. Devolve (linhas, cobertura)."""
    desde = desde or DESDE_PADRAO[tabela]
    linhas_totais = []
    cobertura = {}
    for mes in gerar_meses(desde):
        linhas, situacao = coletar_mes(tabela, mes)
        cobertura[mes] = (len(linhas), situacao)
        linhas_totais.extend(linhas)
    return deduplicar(linhas_totais, CHAVE_UNICA.get(tabela)), cobertura


def gravar_csv(linhas, caminho):
    """Grava o CSV consolidado. Colunas: uniao de todas as linhas, sem perder campo."""
    colunas = []
    vistas = set()
    for linha in linhas:
        for chave in linha:
            if chave not in vistas:
                vistas.add(chave)
                colunas.append(chave)

    os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
    with open(caminho, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()
        escritor.writerows(linhas)


def gravar_snapshot(linhas, tabela, pasta="dados/snapshots", hoje=None):
    """Grava um retrato datado da coleta. Nunca sobrescreve um ja existente."""
    hoje = hoje or date.today().isoformat()
    caminho = os.path.join(pasta, f"{tabela}_{hoje}.json")
    if os.path.exists(caminho):
        return caminho

    os.makedirs(pasta, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(linhas, arquivo, ensure_ascii=False, indent=2)
    return caminho


def gravar_cobertura(cobertura, caminho):
    """Grava quais meses existem, quantas linhas e a situacao de cada um."""
    os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
    with open(caminho, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["AnoMes", "linhas", "situacao"])
        for mes, (qtde, situacao) in sorted(cobertura.items()):
            escritor.writerow([mes, qtde, situacao])


def main(argv):
    parser = argparse.ArgumentParser(description="Coletor de dados abertos de Pix do BCB")
    parser.add_argument("tabela", nargs="?", choices=sorted(TABELAS), help="tabela a coletar")
    parser.add_argument("--desde", type=int, help="mes inicial, formato AAAAMM")
    parser.add_argument("--listar", action="store_true", help="lista as tabelas disponiveis e sai")
    args = parser.parse_args(argv)

    if args.listar or not args.tabela:
        for nome, (entidade, parametro) in TABELAS.items():
            print(f"{nome:12} {entidade} (@{parametro}, desde {DESDE_PADRAO[nome]})")
        return 0

    linhas, cobertura = coletar_tabela(args.tabela, args.desde)
    gravar_csv(linhas, f"dados/{args.tabela}.csv")
    gravar_snapshot(linhas, args.tabela)
    gravar_cobertura(cobertura, f"dados/{args.tabela}_cobertura.csv")

    meses_ok = sum(1 for _, situacao in cobertura.values() if situacao == "ok")
    print(f"{args.tabela}: {len(linhas)} linhas em {meses_ok}/{len(cobertura)} meses")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
