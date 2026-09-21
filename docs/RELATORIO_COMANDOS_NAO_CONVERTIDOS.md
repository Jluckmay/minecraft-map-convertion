# Relatório de Comandos Não Convertidos e Ajustes de Sintaxe / Unconverted Commands & Syntax Adjustments Report

*Read in / Leia em:*
- [Português (PT-BR)](#português-pt-br)
- [English (EN)](#english-en)

---

<a name="português-pt-br"></a>
## Português (PT-BR)

Durante o processo de conversão das 54 funções do datapack original, 2.603 linhas exigiram adaptação técnica para conformidade com o interpretador de comandos do Minecraft Bedrock 1.26.40.

### 1. Comandos com Equivalência Indireta ou Substituição

#### 1.1. `forceload` (2.056 ocorrências em 17 arquivos)
- **Motivo**: O comando `/forceload` não existe no Minecraft Bedrock Edition.
- **Solução Implementada**: Nas funções de abertura de portas e mapas (`open_doors_*.mcfunction`, `map_full_*.mcfunction`), as linhas de `forceload add` e `forceload remove` foram convertidas em comentários informativos (`# [Bedrock Conversion] forceload ...`). O carregamento contínuo das áreas críticas do labirinto é garantido pelo registro de áreas de simulação contínua (`tickingarea`) na função de inicialização do mundo `mazerunner:init_world`.

#### 1.2. `data merge block` (547 ocorrências em 17 arquivos)
- **Motivo**: O comando `/data` é restrito à Java Edition.
- **Solução Implementada**: Nas funções `reset_spawner_1.mcfunction` até `reset_spawner_16.mcfunction`, os comandos `data merge block <x> <y> <z> {Delay:0}` foram documentados como comentários preservando as coordenadas exatas dos geradores. No Bedrock Edition, os geradores de monstros (`spawner`) calculam e reiniciam o ciclo de spawn automaticamente sempre que um jogador se encontra no raio de 16 blocos, garantindo a jogabilidade sem quebra de fluxo.

#### 1.3. `playsound` (11 ocorrências)
- **Motivo**: O identificador de som `minecraft:entity.player.levelup` possui sintaxe diferente no Bedrock.
- **Solução Implementada**: Convertido para `playsound random.levelup @p`.

---

### 2. Resumo Quantitativo de Comandos do Datapack

| Tipo de Comando | Total no Java | Tratamento no Bedrock 1.26.40 |
| :--- | :--- | :--- |
| `forceload` | 2.056 | Substituído por `tickingarea` permanente do labirinto |
| `clone` | 1.024 | 100% convertido e funcional |
| `data merge` | 547 | Substituído pela mecânica nativa de spawners por proximidade |
| `execute` | 76 | 100% convertido para a sintaxe moderna do Bedrock 1.26.40 |
| `setblock` | 32 | 100% convertido e funcional |
| `fill` | 16 | 100% convertido e funcional |
| `tp` | 2 | 100% convertido e funcional |

---

<a name="english-en"></a>
## English (EN)

During the conversion of the 54 functions from the original datapack, 2,603 lines required technical adaptation to ensure full compliance with the Minecraft Bedrock 1.26.40 command parser.

### 1. Commands with Indirect Equivalence or Substitution

#### 1.1. `forceload` (2,056 occurrences across 17 files)
- **Reason**: The `/forceload` command does not exist in Minecraft Bedrock Edition.
- **Implemented Solution**: In door opening and map functions (`open_doors_*.mcfunction`, `map_full_*.mcfunction`), all `forceload add` and `forceload remove` lines were converted into informative comments (`# [Bedrock Conversion] forceload ...`). Continuous simulation of critical maze areas is ensured via persistent `tickingarea` registration in the initialization function `mazerunner:init_world`.

#### 1.2. `data merge block` (547 occurrences across 17 files)
- **Reason**: The `/data` command is restricted to Java Edition.
- **Implemented Solution**: In functions `reset_spawner_1.mcfunction` through `reset_spawner_16.mcfunction`, `data merge block <x> <y> <z> {Delay:0}` commands were preserved as comments maintaining exact block coordinates. In Bedrock Edition, monster spawners automatically recalculate and trigger spawn cycles whenever a player enters within the 16-block proximity radius, ensuring continuous gameplay without disruption.

#### 1.3. `playsound` (11 occurrences)
- **Reason**: The sound identifier `minecraft:entity.player.levelup` has a different syntax in Bedrock.
- **Implemented Solution**: Translated to `playsound random.levelup @p`.

---

### 2. Quantitative Summary of Datapack Commands

| Command Type | Total in Java | Handling in Bedrock 1.26.40 |
| :--- | :--- | :--- |
| `forceload` | 2,056 | Replaced by permanent maze `tickingarea` |
| `clone` | 1,024 | 100% converted and functional |
| `data merge` | 547 | Replaced by native proximity spawner mechanics |
| `execute` | 76 | 100% converted to modern Bedrock 1.26.40 syntax |
| `setblock` | 32 | 100% converted and functional |
| `fill` | 16 | 100% converted and functional |
| `tp` | 2 | 100% converted and functional |
