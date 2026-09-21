# Arquivos de Entrada / Input Files

*Read in / Leia em:*
- [Português (PT-BR)](#português-pt-br)
- [English (EN)](#english-en)

---

<a name="português-pt-br"></a>
## Português (PT-BR)

Este diretório é o local padrão para posicionar os arquivos de entrada do mapa que você deseja converter.

### Arquivos Esperados

Para realizar a conversão completa de um mapa de **Minecraft Java Edition** para **Minecraft Bedrock Edition 1.26.40+**, você precisará de dois arquivos:

1. **Mundo Java Original (`.zip`)**:
   - Arquivo compactado do mundo Java Edition (contendo pastas como `region/`, `level.dat`, `datapacks/`, etc.).
   - Pode ser nomeado como preferir (ex: `meu_mapa_java.zip`).
2. **Mundo Bedrock Base do Chunker (`.mcworld`)**:
   - Saída gerada pela ferramenta [Chunker](https://chunker.app), contendo o terreno e biomas já convertidos para o banco LevelDB.
   - Pode ser nomeado como preferir (ex: `meu_mapa_chunker.mcworld`).

> **Nota**: Arquivos binários pesados de mundos (`*.zip` e `*.mcworld`) não são versionados no Git (excluídos via `.gitignore`) para respeitar as políticas de limite do GitHub.

### Como Executar

Basta colocar seus arquivos aqui e executar:
```bash
python map_converter.py --java inputs/<seu_mundo_java>.zip --bedrock inputs/<seu_mundo_bedrock>.mcworld
```

---

<a name="english-en"></a>
## English (EN)

This directory is the default location to place input world files for conversion.

### Expected Files

To convert any **Minecraft Java Edition** world to **Minecraft Bedrock Edition 1.26.40+**, you will need two files:

1. **Original Java World (`.zip`)**:
   - Zipped archive of the Java Edition world (containing folders such as `region/`, `level.dat`, `datapacks/`, etc.).
   - Can be named freely (e.g., `my_java_world.zip`).
2. **Base Bedrock World from Chunker (`.mcworld`)**:
   - Output produced by [Chunker](https://chunker.app), containing terrain, blocks, and biomes converted into the LevelDB database.
   - Can be named freely (e.g., `my_chunker_world.mcworld`).

> **Note**: Heavy binary world archives (`*.zip` and `*.mcworld`) are not tracked in Git (excluded via `.gitignore`) to comply with GitHub file size limits.

### How to Run

Place your files here and execute:
```bash
python map_converter.py --java inputs/<your_java_world>.zip --bedrock inputs/<your_bedrock_world>.mcworld
```
