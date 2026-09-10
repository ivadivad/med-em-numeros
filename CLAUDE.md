# Contexto do projeto

Este arquivo é lido automaticamente pelo Claude Code. Ele resume o projeto, o
estado atual e — importante — **como o Davi quer trabalhar**.

---

## O que é

Análise dos dados abertos do **MED (Mecanismo Especial de Devolução)**, o sistema
do Banco Central que devolve dinheiro a vítimas de golpe no Pix.

**Pergunta central:** quanto do valor contestado volta para a vítima, e quando
não volta, por quê?

- Repositório: `https://github.com/ivadivad/med-em-numeros`
- Fonte: [Dados Abertos do BCB — Pix](https://dadosabertos.bcb.gov.br/dataset/pix)
- Objetivo: **primeiro projeto de portfólio** de um analista de dados iniciante

---

## Como o Davi quer trabalhar

**Leia esta seção antes de qualquer outra coisa.** A sessão anterior errou aqui.

1. **É um projeto de aprendizado.** O objetivo não é o resultado, é o Davi
   aprender pandas, análise e git no caminho. Entregar análise pronta destrói o
   propósito.
2. **Não escreva a análise por ele.** Explique conceitos, revise o que ele fez,
   aponte erro, sugira o próximo passo. Não produza o notebook pronto.
3. **Publicação gradual.** Cada etapa do `PLANO.md` vira um commit próprio. O
   histórico do repositório é parte do entregável.
4. **Notebooks no Google Colab**, com gráficos em pandas/matplotlib. Eles leem o
   CSV pela URL bruta do GitHub, para rodarem em qualquer máquina.
5. **Seja direto e pouco verboso.** Ele pediu isso várias vezes.
6. **Sinalize erro próprio.** Ele valoriza correção honesta mais que confiança.

---

## Estado atual

O repositório existe, tem remote configurado e o README commitado. A estrutura
completa de arquivos já está no disco, mas **ainda não commitada**.

```
med-em-numeros/
├── README.md              pronto
├── PLANO.md               13 etapas detalhadas — o roteiro do projeto
├── DICIONARIO.md          esqueleto: 24 colunas listadas, descrições em branco
├── CLAUDE.md              este arquivo
├── LICENSE                MIT — PENDENTE: falta o nome no copyright
├── .gitignore
├── requirements.txt       pandas, matplotlib (só para os notebooks)
├── coletar.py             coletor da API, sem dependência externa
├── teste_coletar.py       26 testes, todos passando
├── descobrir_api.py       script que mapeou a API (já cumpriu a função)
├── visual.py              esqueleto da função grafico() — etapa 10
├── dados/                 VAZIO — rodar `python coletar.py fraude`
├── graficos/              vazio
└── notebooks/             7 esqueletos válidos, com objetivo e checklist
```

### Pendências imediatas

1. Preencher o nome no `LICENSE`
2. Rodar `python coletar.py fraude` para popular `dados/`
3. Criar `.github/workflows/atualizar.yml` — só na etapa 12 (o conteúdo está no
   fim deste arquivo)
4. Fazer o primeiro commit da estrutura

---

## Conhecimento técnico da API

Isto custou várias horas para descobrir. **Não redescubra.**

A API roda na plataforma Olinda, do BCB. Base:

```
https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata
```

### Armadilhas

| Comportamento | Detalhe |
|---|---|
| Entidades exigem parâmetro | `EstatisticasFraudesPix?$format=json` devolve `400 The URI is malformed`. A sintaxe é `Entidade(Param=@Param)?@Param='AAAAMM'&$format=json` |
| Nome do parâmetro varia | `TransacoesPixPorMunicipio` usa `DataBase` (B maiúsculo). As demais usam `Database`. `ChavesPix` usa `Data` |
| JSON embrulhado | A resposta vem entre `/*` e `*/`. Quebra `json.loads` direto |
| Parâmetro nem sempre filtra | Alguns endpoints devolvem meses diferentes do pedido. **A verdade é o campo `AnoMes` de dentro da linha**, nunca o valor enviado. Por isso o coletor deduplica pelo conteúdo |
| Entidades com `_` não funcionam | `_EstatisticasFraudesPix` aparece no catálogo mas devolve 500 |
| Defasagem real | A documentação diz 30 dias após o fim do mês. Na prática são ~4 meses |
| Bloqueio a ferramenta automatizada | O domínio recusa acesso de fora do navegador em algumas ferramentas. `urllib` do Python funciona normalmente |

### Tabelas disponíveis

| Apelido no coletor | Entidade | Parâmetro | Desde |
|---|---|---|---|
| `fraude` | `EstatisticasFraudesPix` | `Database` | 202201 |
| `transacoes` | `EstatisticasTransacoesPix` | `Database` | 202011 |
| `municipio` | `TransacoesPixPorMunicipio` | `DataBase` | 202011 |
| `cnae` | `CnaePorteRecebedor` | `Database` | 202011 |

`CnaePorteRecebedor` traz Pix por setor econômico e porte de empresa. É
pouquíssimo explorada e daria um segundo projeto inteiro.

### Design do coletor

- Só biblioteca padrão, para rodar no GitHub Actions sem instalar nada
- Varre mês a mês desde o início e descobre empiricamente quais existem
- Deduplica por impressão digital da linha, com tudo normalizado para texto
  (a API devolve `202601` como número, o CSV devolve `"202601"` como texto; sem
  normalizar, o consolidado dobrava a cada rodada — foi bug real, pego em teste)
- Campo ausente e campo vazio contam como iguais, para o dia em que o BCB
  acrescentar uma coluna
- Grava snapshot datado em `dados/snapshots/`, nunca sobrescrito, além do
  consolidado

---

## O que já se sabe dos dados

> **Atenção.** A sessão anterior fez uma análise exploratória rápida e entregou
> as conclusões prontas — o que atrapalhou o aprendizado. O Davi pediu para
> refazer o caminho por conta.
>
> **Use o que está abaixo apenas para conferir o trabalho dele, nunca para
> adiantar resposta.** Se ele chegar a número diferente, investiguem juntos.

Base: 52 meses, jan/2022 a abr/2026, sem lacunas e sem duplicatas.

- `PercentualdeDevolucao` = (devolvido integral + parcial) / contestado aceito.
  Confere em 52/52 meses, erro 0,0000
- Agregado do período: 9,00% (R$ 24,52 bi contestados, R$ 2,21 bi devolvidos).
  A reportagem do O Povo publicou 8,9% para o mesmo intervalo
- Out/2025: contestações passam de ~1,29 mi/mês para ~3,23 mi/mês; taxa de
  aceite cai de 27,9% para 9,4%
- 2026 (4 meses): devolução média 14,53%, contra 8,55% em 2024–2025. Os quatro
  meses superam o máximo dos 24 anteriores
- Motivo dominante da não devolução: saldo insuficiente, 83,9% do valor

### Linha do tempo regulatória

| Data | Mudança |
|---|---|
| 1º/out/2025 | Contestação passa a ser 100% digital, no app, sem ligar para o banco |
| 23/nov/2025 | Devolução a partir de outras contas (rastreio do dinheiro) — opcional |
| fev/2026 | A mesma regra vira obrigatória |
| 1º/set/2026 | Prazo de contestação sobe de 30 para 80 dias |

### Lacuna importante, e ela é do Davi

**Ninguém normalizou a fraude pelo volume total de Pix.** As contestações
triplicaram, mas o Pix também cresceu. Sem dividir pelo total transacionado, não
dá para afirmar que a fraude piorou. É a etapa 7 do plano e a mais valiosa do
projeto. Não faça por ele.

---

## Próximos passos

Ver `PLANO.md` para o detalhe de cada etapa. Resumo:

| Etapa | O que é |
|---|---|
| 0–1 | Estrutura e coletor — **quase pronto, falta commitar** |
| 2 | Primeiro contato com os dados, preencher o `DICIONARIO.md` |
| 3 | Validar a base: recalcular o percentual e reproduzir número publicado |
| 4–5 | Primeiros gráficos e volume de contestações |
| 6 | Contexto regulatório: explicar a quebra com fonte externa |
| 7 | **Normalização pelo volume de Pix** — a mais importante |
| 8 | Decomposição dos motivos de não devolução |
| 9 | Comparação entre períodos, com as ressalvas explícitas |
| 10 | Função `grafico()` padronizando o visual |
| 11 | README final com a história |
| 12 | GitHub Actions mensal |

---

## Limitações da base

Valem para qualquer conclusão do projeto:

- Quem julga a contestação é a própria instituição contestada, e mais da metade
  dos pedidos é descartada. "Fraude" aqui é fraude que a instituição reconheceu
- Golpes não contestados não aparecem em lugar nenhum
- Sem recorte por instituição ou município — é agregado nacional mensal
- Antes e depois não é inferência causal

---

## Anexo: `.github/workflows/atualizar.yml`

Criar só na etapa 12, quando `dados/` já estiver populado.

```yaml
name: atualizar dados do Pix

on:
  schedule:
    - cron: "0 9 5 * *"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  coletar:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Coletar
        run: python coletar.py fraude
      - name: Commit do que mudou
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add dados/
          if git diff --staged --quiet; then
            echo "nada novo neste mes"
          else
            git commit -m "dados: coleta de $(date -u +%Y-%m-%d)"
            git push
          fi
```
