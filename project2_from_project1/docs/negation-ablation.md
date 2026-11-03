# Experimento de consistência da negação

O pipeline acadêmico classifica candidatos a relações independentemente. Assim, a mesma menção de `Finding` pode receber `NEGATES(Modifier, Finding)` e `HAS_FINDING(Patient, Finding)`. Isso contraria a [decisão arquitetural sobre negação](adr/0007-preservar-negacao-como-evidencia.md).

A etapa opcional `negated-finding-consistency-v1` altera **somente** `HAS_FINDING` cujo documento e ID da menção alvo também aparecem em um `NEGATES` positivo. A decisão passa a `NO_RELATION`; o registro conserva o par, a versão e a evidência da alteração. Menções diferentes da mesma palavra não são suprimidas. As predições e métricas originais não são reescritas.

## Reproduzir com dados fictícios

Após instalar as dependências conforme o [README da raiz](../../README.md#executar-sem-dados-clínicos), execute da raiz do repositório:

```bash
python -m project2_from_project1.scripts.run_full_study --synthetic project2_from_project1/artifacts/demo-input --output-dir project2_from_project1/artifacts/demo-output --max-iterations 20
python -m project2_from_project1.scripts.run_negation_ablation --study-output project2_from_project1/artifacts/demo-output --corpus project2_from_project1/artifacts/demo-input/corpus.jsonl --output-dir project2_from_project1/artifacts/negation-ablation
```

O segundo comando usa as predições congeladas pelo primeiro, sem treinar novamente. Produz `report.json`, predições corrigidas e grafos JSONL v2 corrigidos, todos em uma pasta separada. O relatório contém hashes SHA-256 das entradas e saídas, contagens de conflitos e precisão, recall e F1 micro de arestas conceituais antes/depois. Esses números são **secundários**; a avaliação estrita de relações fim a fim continua sendo a métrica principal do estudo.

## Resultado observado

Na execução sintética local de 2026-11-03, com 12 documentos, `seed=7`, dois folds e `--max-iterations 20`, a etapa alterou 27 decisões nos oito conjuntos (quatro abordagens × dois folds). Os 27 conflitos por menção caíram a zero. O [relatório sanitizado](negation-ablation-evidence.json) registra cada fold e seus hashes; não contém relatos clínicos.

| Abordagem | Conflitos antes → depois | F1 micro de arestas conceituais, fold 1 | Fold 2 |
| --- | ---: | ---: | ---: |
| Dicionário + regras | 10 → 0 | 0,7879 → 0,8525 | 0,8060 → 0,8710 |
| Dicionário + k-NN | 4 → 0 | 0,7458 → 0,7018 | 0,8065 → 0,7667 |
| CRF + regras | 9 → 0 | 0,9333 → 1,0000 | 0,9189 → 0,9714 |
| CRF + k-NN | 4 → 0 | 0,9118 → 0,8788 | 0,9143 → 0,8824 |

A queda nos braços k-NN mostra que uma predição `NEGATES` incorreta pode suprimir um `HAS_FINDING` correto. Portanto, consistência lógica e qualidade de extração precisam ser avaliadas separadamente. Esta fixture artificial não estima desempenho clínico e não foi usada para ajustar modelos. Antes de adotar a etapa como padrão, é necessário compará-la em partições de validação por documento com suporte por classe e manter o teste fixo separado.
