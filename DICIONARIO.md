# Dicionário de dados

Descrição das colunas da tabela `EstatisticasFraudesPix`, do Portal de Dados
Abertos do Banco Central.

> Preenchido na etapa 2, a partir do nome de cada coluna, do domínio do MED e
> de checagens diretas em cima dos dados reais coletados (`dados/fraude.csv`,
> 52 meses, jan/2022 a abr/2026). Onde uma checagem confirmou uma relação
> entre colunas, está registrado. Onde ficou dúvida genuína, está em
> "Perguntas em aberto" em vez de um palpite escrito como se fosse certeza.

## Chave

| Coluna | Tipo | Descrição |
|---|---|---|
| `AnoMes` | Int32 | Mês de referência no formato AAAAMM. Chave única da tabela — uma linha por mês. |

## Contestações

| Coluna | Tipo | Descrição |
|---|---|---|
| `QtdePixcontestados` | Decimal | Quantidade de transações Pix contestadas no mês — o usuário alega ter sido vítima de golpe e pede abertura do MED. **Confirmado nos dados:** é exatamente a soma de `Qtdecontestacoesaceitas` + `Qtdecontestacoesrejeitadas` nos 52 meses, sem exceção. |
| `Qtdecontestacoesaceitas` | Decimal | Quantidade de contestações aceitas pela instituição do recebedor — ela reconhece indício de fraude e segue com o processo do MED. |
| `Qtdecontestacoesrejeitadas` | Decimal | Quantidade de contestações negadas pela instituição do recebedor. |
| `Qtdecontestacoesaceitasacada100mil` | Decimal | Taxa de contestações aceitas a cada 100 mil — provavelmente transações Pix do mês, mas a API não declara o denominador e não achei como derivá-lo só com esta tabela. Ver "perguntas em aberto". |
| `QtdeUsuarioscommarcacoesdefraude` | Decimal | Quantidade de usuários (CPF/CNPJ) com pelo menos uma marcação de fraude no mês. |
| `QtdeChavesPixcommarcacoesdefraude` | Decimal | Quantidade de chaves Pix (CPF, e-mail, telefone, celular, aleatória) associadas a alguma marcação de fraude no mês. Em todos os meses é um pouco maior que `QtdeUsuarioscommarcacoesdefraude`, o que faz sentido: uma pessoa pode ter mais de uma chave. |
| `ValorPixcontestadosaceitos` | Decimal | Soma em reais do valor das transações cuja contestação foi aceita no mês. Varia de ~R$ 123 milhões a ~R$ 860 milhões por mês no período coletado. |

## Devoluções

| Coluna | Tipo | Descrição |
|---|---|---|
| `QuantidadedevolvidaintegralmentepormeiodoMED` | Decimal | Quantidade de casos em que o valor contestado foi devolvido 100% à vítima via MED. |
| `ValorPixdevolvidosintegralmente` | Decimal | Valor em reais devolvido integralmente. |
| `QuantidadedevolvidaparcialmentepormeiodoMED` | Decimal | Quantidade de casos com devolução parcial — provavelmente quando só parte do saldo ainda estava disponível na conta de destino no momento do bloqueio. |
| `ValorPixdevolvidosparcialmente` | Decimal | Valor em reais devolvido parcialmente. |
| `PercentualdeDevolucao` | Decimal | Coluna derivada. Varia de 2,86% a 16,23% no período, média 8,72%. **Fórmula confirmada na etapa 3** (`notebooks/02-validacao.ipynb`): `(ValorPixdevolvidosintegralmente + ValorPixdevolvidosparcialmente) / ValorPixcontestadosaceitos × 100`. Erro máximo de 0,0049 ponto percentual nos 52 meses — é sobre valor, não quantidade de casos, e o denominador é o valor já **aceito**, não o total solicitado antes do crivo da instituição. |

## Não devolvidos, por motivo

