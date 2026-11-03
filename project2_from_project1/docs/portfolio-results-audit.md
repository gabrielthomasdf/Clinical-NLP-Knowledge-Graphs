# Auditoria dos resultados externos para o portfólio

Em 2026-11-03, os artefatos locais ignorados pelo Git foram conferidos com `scripts.audit_external_results`. O script verificou os SHA-256 dos **5 artefatos de modelos**, **64 arquivos de código registrados no manifesto dos modelos**, **18 artefatos da avaliação**, arquivos das cinco partições e suas ligações de entrada. Confirmou 42 documentos de desenvolvimento, 11 no teste fixo MCRC e 63 no snapshot externo, sem sobreposição de IDs entre essas partições. O [resumo JSON sem textos clínicos](portfolio-results-evidence.json) contém os hashes e as métricas completas.

As métricas arredondadas no [README da raiz](../../README.md#dados-avaliação-e-resultados) correspondem às do `report.json` local. Reexecutei a **pontuação** com `--resume-frozen-predictions` em uma pasta separada: o novo `report.json` ficou idêntico, byte a byte, ao original (`SHA-256 aa9a15d4c545c58a44e673519e2ec380f469882767c128051b1a14c4ea8825f2`); os 18 hashes de artefatos da avaliação também coincidiram. Essa operação usa as predições já congeladas: **não** retreina os modelos nem repete a inferência do CRF.

## Como repetir a conferência local

Depois de obter os corpora e os artefatos locais nas pastas indicadas pelo [guia do estudo](running-the-study.md), execute na raiz do repositório:

```bash
python -m project2_from_project1.scripts.audit_external_results
```

O script falha se faltar um arquivo, se um hash mudar, se as partições se sobrepuserem, se os textos/IDs do snapshot diferirem do gold ou se os F1 publicados não corresponderem ao relatório. Ele imprime somente contagens, hashes e métricas agregadas. Para reproduzir a pontuação original, copie `predictions-manifest.json` e as pastas `dictionary/` e `crf/` de `artifacts/external-final-evaluation-v1/` para uma **nova** pasta de saída e execute:

```bash
python -m project2_from_project1.scripts.run_external_evaluation \
  --models project2_from_project1/artifacts/external-final-models-v1 \
  --raw project2_from_project1/artifacts/external-final-snapshot-v1/raw.jsonl \
  --gold project2_from_project1/artifacts/external-multicare-fresh-gold-through70-eligible-v3/provisional-gold.jsonl \
  --training-corpus project2_from_project1/artifacts/development-source-reconciled-v1/corpus.jsonl \
  --training-projection project2_from_project1/artifacts/development-source-reconciled-v1/gold/gold-projection.jsonl \
  --output-dir CAMINHO_DA_NOVA_PASTA \
  --resume-frozen-predictions
```

Use o **corpus reconciliado** nesse comando. O `data/secure/mcrc.jsonl` inicial tem hash diferente e é rejeitado pelo manifesto dos modelos congelados. Essa recusa foi observada na auditoria; nenhum modelo foi alterado para contorná-la.

## Limites da evidência

- O repositório público inclui o resumo auditado e os scripts, mas não inclui textos clínicos, predições, modelos ou a anotação externa completa. Um clone público sozinho ainda não permite recalcular as métricas externas. A auditoria acima comprova a consistência dos artefatos **locais** disponíveis nesta máquina.
- O snapshot externo foi solicitado com 63 documentos elegíveis de 70 candidatos. Não atingiu a regra inicialmente proposta de 100 documentos ou 20 relações por classe: `CAUSES` possui 9 exemplos. Os resultados não equivalem à validação externa definitiva originalmente planejada.
- O CRF produziu valores finitos, mas não convergiu dentro de 250 iterações. O relatório registra 8 menções que cruzam sentenças fora da projeção plana; 8 relações `HAS_FINDING` aparecem como perdas de projeção do grafo.
- Esta auditoria não é uma nova avaliação cega: os dados e as métricas do snapshot já haviam sido examinados no trabalho acadêmico. Novos ajustes de modelo precisam usar desenvolvimento ou outro conjunto externo, sem otimização sobre este snapshot.
- Os resumos completos dos cinco folds de desenvolvimento não estão presentes entre os artefatos locais preservados. Os valores de desenvolvimento descritos em `entity-recognizer-comparison.md` e `relation-factorial-results.md` ainda não foram recalculados nesta auditoria; reproduzi-los exige o estudo completo, com cerca de 65 treinos do CRF e aproximadamente 4 horas na máquina de referência documentada.
