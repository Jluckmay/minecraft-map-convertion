# Relatório de Auditoria de Entidades e Jogadores / Entity & Playerdata Audit Report (Java 1.16.5)

*Read in / Leia em:*
- [Português (PT-BR)](#português-pt-br)
- [English (EN)](#english-en)

---

<a name="português-pt-br"></a>
## Português (PT-BR)

### 1. Dados Globais do Mundo Java
- **Nome do Nível**: `Mazescapist` (`§4§lMazescapist`)
- **Versão Java**: 1.16.5 (DataVersion 2586)
- **Coordenadas de Spawn**: `X: 381, Y: 5, Z: -2171` (Lobby central do labirinto)
- **Dimensões Auditadas**:
  - Overworld (`region/`): 259 arquivos MCA
  - Nether (`DIM-1/region/`): 41 arquivos MCA
  - Total de entidades extraídas: **2.031 entidades**

### 2. Auditoria Individual de Jogadores (Playerdata)
Foram encontrados e auditados dois arquivos de playerdata no mundo Java:

| Jogador | UUID | Dimensão | Posição (X, Y, Z) | Modo | Vida | XP | Inventário | Ender Chest | Efeitos | Veículo |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **NereidRegulus** | `370fb06a-0d01-43b7-984c-8cbb7d03bfc5` | `minecraft:overworld` | `381.49, 5.00, -2170.52` | Sobrevivência (0) | 20.0 | Nível 0 (0.0) | **Vazio** | **Vazio** | Nenhum | Nenhum |
| **Cafeslayeur** | `7efa11a0-7b4f-4292-948e-796cceccd1ef` | `minecraft:overworld` | `381.53, 5.00, -2170.74` | Sobrevivência (0) | 20.0 | Nível 0 (0.0) | **Vazio** | **Vazio** | Nenhum | Nenhum |

Ambos os jogadores estavam posicionados no lobby de entrada do mapa, desprovidos de itens no inventário ou baú do fim, confirmando estado limpo de distribuição.

---

### 3. Censo Completo de Entidades nas Regiões Java
Distribuição das 2.031 entidades encontradas:

| Identificador Java | Quantidade | Dimensão | Categoria / Descrição |
| :--- | :--- | :--- | :--- |
| `minecraft:strider` | 359 | Nether | Mobs passivos nativos dos mares de lava |
| `minecraft:sheep` | 282 | Overworld | Ovelhas nativas geradas pelo terreno |
| `minecraft:item` | 219 | Overworld / Nether | Itens caídos no chão durante sessões de teste |
| `minecraft:pig` | 205 | Overworld | Porcos nativos gerados pelo terreno |
| `minecraft:chicken` | 178 | Overworld | Galinhas nativas geradas pelo terreno |
| `minecraft:cow` | 149 | Overworld | Vacas nativas geradas pelo terreno |
| `minecraft:falling_block` | 136 | Overworld | Blocos de areia em queda (armadilhas) |
| `minecraft:rabbit` | 133 | Overworld | Coelhos nativos gerados pelo terreno |
| `minecraft:shulker` | 109 | Overworld | Desafios de levitação nas áreas de teste |
| `minecraft:wolf` | 37 | Overworld | Lobos nativos do terreno |
| `minecraft:llama` | 36 | Overworld | Lamas nativas |
| `minecraft:horse` | 36 | Overworld | Cavalos nativos |
| `minecraft:fox` | 31 | Overworld | Raposas nativas |
| `minecraft:bee` | 29 | Overworld | Abelhas nativas |
| `minecraft:creeper` | 17 | Overworld | Monstros nativos |
| `minecraft:zombie` | 12 | Overworld | Monstros nativos |
| `minecraft:skeleton` | 9 | Overworld | 8 nativos + 1 nomeado ("Steve") |
| `minecraft:turtle` | 9 | Overworld | Tartarugas nativas em praias |
| `minecraft:bat` | 8 | Overworld | Morcegos de cavernas |
| `minecraft:item_frame` | 7 | Overworld | Molduras decorativas e livros de regras |
| `minecraft:armor_stand` | 6 | Overworld | Estátuas do Hall da Fama e marcadores técnicos |
| `minecraft:phantom` | 5 | Overworld | Monstros aéreos |
| `minecraft:polar_bear` | 3 | Overworld | Ursos nativos |
| `minecraft:wither_skeleton`| 2 | Overworld | Mobs nativos |
| `minecraft:spider` | 2 | Overworld | Mobs nativos |
| `minecraft:elder_guardian` | 2 | Overworld | Desafios de fadiga de mineração no labirinto |
| `minecraft:parrot` | 2 | Overworld | Papagaios da selva |
| `minecraft:ravager` | 2 | Overworld | Desafios de combate no labirinto |
| `minecraft:vex` | 2 | Overworld | Desafios do labirinto |
| `minecraft:evoker_fangs` | 1 | Overworld | Entidade temporária |
| `minecraft:experience_orb`| 1 | Overworld | Orbe temporário |
| `minecraft:villager` | 1 | Overworld | Aldeão colocado no Setor 13 ("Angus") |
| `minecraft:ghast` | 1 | Nether | Mob nativo |

---

### 4. Entidades Especiais e Curadas

#### 4.1. Suportes de Armadura (Armor Stands)
- **`[99998.5, 105.5, 99956.5]`**: Marcador nomeado `Beta Testers` (verde, negrito).
- **`[99996.5, 105.0, 99955.5]`**: Estátua de `Cyohg` (botas de diamante, calça de cota de malha, peitoral de ferro, cabeça customizada com textura URL: `b06f7164...`).
- **`[100000.5, 105.0, 99955.5]`**: Estátua de `LordOfGnou` (botas de malha, calça de ferro, peitoral de couro tingido de verde, cabeça customizada com textura URL: `dea1088f...`).
- **`[99979.5, 105.0, 99983.5]`**: Estátua de `NereidRegulus` (criador) com armadura de couro tingido e cabeça customizada.
- **`[99979.5, 105.0, 99987.5]`**: Estátua de `Cafeslayeur` (criador) com peitoral de netherita e cabeça customizada.
- **`[277.59, 1.0, -2197.21]`**: Marcador técnico de suporte aos mecanismos.

#### 4.2. Molduras com Itens (Item Frames)
- **Spawn / Lobby**:
  - `[377.03, 6.5, -2131.5]` e `[377.03, 6.5, -2133.5]`: Livro Escrito `"Objective"` por `Nereid` contendo os objetivos do labirinto e monumentos de lã.
  - `[385.97, 6.5, -2131.5]` e `[385.97, 6.5, -2133.5]`: Livro Escrito `"Rules"` por `Nereid` com regras de conduta.
- **Setor 13**:
  - `[963.5, 147.0, 1142.5]`: Salmão cru.
  - `[961.0, 146.5, 1144.5]`: Bacalhau cru.
  - `[963.5, 147.0, 1144.5]`: Peixe tropical.

#### 4.3. NPCs Progressivos da Função `generates_npc.mcfunction`
1. **Bruce** (Dia 4) - Fazendeiro Savanna (`264, 59, -2184`)
2. **Boris** (Dia 9) - Pastor Savanna (`264, 59, -2184`)
3. **Joe** (Dia 13) - Flecheiro Savanna (`264, 59, -2184`)
4. **Tobias** (Dia 17) - Armeiro de Armas Savanna (`264, 59, -2184`)
5. **George** (Dia 21) - Açougueiro Savanna (`264, 59, -2184`)
6. **Erik** (Dia 26) - Clérigo Savanna (`264, 59, -2184`)
7. **Adam** (Dia 31) - Pedreiro Savanna (`264, 59, -2184`)
8. **Joakim** (Dia 38) - Armeiro de Armadura Savanna (`264, 59, -2184`)
9. **Seth** (Dia 47) - Bibliotecário Savanna (`264, 59, -2184`)
10. **Jörn** (Dia 55) - Cartógrafo Savanna (`264, 59, -2184`)

#### 4.4. NPCs de Exploração (Blocos de Comando)
11. **Ylva** - Armeira Selva (Armaduras personalizadas e netherita)
12. **Jonne** - Clérigo Selva (Poções customizadas e poções persistentes)
13. **Heri** - Armeiro Selva (Armas encantadas e tridente)
14. **Kai** - Flecheiro Selva (Flechas especiais)
15. **Angus** - Bibliotecário Selva (Livros encantados)

---

<a name="english-en"></a>
## English (EN)

### 1. Global Java World Data
- **Level Name**: `Mazescapist` (`§4§lMazescapist`)
- **Java Version**: 1.16.5 (DataVersion 2586)
- **Spawn Coordinates**: `X: 381, Y: 5, Z: -2171` (Central maze lobby)
- **Audited Dimensions**:
  - Overworld (`region/`): 259 MCA files
  - Nether (`DIM-1/region/`): 41 MCA files
  - Total extracted entities: **2,031 entities**

### 2. Individual Playerdata Audit
Two playerdata files were discovered and audited from the Java world:

| Player | UUID | Dimension | Position (X, Y, Z) | Mode | Health | XP | Inventory | Ender Chest | Effects | Vehicle |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **NereidRegulus** | `370fb06a-0d01-43b7-984c-8cbb7d03bfc5` | `minecraft:overworld` | `381.49, 5.00, -2170.52` | Survival (0) | 20.0 | Level 0 (0.0) | **Empty** | **Empty** | None | None |
| **Cafeslayeur** | `7efa11a0-7b4f-4292-948e-796cceccd1ef` | `minecraft:overworld` | `381.53, 5.00, -2170.74` | Survival (0) | 20.0 | Level 0 (0.0) | **Empty** | **Empty** | None | None |

Both players were positioned directly in the spawn lobby, with empty inventories and empty ender chests, confirming a clean distribution state.

---

### 3. Complete Entity Census Across Java Regions
Distribution of all 2,031 detected entities:

| Java Identifier | Count | Dimension | Category / Description |
| :--- | :--- | :--- | :--- |
| `minecraft:strider` | 359 | Nether | Native passive mobs on lava oceans |
| `minecraft:sheep` | 282 | Overworld | Native sheep generated by terrain |
| `minecraft:item` | 219 | Overworld / Nether | Dropped items from prior test runs |
| `minecraft:pig` | 205 | Overworld | Native pigs generated by terrain |
| `minecraft:chicken` | 178 | Overworld | Native chickens generated by terrain |
| `minecraft:cow` | 149 | Overworld | Native cows generated by terrain |
| `minecraft:falling_block` | 136 | Overworld | Falling sand blocks (traps) |
| `minecraft:rabbit` | 133 | Overworld | Native rabbits |
| `minecraft:shulker` | 109 | Overworld | Levitation challenges in test sectors |
| `minecraft:wolf` | 37 | Overworld | Native wolves |
| `minecraft:llama` | 36 | Overworld | Native llamas |
| `minecraft:horse` | 36 | Overworld | Native horses |
| `minecraft:fox` | 31 | Overworld | Native foxes |
| `minecraft:bee` | 29 | Overworld | Native bees |
| `minecraft:creeper` | 17 | Overworld | Native monsters |
| `minecraft:zombie` | 12 | Overworld | Native monsters |
| `minecraft:skeleton` | 9 | Overworld | 8 native + 1 named ("Steve") |
| `minecraft:turtle` | 9 | Overworld | Native turtles on beaches |
| `minecraft:bat` | 8 | Overworld | Cave bats |
| `minecraft:item_frame` | 7 | Overworld | Decorative frames & rule books |
| `minecraft:armor_stand` | 6 | Overworld | Hall of Fame statues & tech markers |
| `minecraft:phantom` | 5 | Overworld | Aerial monsters |
| `minecraft:polar_bear` | 3 | Overworld | Native polar bears |
| `minecraft:wither_skeleton`| 2 | Overworld | Native mobs |
| `minecraft:spider` | 2 | Overworld | Native mobs |
| `minecraft:elder_guardian` | 2 | Overworld | Mining fatigue maze challenges |
| `minecraft:parrot` | 2 | Overworld | Jungle parrots |
| `minecraft:ravager` | 2 | Overworld | Combat challenges in maze |
| `minecraft:vex` | 2 | Overworld | Maze combat challenges |
| `minecraft:evoker_fangs` | 1 | Overworld | Temporary combat entity |
| `minecraft:experience_orb`| 1 | Overworld | Temporary orb entity |
| `minecraft:villager` | 1 | Overworld | Custom placed villager in Sector 13 ("Angus") |
| `minecraft:ghast` | 1 | Nether | Native mob |

---

### 4. Special & Curated Entities

#### 4.1. Armor Stands
- **`[99998.5, 105.5, 99956.5]`**: Marker named `Beta Testers` (green, bold).
- **`[99996.5, 105.0, 99955.5]`**: Statue of `Cyohg` (diamond boots, chainmail leggings, iron chestplate, custom head).
- **`[100000.5, 105.0, 99955.5]`**: Statue of `LordOfGnou` (chain boots, iron leggings, green dyed leather chestplate, custom head).
- **`[99979.5, 105.0, 99983.5]`**: Statue of `NereidRegulus` (creator) with dyed leather armor set and custom head.
- **`[99979.5, 105.0, 99987.5]`**: Statue of `Cafeslayeur` (creator) with netherite chestplate and custom head.
- **`[277.59, 1.0, -2197.21]`**: Technical redstone marker.

#### 4.2. Item Frames
- **Spawn / Lobby**:
  - `[377.03, 6.5, -2131.5]` & `[377.03, 6.5, -2133.5]`: Written Book `"Objective"` by `Nereid` detailing wool monuments and victory conditions.
  - `[385.97, 6.5, -2131.5]` & `[385.97, 6.5, -2133.5]`: Written Book `"Rules"` by `Nereid` stating difficulty constraints.
- **Sector 13**:
  - `[963.5, 147.0, 1142.5]`: Raw Salmon.
  - `[961.0, 146.5, 1144.5]`: Raw Cod.
  - `[963.5, 147.0, 1144.5]`: Tropical Fish.

#### 4.3. Progressive NPCs (`generates_npc.mcfunction`)
1. **Bruce** (Day 4) - Savanna Farmer (`264, 59, -2184`)
2. **Boris** (Day 9) - Savanna Shepherd (`264, 59, -2184`)
3. **Joe** (Day 13) - Savanna Fletcher (`264, 59, -2184`)
4. **Tobias** (Day 17) - Savanna Weaponsmith (`264, 59, -2184`)
5. **George** (Day 21) - Savanna Butcher (`264, 59, -2184`)
6. **Erik** (Day 26) - Savanna Cleric (`264, 59, -2184`)
7. **Adam** (Day 31) - Savanna Mason (`264, 59, -2184`)
8. **Joakim** (Day 38) - Savanna Armorer (`264, 59, -2184`)
9. **Seth** (Day 47) - Savanna Librarian (`264, 59, -2184`)
10. **Jörn** (Day 55) - Savanna Cartographer (`264, 59, -2184`)

#### 4.4. Exploration NPCs (Command Blocks)
11. **Ylva** - Jungle Armorer (Netherite and custom armor)
12. **Jonne** - Jungle Cleric (Custom potions & lingering brews)
13. **Heri** - Jungle Weaponsmith (Enchanted weapons & trident)
14. **Kai** - Jungle Fletcher (Special arrows)
15. **Angus** - Jungle Librarian (Enchanted books)

---

### 5. Detailed Mapping Table (Java 1.16.5 -> Bedrock 1.26.40)

| Java Identifier | Qty | Dimension | Position | Rotation | Name | Behavior | Bedrock Destination | Responsible Component |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `minecraft:strider` | 359 | nether | `[-460.8, 31.5, -475.9]` | `[27.2, 0.0]` | None | Passive | `strider` (Bedrock vanilla) | Native Bedrock Spawning |
| `minecraft:sheep` | 282 | overworld | `[-84.7, 76.0, -20.3]` | `[315.0, 0.0]` | None | Passive | `sheep` (Bedrock vanilla) | Native Bedrock Spawning |
| `minecraft:item` | 213 | overworld | `[-503.1, 68.0, -2035.3]` | `[344.7, 0.0]` | None | Object / Drop | Ignored / Non-essential test drops | Filtered out |
| `minecraft:pig` | 195 | overworld | `[-134.8, 80.0, -121.3]` | `[228.1, 0.0]` | None | Passive | `pig` (Bedrock vanilla) | Native Bedrock Spawning |
| `minecraft:chicken` | 178 | overworld | `[-147.5, 80.0, 14.7]` | `[51.4, 0.0]` | None | Passive | `chicken` (Bedrock vanilla) | Native Bedrock Spawning |
| `minecraft:cow` | 149 | overworld | `[-134.0, 75.0, -52.0]` | `[315.0, 0.0]` | None | Passive | `cow` (Bedrock vanilla) | Native Bedrock Spawning |
| `minecraft:falling_block` | 136 | overworld | `[637.5, 154.0, -3024.5]` | `[0.0, 0.0]` | None | Trap / Block | `sand` (Static block / falling) | `custom/enable_block_fall.mcfunction` |
| `minecraft:rabbit` | 133 | overworld | `[-7128.0, 65.0, -75.0]` | `[270.6, 0.0]` | None | Passive | `rabbit` (Bedrock vanilla) | Native Bedrock Spawning |
| `minecraft:shulker` | 109 | overworld | `[4984.5, 78.0, -5040.5]` | `[0.0, 0.0]` | None | Hostile | `shulker` + Emerald loot table | `loot_tables/entities/shulker.json` |
| `minecraft:wolf` | 37 | overworld | `[-558.5, 69.0, -1879.5]` | `[135.0, 0.0]` | None | Passive | `wolf` (Bedrock vanilla) | Native Bedrock Spawning |
| `minecraft:creeper` | 17 | overworld | `[-48.9, 41.0, -59.0]` | `[321.6, 0.0]` | None | Hostile | `creeper` + Emerald loot table | `loot_tables/entities/creeper.json` |
| `minecraft:zombie` | 12 | overworld | `[-44.2, 41.0, -45.2]` | `[135.5, 0.0]` | None | Hostile | `zombie` + Emerald loot table | `loot_tables/entities/zombie.json` |
| `minecraft:skeleton` | 8 | overworld | `[-41.5, 43.0, -31.5]` | `[167.8, 0.0]` | {"text":"Steve"} | Hostile | `skeleton` + Emerald loot table | `loot_tables/entities/skeleton.json` |
| `minecraft:item_frame` | 7 | overworld | `[377.0, 6.5, -2131.5]` | `[270.0, 0.0]` | None | Static | `frame` (Bedrock item frame) | Native Bedrock / Chunker |
| `minecraft:armor_stand` | 6 | overworld | `[277.6, 1.0, -2197.2]` | `[0.0, 0.0]` | Creator names | Static | `armor_stand` (Hall of Fame) | `mazerunner/setup_hall_of_fame.mcfunction` |
| `minecraft:phantom` | 5 | nether | `[762.4, 176.7, -201.6]` | `[-112.7, -7.2]` | None | Hostile | `phantom` + Emerald loot table | `loot_tables/entities/phantom.json` |
| `minecraft:elder_guardian` | 2 | overworld | `[279.2, 30.1, -1633.2]` | `[250.8, 0.0]` | None | Hostile | `elder_guardian` + Emerald loot | `loot_tables/entities/elder_guardian.json` |
| `minecraft:villager` | 1 | overworld | `[967.2, 135.0, 1180.2]` | `[313.0, 0.0]` | {"text":"Angus"} | Passive | `mazerunner:npc_angus` | `entities/npc_angus.json` |