| Coluna | Tipo | Descrição |
|---|---|---|
| `ValorPixresidualnaodevolvido` | Decimal | Valor em reais que **não voltou dos casos devolvidos só em parte** — a diferença entre o contestado e o devolvido nesses casos. Não tem motivo associado. **Confirmado na etapa 8** (`notebooks/06-motivos-nao-devolucao.ipynb`) pela identidade abaixo, que fecha com erro R$ 0 nos 52 meses: `ValorPixcontestadosaceitos = devolvido integral + devolvido parcial + residual + saldo insuficiente + conta encerrada + motivos diversos`. |
| `Quantidadedenaodevolvidossaldoinsuficiente` | Decimal | Quantidade de casos não devolvidos porque a conta de destino já não tinha saldo suficiente no momento do bloqueio — o motivo que mais pesa em valor, segundo análises anteriores deste mesmo projeto. |
| `ValorPixnaodevolvidossaldoinsuficiente` | Decimal | Valor correspondente, em reais. |
| `Quantidadedenaodevolvidoscontaencerrada` | Decimal | Quantidade de casos não devolvidos porque a conta de destino já tinha sido encerrada antes do bloqueio. |
| `Valornaodevolvidoscontaencerrada` | Decimal | Valor correspondente, em reais. |
| `Quantidadedenaodevolvidosmotivosdiversos` | Decimal | Quantidade de casos não devolvidos por motivos que não se encaixam nas duas categorias acima (catch-all). Ver "perguntas em aberto" — o que exatamente cai aqui continua sem fonte oficial encontrada. |
| `ValorPixnaodevolvidosmotivosdiversos` | Decimal | Valor correspondente, em reais. Os três valores de motivo (`saldo insuficiente` + `conta encerrada` + `motivos diversos`) somados são o valor dos casos em que **nada** voltou — não a decomposição do residual (ver identidade em `ValorPixresidualnaodevolvido`). |

## Bloqueio cautelar

| Coluna | Tipo | Descrição |
|---|---|---|
| `QtdePixbloqueadoscautelarmenteeliberados` | Decimal | Quantidade de Pix bloqueados cautelarmente (por suspeita de fraude, antes de qualquer contestação formal) e depois liberados — a leitura mais provável é que a apuração não confirmou fraude e o valor seguiu seu curso normal, não necessariamente para a vítima. Não confirmado em documentação oficial. |
| `ValorPixbloqueadoscautelarmenteeliberados` | Decimal | Valor correspondente, em reais. É a coluna de maior variação da tabela: de ~R$ 18 milhões a ~R$ 5,5 bilhões num único mês. |
| `QtdePixbloqueadoscautelarmenteedevolvidos` | Decimal | Quantidade de Pix bloqueados cautelarmente e devolvidos — aqui a apuração aparentemente confirmou a fraude e o valor retornou à vítima. Mesma ressalva: leitura pelo nome da coluna, não por documentação oficial. |
| `ValorPixbloqueadoscautelarmenteedevolvidos` | Decimal | Valor correspondente, em reais. |

---

## Perguntas em aberto

Anote aqui o que não ficou claro na documentação oficial. Uma boa análise começa
sabendo o que ela não sabe.

- ~~"Aceitas" e "rejeitadas" somam o total de contestadas em todos os meses?~~
  **Resolvido:** sim, exatamente, nos 52 meses coletados.
- Valor está em reais? A magnitude (centenas de milhões a bilhões por mês)
  é compatível com reais para o volume de Pix do Brasil, mas a API não
  declara a unidade em lugar nenhum que eu tenha encontrado.
- `Qtdecontestacoesaceitasacada100mil`: a cada 100 mil o quê? Transações Pix
  do mês? Chaves cadastradas? Não dá pra derivar só com esta tabela.
- ~~`ValorPixresidualnaodevolvido` não é explicado pelos três motivos somados
  nem por `contestado − devolvido`.~~ **Resolvido na etapa 8:** não faltava
  fonte de valor nenhuma — os dois são destinos diferentes do valor aceito.
  `aceito = devolvido integral + parcial + residual + os três motivos`, erro
  R$ 0 nos 52 meses. O palpite anterior (bloqueio cautelar) estava errado.
- Por que "conta encerrada" caiu de 13,5–28,7% do valor sem devolução em
  jan–jul/2022 para no máximo 5,6% a partir de ago/2022? Quebra nítida, causa
  não pesquisada (etapa 8).
- ~~Devolução parcial entra no numerador do percentual pelo valor devolvido ou
  pela quantidade de casos?~~ **Resolvido na etapa 3:** pelo valor — ver
  fórmula confirmada acima, em "Devoluções".
- O que exatamente cai em "motivos diversos"?
- Bloqueio cautelar "liberado" volta pro remetente, fica com quem recebeu, ou
  é outra coisa? A documentação da Olinda não detalha o fluxo.
