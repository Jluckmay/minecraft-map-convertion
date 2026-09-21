# Arquivos de Entrada / Input Files

*Read in / Leia em:*
- [Português (PT-BR)](#português-pt-br)
- [English (EN)](#english-en)

---

<a name="português-pt-br"></a>
## Português (PT-BR)

Este diretório contém os arquivos-fonte originais utilizados para o processo de conversão e bridge.

### Arquivos Oficiais do Projeto

1. **`java-version.zip`**
   - **Origem**: Mundo Java Edition 1.16.5 original do mapa Mazescapist / MazeRunner.
   - **Tamanho**: ~224.7 MB (224.707.649 bytes)
   - **SHA-256**: `16ac4e38618a47bee3771bb97dd48024ceb6c350a55fa264bdd6cd99cf42833a`
   - **Conteúdo**: Regiões MCA (`region/r.*.*.mca`), `level.dat`, `playerdata/`, datapack `MazeRunner` (`data/custom/functions/`, `loot_tables/`), `resources.zip` / assets de texturas.

2. **`bedrock-version.mcworld`**
   - **Origem**: Conversão base de terreno, blocos, biomas e dimensões gerada via ferramenta Chunker.
   - **Tamanho**: ~75.2 MB (75.289.246 bytes)
   - **SHA-256**: `28c99e1f83982fbc72b01179ef22de7a7a84e69880bcc21a76f12558606ee5f1`
   - **Conteúdo**: Banco LevelDB compilado com o terreno do labirinto, contêineres e mapas Bedrock.

### Usando Outros Mapas

Se desejar converter outro mapa utilizando a ferramenta `map_converter.py`:
- Coloque o ZIP do mundo Java como `inputs/java-version.zip` (ou passe via `--java <caminho>`).
- Coloque o MCWORLD convertido pelo Chunker como `inputs/bedrock-version.mcworld` (ou passe via `--bedrock <caminho>`).

---

<a name="english-en"></a>
## English (EN)

This directory contains the original source files used in the conversion and bridge pipeline.

### Official Project Files

1. **`java-version.zip`**
   - **Origin**: Original Java Edition 1.16.5 world of the Mazescapist / MazeRunner map.
   - **Size**: ~224.7 MB (224,707,649 bytes)
   - **SHA-256**: `16ac4e38618a47bee3771bb97dd48024ceb6c350a55fa264bdd6cd99cf42833a`
   - **Contents**: Anvil MCA regions (`region/r.*.*.mca`), `level.dat`, `playerdata/`, `MazeRunner` datapack (`data/custom/functions/`, `loot_tables/`), and `resources.zip` / texture assets.

2. **`bedrock-version.mcworld`**
   - **Origin**: Base conversion of terrain, blocks, biomes, and dimensions generated via the Chunker tool.
   - **Size**: ~75.2 MB (75,289,246 bytes)
   - **SHA-256**: `28c99e1f83982fbc72b01179ef22de7a7a84e69880bcc21a76f12558606ee5f1`
   - **Contents**: LevelDB database compiled with maze terrain, containers, and Bedrock maps.

### Using Other Maps

To convert a different map using the `map_converter.py` tool:
- Place the Java world ZIP archive as `inputs/java-version.zip` (or pass it via `--java <path>`).
- Place the Chunker-converted MCWORLD as `inputs/bedrock-version.mcworld` (or pass it via `--bedrock <path>`).
