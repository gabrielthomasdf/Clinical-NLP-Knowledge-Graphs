# Execução sintética para o portfólio

Este exemplo foi executado localmente em 2026-11-03 com Python 3.14.6, PyTorch 2.14.1+cpu, fixture de 12 documentos (`seed=7`) e `--max-iterations 20`. Usa somente texto fictício. O objetivo é demonstrar a integração de texto, entidades, relações e grafo; seus F1 não representam qualidade em relatos reais.

Na raiz do repositório, após a [instalação](../../README.md#executar-sem-dados-clínicos):

```bash
python -m project2_from_project1.scripts.run_full_study --synthetic project2_from_project1/artifacts/demo-input --output-dir project2_from_project1/artifacts/demo-output --max-iterations 20
```

O comando imprime os resultados dos seis braços (quatro fim a fim e dois tetos diagnósticos) e escreve `manifest.json`. Nesta execução, os quatro braços fim a fim completaram os dois folds sem falhas. O `relation_macro_f1.mean` sintético foi `0.7163` para `dictionary+rules`, `0.6298` para `dictionary+knn`, `0.9537` para `crf+rules` e `0.8604` para `crf+knn`. Esses números dependem da fixture artificial e do limite reduzido de iterações; servem apenas para conferir a execução.

## Entrada e saída verificáveis

O texto completo de `synthetic:000` em `demo-input/corpus.jsonl` é:

```text
The patient is a smoker adult. She reported fatigue and chest pain. No nausea was observed. Asthma caused back pain. The weather was mild today.
```

No arquivo `demo-output/graph/dictionary-rules/fold-01/graph.jsonl`, a camada de conceitos de `synthetic:000` contém os nós `Patient`, `Factor(smoker)`, `Finding(fatigue)`, `Finding(chest pain)`, `Finding(nausea)`, `Condition(asthma)`, `Finding(back pain)` e `Modifier(no)`. As relações incluem `HAS_FACTOR(Patient, smoker)`, `HAS_CONDITION(Patient, asthma)`, `CAUSES(asthma, back pain)` e `NEGATES(no, nausea)`.

**Falha observada na versão acadêmica:** o mesmo braço também produziu `HAS_FINDING(Patient, nausea)`, apesar de `NEGATES(no, nausea)`. A [etapa opcional de consistência](negation-ablation.md) corrige o conflito nessa menção e exporta novas saídas em pasta separada. Este exemplo permanece como evidência do comportamento da versão auditada.

Para inspecionar o manifesto e os registros completos, abra os JSONL gerados no caminho acima. Cada registro de grafo inclui `document_id`, camada, tipo de registro, IDs estáveis, relação ou tipo canônico e proveniência. O código do teste de integração está em [`tests/test_full_study.py`](../tests/test_full_study.py).
