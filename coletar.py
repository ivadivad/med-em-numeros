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

# tabelas grandes demais pra versionar linha a linha: o coletor soma estas
# colunas por mes e grava so o total. EstatisticasTransacoesPix tem dezenas
# de milhares de linhas por mes (uma por combinacao de PF/PJ, regiao, idade,
# forma de iniciacao, natureza e finalidade) — centenas de MB no total.
AGREGAR = {
    "transacoes": ("VALOR", "QUANTIDADE"),
}

# coluna(s) que identificam uma linha de forma unica, por tabela — usado ao
# mesclar a coleta nova com o consolidado ja existente: na colisao, fica a
# versao mais recente (meses recentes sao revisados pelo BCB). Tabelas sem
# entrada aqui caem no fallback: deduplicar pelo conteudo inteiro da linha.
# "transacoes" so pode usar AnoMes porque ja chega agregada (ver AGREGAR);
# a tabela crua tem varias linhas por mes.
CHAVE_UNICA = {
    "fraude": ("AnoMes",),
    "transacoes": ("AnoMes",),
}

# tabelas em que $filter=AnoMes eq AAAAMM foi confirmado. Na de fraude nao
# deu pra testar: desde 06/10/2026 a API devolve 500 em qualquer consulta a
# essa tabela que tenha linha pra devolver, com ou sem filtro (so meses vazios
# respondem). Fica a consulta sem filtro, a unica comprovada nela — cada
# consulta traz todos os meses a partir do pedido, o que pra fraude (uma linha
# por mes) e inofensivo e ainda da redundancia. municipio e cnae: nao testadas.
FILTRO_MES = {"transacoes"}

TENTATIVAS = 3
ESPERA_BASE = 1  # segundos; cresce a cada nova tentativa


def requisitar(url, timeout=120):
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


def montar_url(entidade, parametro, valor, filtrar_mes=False):
    """Monta a URL no formato exigido pela Olinda: Entidade(Param=@Param).

    O parametro sozinho devolve todos os meses a partir de `valor`, nao so
    ele; `filtrar_mes` acrescenta $filter pra restringir ao mes exato — so
    funciona em algumas tabelas (ver FILTRO_MES).
    """
    filtro = f"&$filter=AnoMes%20eq%20{valor}" if filtrar_mes else ""
    return (
        f"{BASE}/{entidade}({parametro}=@{parametro})"
        f"?@{parametro}='{valor}'{filtro}&$format=json"
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

    situacao: "ok", "vazio", "erro_400", "erro_500" (o servidor respondeu com
    erro em todas as tentativas), "falha_rede" (nem chegou resposta: timeout ou
    conexao recusada) ou "erro_<codigo>" pra qualquer outro status. Separar
    500 de falha de rede importa: uma e problema do BC, a outra da sua conexao.
    Reentrega em 500 e em falha de rede, com espera crescente. Erro 400 nao
    reentrega, porque parametro errado nao melhora tentando de novo.
    """
    entidade, parametro = TABELAS[tabela]
    url = montar_url(entidade, parametro, mes, filtrar_mes=tabela in FILTRO_MES)

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

        return [], ("falha_rede" if status is None else f"erro_{status}")

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


def agregar_por_mes(linhas, colunas_soma):
    """Soma `colunas_soma` por AnoMes. Uma linha por mes, mais `LinhasOrigem`.

    `LinhasOrigem` conta quantas linhas cruas entraram em cada total — se
    muitos meses derem o mesmo numero redondo, a API provavelmente cortou a
    resposta.
    """
    totais = {}
    for linha in linhas:
        mes = int(linha["AnoMes"])
        total = totais.setdefault(mes, {"AnoMes": mes, **{c: 0 for c in colunas_soma}, "LinhasOrigem": 0})
        for coluna in colunas_soma:
            total[coluna] += linha.get(coluna) or 0
        total["LinhasOrigem"] += 1

    for total in totais.values():
        for coluna in colunas_soma:
            if isinstance(total[coluna], float):
                total[coluna] = round(total[coluna], 2)
    return list(totais.values())


def coletar_tabela(tabela, desde=None):
    """Varre todos os meses de uma tabela. Devolve (linhas, cobertura).

    Tabelas em AGREGAR sao somadas mes a mes, logo apos cada consulta, pra
    nao manter milhoes de linhas cruas em memoria. A cobertura registra
    sempre o numero de linhas cruas que a API devolveu.
    """
    desde = desde or DESDE_PADRAO[tabela]
    linhas_totais = []
    cobertura = {}
    for mes in gerar_meses(desde):
        linhas, situacao = coletar_mes(tabela, mes)
        cobertura[mes] = (len(linhas), situacao)
        if tabela in AGREGAR:
            linhas = agregar_por_mes(linhas, AGREGAR[tabela])
        linhas_totais.extend(linhas)
    return deduplicar(linhas_totais, CHAVE_UNICA.get(tabela)), cobertura


def ler_csv(caminho):
    """Le um CSV consolidado ja existente. Arquivo ausente vira lista vazia."""
    if not os.path.exists(caminho):
        return []
    with open(caminho, newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def consolidar(existentes, novas, colunas_chave=None):
    """Mescla a coleta nova com o consolidado existente, ordenado por AnoMes.

    Na colisao de chave, a linha nova vence (mes revisado pelo BCB). Meses
    que so existem no consolidado sao mantidos — uma rodada em que a API
    falhou num mes nao apaga o que ja tinha sido coletado antes.
    """
    linhas = deduplicar(existentes + novas, colunas_chave)
    return sorted(linhas, key=lambda linha: int(linha.get("AnoMes") or 0))


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
    """Grava um retrato datado da coleta. Nunca sobrescreve um ja existente.

    Coleta vazia nao vira snapshot: como o do dia nunca e sobrescrito, um
    snapshot vazio de uma rodada que falhou bloquearia o certo ate o dia
    seguinte. Devolve None nesse caso.
    """
    if not linhas:
        return None
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

    caminho = f"dados/{args.tabela}.csv"
    novas, cobertura = coletar_tabela(args.tabela, args.desde)
    consolidado = consolidar(ler_csv(caminho), novas, CHAVE_UNICA.get(args.tabela))

    gravar_csv(consolidado, caminho)
    gravar_snapshot(novas, args.tabela)
    gravar_cobertura(cobertura, f"dados/{args.tabela}_cobertura.csv")

    meses_ok = sum(1 for _, situacao in cobertura.values() if situacao == "ok")
    print(
        f"{args.tabela}: {meses_ok}/{len(cobertura)} meses ok nesta coleta, "
        f"{len(novas)} linhas novas, {len(consolidado)} linhas no consolidado"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
