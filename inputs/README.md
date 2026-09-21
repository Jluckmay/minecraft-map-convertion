# Arquivos de Entrada / Input Files

Este diretório contém os arquivos-fonte originais utilizados para o processo de conversão e bridge.

## Arquivos Oficiais do Projeto

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

---

## Usando Outros Mapas / Using Other Maps

Se desejar converter outro mapa utilizando a ferramenta `map_converter.py`:
- Coloque o ZIP do mundo Java como `inputs/java-version.zip` (ou passe via `--java <caminho>`).
- Coloque o MCWORLD convertido pelo Chunker como `inputs/bedrock-version.mcworld` (ou passe via `--bedrock <caminho>`).

