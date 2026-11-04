# Resultados reproduzidos nos folds de desenvolvimento

Em 2026-11-04, já na continuação individual do projeto, o estudo completo foi executado novamente sobre os **42 documentos de desenvolvimento** do MCRC. A execução terminou nos cinco folds externos e gerou entidades, relações e grafos para as quatro combinações fim a fim. A partição fixa de teste do MCRC não foi lida.

## Protocolo

- Cinco folds externos separados por documento.
- Seleção do CRF em três folds internos, também separados por documento.
- Grade de regularização L2: `0.01`, `0.1`, `1.0` e `10.0`.
- Limite de 250 iterações por ajuste.
- Entidades avaliadas por tipo e offsets exatos.
- Relações avaliadas por documento, endpoints e rótulo exatos.
- Médias e desvios padrão calculados entre os cinco folds externos.
- Nenhuma barreira de desempenho foi usada para retirar abordagens do relatório.

## Resultados

| Pipeline | Macro-F1 de entidades | Macro-F1 de relações | F1 de arestas conceituais |
| --- | ---: | ---: | ---: |
| Dicionário + regras | 0,1208 ± 0,0127 | 0,0404 ± 0,0069 | 0,0799 ± 0,0097 |
| Dicionário + k-NN | 0,1208 ± 0,0127 | 0,0632 ± 0,0095 | 0,1246 ± 0,0266 |
| CRF + regras | 0,2857 ± 0,0434 | 0,1364 ± 0,0314 | 0,1482 ± 0,0358 |
| CRF + k-NN | 0,2857 ± 0,0434 | 0,1555 ± 0,0382 | 0,2048 ± 0,0299 |

Os valores são média ± desvio padrão entre folds. O F1 de arestas conceituais é uma métrica secundária do grafo; as métricas estritas de entidades e relações continuam sendo as medidas principais das tarefas de extração.

O CRF selecionou L2 `0.1` nos folds 1, 2, 4 e 5, e L2 `1.0` no fold 3. Os cinco ajustes externos produziram saídas finitas, mas todos alcançaram o limite de 250 iterações sem convergir. Essa limitação impede interpretar a vantagem observada como evidência de que a otimização do CRF já está estabilizada.

## Evidência e auditoria

O arquivo [development-cv-results-evidence.json](development-cv-results-evidence.json) contém configuração, hashes das entradas, commit do código, L2 selecionado, hashes dos cinco manifestos de modelos e métricas sem incluir textos clínicos, anotações ou predições.

Com os artefatos locais preparados conforme o [guia de execução](running-the-study.md), a conferência pode ser repetida com:

```bash
python -m project2_from_project1.scripts.audit_development_results
```

O auditor verifica os hashes dos 401 artefatos declarados pelo manifesto consolidado, os cinco ajustes externos e todas as métricas publicadas. Ele imprime somente contagens, hashes e estado da verificação.

## Limitações de interpretação

- Estes resultados usam validação cruzada de desenvolvimento. Eles não constituem uma nova avaliação externa cega.
- O teste fixo do MCRC permaneceu isolado e não foi usado para escolher hiperparâmetros ou publicar esta tabela.
- Os textos, modelos e predições permanecem fora do Git público. Um clone sem os dados autorizados não consegue recalcular as métricas; o JSON público permite conferir os artefatos quando eles estão disponíveis localmente.
- Os resultados externos do trabalho acadêmico usam outro conjunto e outro protocolo. Comparações diretas entre as duas tabelas não medem uma melhora causal.
