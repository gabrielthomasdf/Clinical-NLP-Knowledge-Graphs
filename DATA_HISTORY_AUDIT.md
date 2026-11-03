# Auditoria e limpeza dos dados clínicos no histórico público

Revisão local concluída em 2026-11-03. Foram inspecionados os 85 commits que formavam `main` antes da publicação da história limpa. Este documento registra o inventário, os sinais de identificação encontrados e a decisão aplicada ao fork. Não reproduz relatos clínicos.

## Resultado da limpeza

Os caminhos abaixo foram retirados de todos os commits públicos, e não apenas da árvore atual:

| Caminho removido | Motivo |
| --- | --- |
| `project1/data/raw/cases.csv` | 56 registros com texto de 50 artigos MultiCaRe, incluindo artigos com restrição `NC` ou `NC-SA`. |
| `project1/data/processed/nodes.csv` e `edges.csv` | Conceitos e relações derivados dos relatos. |
| `project1/output/nodes.csv` e `edges.csv` | Versões históricas das saídas derivadas. |
| `project1/assets/slides/Projeto 1 - NLP.pdf` | Capturas com trechos de artigos e uma data clínica exata. |
| `project2_from_project1/annotations/entity-gold-v1/adjudication.jsonl` | Decisões de adjudicação cujas justificativas podiam conter frases clínicas curtas do MCRC. |

A reescrita preservou autores, datas, mensagens e a ordem dos commits que permaneceram, mas alterou seus hashes. Um bundle privado do estado anterior foi guardado localmente e não deve ser publicado. Regras no `.gitignore` reduzem o risco de reintroduzir esses artefatos.

Permanecem públicos os metadados bibliográficos e de licença, vocabulários, testes sintéticos, código, documentação própria e relatórios agregados nos quais não foi identificado relato integral. `project1/data/raw/metadata.csv` contém autores, título, identificadores, links e licença por artigo. `DATA_LICENSE_EVIDENCE.json` contém apenas evidências de licença.

## Origem e licenças registradas

Todos os 56 registros usados no trabalho acadêmico tinham artigo correspondente em `metadata.csv`, sem duplicatas e com link de origem. A distribuição por artigo é: 31 `CC BY`, 11 `CC BY-NC-SA` e 8 `CC BY-NC`. Por registro: 36, 12 e 8, respectivamente.

O script [`project1/scripts/audit_article_licenses.py`](project1/scripts/audit_article_licenses.py) consultou o XML público dos 50 artigos no Europe PMC. As 50 famílias de licença conferiram com os metadados: 29 por URL Creative Commons e 21 pelo aviso textual. A versão foi identificada em 38 artigos; em 12, o aviso consultado não especifica versão. O XML foi lido em memória e não foi salvo.

```bash
python -m project1.scripts.audit_article_licenses --output project2_from_project1/artifacts/article-license-audit.json --public-output DATA_LICENSE_EVIDENCE.json
```

O [MultiCaRe no Zenodo](https://zenodo.org/records/10079370) descreve os relatos como de acesso aberto e desidentificados. A licença MIT da raiz cobre o código e a documentação próprios do grupo; textos de artigos continuam sujeitos aos termos de cada fonte. O [guia de atribuição](DATA_ATTRIBUTION.md) registra a proveniência sem redistribuir os textos.

## Sinais de identificação observados antes da limpeza

Uma busca nos 56 textos procurou e-mail, telefone, endereço postal, data de nascimento, nome explicitamente apresentado como do paciente e número de prontuário ou identificação. Nenhum identificador direto foi confirmado. Os 13 registros de linha assinalados pela busca inicial eram falsos positivos de termos como `medical records`, `address`, `ms` e `phone`.

Quatro registros continham datas clínicas exatas (`PMC7718649_01`, `PMC3557982_01`, `PMC11368112_01`, `PMC11345641_01`), e um relato citava instituição e cidade. Datas, local, idade e doença rara podem funcionar como identificadores indiretos quando combinados. Essa constatação, junto às condições `NC` e `NC-SA`, motivou a remoção preventiva do texto e dos derivados do fork público.

## Política para novas contribuições

- Use relatos sintéticos, fictícios ou públicos com licença conferida nos exemplos versionados.
- Mantenha corpora adquiridos, modelos e saídas com texto clínico nos caminhos ignorados.
- Registre origem, licença, hash e partição por documento nos experimentos.
- Antes de publicar um novo artefato, verifique se ele reproduz texto, offsets, justificativas ou capturas das fontes.
