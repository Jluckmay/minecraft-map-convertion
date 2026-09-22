# Arquivos de Referência e Exemplo / Expected & Reference Files

*Read in / Leia em:*
- [Português (PT-BR)](#português-pt-br)
- [English (EN)](#english-en)

---

<a name="português-pt-br"></a>
## Português (PT-BR)

Este diretório contém os arquivos de **referência, amostras e resultados esperados** utilizados para validação, comparação de schemas e benchmarks do conversor.

### Arquivos de Amostra e Referência

1. **`bedrock-version.mcworld`**:
   - Mundo Minecraft Bedrock de referência convertido via ferramenta [Chunker](https://chunker.app).
   - Serve como gabarito estrutural do banco LevelDB, layout de sub-chunks e template de terreno inicial para injeção de command blocks e addons.

2. **`maze-runner-resource-pack.mcpack`**:
   - Pacote de recursos Bedrock funcional de referência convertido via [MinecraftMaps](https://chunker.app).
   - Utilizado como padrão ouro comprovado para a sintaxe de variações ponderadas de texturas em `terrain_texture.json` e compatibilidade com Bedrock 1.20+/1.21+.

3. **`resources.zip`**:
   - Pacote de recursos Java original fornecido como referência complementar de texturas (`textures/block/bedrock_*.png`) e áudios (`sounds/`).
   - Idêntico ao pacote de recursos embutido no mapa Java.

> **Nota de Versionamento**: Arquivos binários pesados (`*.mcworld`, `*.mcpack`, `*.zip`) são estritamente excluídos do controle de versão via `.gitignore`. Apenas a documentação e os arquivos de controle permanecem versionados.

---

<a name="english-en"></a>
## English (EN)

This directory contains **reference, sample, and expected output files** used for validation, schema comparison, and converter benchmarking.

### Reference and Sample Files

1. **`bedrock-version.mcworld`**:
   - Reference Minecraft Bedrock world converted via [Chunker](https://chunker.app).
   - Serves as the structural LevelDB baseline, sub-chunk layout reference, and initial terrain template for command block injection and addon attachment.

2. **`maze-runner-resource-pack.mcpack`**:
   - Working reference Bedrock resource pack converted via [MinecraftMaps](https://chunker.app).
   - Serves as the proven gold standard for weighted texture variations in `terrain_texture.json` and Bedrock 1.20+/1.21+ rendering compatibility.

3. **`resources.zip`**:
   - Original Java resource pack provided as an additional reference for block textures (`textures/block/bedrock_*.png`) and sound files (`sounds/`).
   - Exactly matches the resource pack embedded inside the Java world archive.

> **VCS Note**: Heavy binary archives (`*.mcworld`, `*.mcpack`, `*.zip`) are strictly excluded from version control via `.gitignore`. Only documentation and tracking files remain in the repository.

