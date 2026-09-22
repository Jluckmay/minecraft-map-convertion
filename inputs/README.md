# Arquivos de Entrada / Input Files

*Read in / Leia em:*
- [Português (PT-BR)](#português-pt-br)
- [English (EN)](#english-en)

---

<a name="português-pt-br"></a>
## Português (PT-BR)

Este diretório é o local padrão para posicionar os arquivos de entrada do mapa que você deseja converter.
Este diretório é o local padrão para posicionar os arquivos de entrada do mapa Java que você deseja converter.

### Arquivos Esperados
### Arquivo Obrigatório

Para realizar a conversão completa de um mapa de **Minecraft Java Edition** para **Minecraft Bedrock Edition 1.26.40+**, você precisará de dois arquivos:

1. **Mundo Java Original (`.zip`)**:
   - Arquivo compactado do mundo Java Edition (contendo pastas como `region/`, `level.dat`, `datapacks/`, etc.).
   - Pode ser nomeado como preferir (ex: `meu_mapa_java.zip`).
2. **Mundo Bedrock Base do Chunker (`.mcworld`)**:
   - Saída gerada pela ferramenta [Chunker](https://chunker.app), contendo o terreno e biomas já convertidos para o banco LevelDB.
   - Pode ser nomeado como preferir (ex: `meu_mapa_chunker.mcworld`).
   - Arquivo compactado do mundo Java Edition (contendo pastas como `region/`, `level.dat`, `datapacks/`, etc., ex: `java-version.zip` ou `<seu_mapa>.zip`).
   - Caso o mapa possua Resource Pack embutido (`resources.zip` ou pasta `resources/`), o pipeline o detecta e extrai automaticamente sem necessidade de arquivos externos adicionais.

> **Nota**: Arquivos binários pesados de mundos (`*.zip` e `*.mcworld`) não são versionados no Git (excluídos via `.gitignore`) para respeitar as políticas de limite do GitHub.
### Arquivo Opcional

2. **Mundo Bedrock Base (`.mcworld`)**:
   - Se fornecido em `inputs/`, será utilizado como a base do terreno para conversão.
   - Caso não seja fornecido em `inputs/`, o pipeline utilizará automaticamente o template de referência presente na pasta `expected/` (`expected/bedrock-version.mcworld`).

> **Nota de Versionamento**: Arquivos binários pesados de mundos (`*.zip` e `*.mcworld`) não são versionados no Git (excluídos via `.gitignore`).

### Como Executar

Basta colocar seus arquivos aqui e executar:
Para executar o pipeline modular completo:
```bash
python map_converter.py --java inputs/<seu_mundo_java>.zip --bedrock inputs/<seu_mundo_bedrock>.mcworld
python scripts/phase1_analyze_world.py
python scripts/phase2_extract_command_blocks.py
python scripts/phase3_inventory_commands.py
python scripts/phase4_analyze_resources.py
python scripts/phase5_to_9_convert_all.py
python scripts/phase10_validate.py
python scripts/phase11_package.py
python scripts/phase12_report.py
```

---

<a name="english-en"></a>
## English (EN)

This directory is the default location to place input world files for conversion.
This directory is the default location to place input Java world files for conversion.

### Expected Files
### Required File

To convert any **Minecraft Java Edition** world to **Minecraft Bedrock Edition 1.26.40+**, you will need two files:

1. **Original Java World (`.zip`)**:
   - Zipped archive of the Java Edition world (containing folders such as `region/`, `level.dat`, `datapacks/`, etc.).
   - Can be named freely (e.g., `my_java_world.zip`).
2. **Base Bedrock World from Chunker (`.mcworld`)**:
   - Output produced by [Chunker](https://chunker.app), containing terrain, blocks, and biomes converted into the LevelDB database.
   - Can be named freely (e.g., `my_chunker_world.mcworld`).
   - Compressed archive of the Java Edition world (containing folders like `region/`, `level.dat`, `datapacks/`, etc., e.g., `java-version.zip` or `<your_world>.zip`).
   - If the map contains an embedded resource pack (`resources.zip` or a `resources/` directory), the pipeline detects and extracts it automatically without requiring separate external files.

> **Note**: Heavy binary world archives (`*.zip` and `*.mcworld`) are not tracked in Git (excluded via `.gitignore`) to comply with GitHub file size limits.
### Optional File

2. **Base Bedrock World (`.mcworld`)**:
   - If provided in `inputs/`, it will be used as the base terrain for conversion.
   - If omitted from `inputs/`, the pipeline automatically falls back to the reference template in `expected/` (`expected/bedrock-version.mcworld`).

> **VCS Note**: Heavy binary world archives (`*.zip` and `*.mcworld`) are excluded from Git tracking via `.gitignore`.

### How to Run

Place your files here and execute:
To run the complete modular conversion pipeline:
```bash
python map_converter.py --java inputs/<your_java_world>.zip --bedrock inputs/<your_bedrock_world>.mcworld
python scripts/phase1_analyze_world.py
python scripts/phase2_extract_command_blocks.py
python scripts/phase3_inventory_commands.py
python scripts/phase4_analyze_resources.py
python scripts/phase5_to_9_convert_all.py
python scripts/phase10_validate.py
python scripts/phase11_package.py
python scripts/phase12_report.py
```
