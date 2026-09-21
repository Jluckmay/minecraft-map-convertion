# Guia de Auditoria de Mundos e Entidades / World & Entity Audit Guide (Java Edition)

*Read in / Leia em:*
- [Português (PT-BR)](#português-pt-br)
- [English (EN)](#english-en)

---

<a name="português-pt-br"></a>
## Português (PT-BR)

Antes de converter qualquer mundo Java para Bedrock, a ferramenta executa uma rotina de auditoria profunda diretamente nos arquivos binários de região do formato Anvil e nos arquivos NBT do mapa.

### 1. O Que é Auditado

1. **Cabeçalho e Metadados Globais (`level.dat`)**:
   - Versão do jogo e `DataVersion` do Minecraft.
   - Nome do mundo (`LevelName`), modo de jogo e coordenadas de spawn padrão (`SpawnX`, `SpawnY`, `SpawnZ`).
2. **Dados dos Jogadores (`playerdata/*.dat`)**:
   - Posição do jogador, dimensões de logout, modo de jogo, nível de experiência e vida.
   - Itens no inventário principal, barra rápida e baú do fim (`EnderItems`).
3. **Regiões Anvil (`region/r.*.*.mca` e `DIM-1/region/r.*.*.mca`)**:
   - Leitura da tabela de setores do formato Anvil (4096 bytes de cabeçalho).
   - Descompressão zlib das seções de chunks.
   - Extração do censo de todas as entidades (`Entities`), blocos de comando (`TileEntities` com ID `minecraft:command_block`) e molduras de itens (`ItemFrame`).
4. **Datapacks e Funções (`datapacks/*/data/*/functions/`)**:
   - Identificação de comandos de invocação de NPCs customizados e trocas embutidas.

---

<a name="english-en"></a>
## English (EN)

Prior to converting any Java world to Bedrock, the tool executes an in-depth audit scanning the Anvil region binary files and NBT files of the world.

### 1. What is Audited

1. **Global Header & Metadata (`level.dat`)**:
   - Game version and Minecraft `DataVersion`.
   - World name (`LevelName`), game mode, and spawn coordinates (`SpawnX`, `SpawnY`, `SpawnZ`).
2. **Player Data (`playerdata/*.dat`)**:
   - Player position, logout dimension, game mode, XP level, and health.
   - Main inventory contents, hotbar items, and Ender Chest items (`EnderItems`).
3. **Anvil Regions (`region/r.*.*.mca` and `DIM-1/region/r.*.*.mca`)**:
   - Reading the sector table of the Anvil format (4096-byte header).
   - Decompressing chunk zlib payloads.
   - Census extraction of all entities (`Entities`), command blocks (`TileEntities` with ID `minecraft:command_block`), and item frames (`ItemFrame`).
4. **Datapacks & Functions (`datapacks/*/data/*/functions/`)**:
   - Detection of custom NPC summon commands and embedded trade recipes.
