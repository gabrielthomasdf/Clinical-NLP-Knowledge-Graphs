# Auditoria dos dados clínicos no histórico público

Revisão local em 2026-11-03 do histórico alcançável por `main` até `afe00d1` (82 commits). Este documento registra o que foi verificado e as decisões ainda necessárias para o fork de portfólio. Não reproduz relatos clínicos.

## Inventário

| Caminho | Conteúdo e histórico | Observação |
| --- | --- | --- |
| `project1/data/raw/cases.csv` | 56 registros de 50 artigos, um blob histórico | Texto de artigos permanece no histórico; nem todo registro descreve um caso individual. |
| `project1/data/raw/metadata.csv` | 50 registros, um blob histórico | Autores, título, identificadores, link e licença por artigo. Dois registros não têm DOI, mas têm link PubMed. |
| `project1/data/processed/nodes.csv` e `edges.csv` | Duas versões de nós e uma de arestas | Conceitos e relações extraídos dos relatos. |
| `project1/output/nodes.csv` e `edges.csv` | Duas versões históricas de cada arquivo | Saídas antigas removidas da árvore atual, ainda acessíveis pelos commits. |
| `project1/assets/slides/Projeto 1 - NLP.pdf` | 15 páginas | Capturas incorporadas incluem um trecho de relato com data clínica exata. A captura do caso `PMC11368112_01` deriva de artigo marcado `CC BY-NC` nos metadados. |
| `project2_from_project1/annotations/entity-gold-v1/adjudication.jsonl` | 233 decisões, um blob histórico | IDs, votos e justificativas de adjudicação MCRC; não contém campo de texto integral do corpus. As justificativas podem citar frases clínicas curtas. |
| `project2_from_project1/reports/relatorio-estudo-reconhecimento-global-entidades.pdf` | 11 páginas | Relatório agregado; texto extraído sem PMCID, e-mail ou relato integral identificado. |
| `project2_from_project1/tests/fixtures/` | Exemplos sintéticos | Sem relato real identificado. |

Os arquivos `.scratch/` versionados no histórico de `main` inspecionado são especificações e tarefas Markdown. A árvore atual contém 324 arquivos rastreados. Diretórios `.scratch/` locais não rastreados foram deixados intactos.

## Origem e licenças registradas

Todos os 56 `case_id` têm `article_id` correspondente em `metadata.csv`, sem duplicatas e com link de origem. A distribuição por artigo é: 31 `CC BY`, 11 `CC BY-NC-SA` e 8 `CC BY-NC`. Por registro: 36, 12 e 8, respectivamente. A versão exata de cada licença não está registrada no CSV e ainda precisa ser confirmada nas páginas dos artigos antes de afirmar termos específicos. A [triagem local](project2_from_project1/annotations/external-multicare-v1/local-source-eligibility.json) já excluiu três registros do teste externo por não serem narrativas inequívocas de um único paciente; eles continuam no CSV bruto e no histórico.

O [registro original do MultiCaRe no Zenodo](https://zenodo.org/records/10079370) descreve os relatos como de acesso aberto e desidentificados e aponta `metadata.parquet` como fonte da citação por artigo. A licença MIT da raiz cobre o código e a documentação próprios do grupo; os textos de artigos continuam sujeitos aos termos das fontes. As licenças [CC BY-NC](https://creativecommons.org/licenses/by-nc/4.0/) e [CC BY-NC-SA](https://creativecommons.org/licenses/by-nc-sa/4.0/) exigem atribuição e restringem uso comercial; a segunda também impõe compartilhamento pela mesma licença a adaptações quando aplicável. Esses links explicam a família de licenças 4.0, não comprovam que todos os artigos usem essa versão.

Os metadados locais permitem atribuição por artigo, mas o README ainda não fornece um aviso de atribuição e de alterações ligado a cada relato ou derivado. Um portfólio público voltado a emprego cria uma questão de interpretação do termo `NonCommercial`; a auditoria não resolve essa questão. O [aviso do PubMed Central](https://pmc.ncbi.nlm.nih.gov/about/copyright/) recomenda conferir a licença no registro de cada artigo e lembra que acesso aberto não elimina outros direitos.

## Sinais de identificação

Foi feita uma busca em todos os 56 textos brutos por e-mail, telefone, endereço postal, data de nascimento, nome explicitamente apresentado como do paciente e número de prontuário/identificação. Nenhum desses padrões produziu um identificador direto confirmado. Os 13 **registros de linha** assinalados pela busca inicial eram falsos positivos de palavras como `medical records`, `address`, `ms` e `phone`; o termo `initials` aparece em uma declaração genérica de consentimento, sem iniciais de paciente.

Quatro registros contêm datas clínicas exatas (`PMC7718649_01`, `PMC3557982_01`, `PMC11368112_01`, `PMC11345641_01`). Há relato que cita uma instituição e cidade. Datas, local, idade e doença rara podem funcionar como identificadores indiretos quando combinados. A busca por padrões e a revisão dirigida não certificam anonimato nem substituem uma avaliação de reidentificação. As capturas dos slides também carregam parte desse texto.

## Decisão para o fork

O histórico atual publica texto clínico de artigos marcados com restrição `NC` e seus derivados. Remover apenas os arquivos da versão mais recente não os elimina dos commits antigos. Há duas rotas técnicas:

1. **Preservar o histórico integral:** manter os relatos e derivados acessíveis, documentar atribuição, versão da licença e alterações por artigo e obter uma decisão informada sobre o uso pretendido dos itens `NC`/`NC-SA`.
2. **Publicar uma história limpa com dados sintéticos:** retirar os arquivos clínicos e capturas do histórico público com reescrita de commits; preservar autores, datas e referência ao repositório acadêmico original, mas os hashes dos commits reescritos mudam. Uma simples exclusão em `main` não atende a esse objetivo.

Nenhuma reescrita de histórico, exclusão de arquivos ou alteração do fork remoto foi feita nesta auditoria. Antes de escolher a rota, resta conferir a licença e a atribuição diretamente nos 50 artigos, especialmente os 19 marcados `NC`/`NC-SA`, e decidir se o objetivo do fork permite manter esses materiais públicos.
