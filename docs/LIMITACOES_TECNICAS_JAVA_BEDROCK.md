# Limitações Técnicas e Diferenças de Engine / Technical Limitations & Engine Differences (Java vs Bedrock)

*Read in / Leia em:*
- [Português (PT-BR)](#português-pt-br)
- [English (EN)](#english-en)

---

<a name="português-pt-br"></a>
## Português (PT-BR)

Ao converter mapas e datapacks de **Minecraft Java Edition** para **Minecraft Bedrock Edition (1.26.40+)**, algumas mecânicas exigem adaptação técnica devido a diferenças fundamentais de arquitetura entre as duas plataformas.

### Tabela de Comparação Técnica

| Recurso (Java Edition) | Equivalente / Comportamento (Bedrock 1.26.40) | Estratégia Adotada pelo Conversor | Justificativa Técnica |
| :--- | :--- | :--- | :--- |
| **Comando `/forceload`** | `/tickingarea` | Conversão para áreas de simulação contínua na inicialização | Bedrock não possui `/forceload` baseado em chunks. O limite de `tickingarea` é de 10 por mundo. |
| **Comando `/data merge block`** | Mecânicas nativas de componentes e blocos | Substituição por blocos nativos ou ativação por proximidade | Bedrock Edition não permite manipular diretamente NBT de blocos em tempo de execução via comandos. |
| **Tags NBT em `/summon` (`{Offers:[...]}`)** | Tabelas de troca nativas (`trading/*.json`) | Geração de arquivos JSON de comércio e entidades customizadas | Bedrock não aceita NBT livre na linha de comando de invocação. |
| **`/tellraw` com JSON puro** | `/tellraw` com `{"rawtext": [...]}` e códigos de formatação | Conversão de tags de cores para códigos `§` | Bedrock utiliza uma sintaxe de texto cru diferente para formatação no chat. |
| **Flecha Espectral (`spectral_arrow`)** | Flechas com efeitos de poção / flechas comuns | Substituição transparente na tabela de comércio | Flechas espectrais com contorno brilhante são exclusivas da Java Edition. |
| **Livros abertos em molduras** | Moldura convencional com o item livro | Preservação do texto em relatórios e documentação | No Bedrock, molduras não exibem o NBT de páginas abertas formatadas diretamente na face do bloco. |
| **Baús e Contêineres de Blocos** | `Chest`, `Barrel`, `ShulkerBox`, `Hopper`, `Dispenser` | Preservação total no banco LevelDB | O conversor lê e mantém 100% dos blocos e compostos NBT de itens, slots e quantidades no LevelDB. |
| **Inventário do Jogador e Playerdata** | Entidade `~local_player` no LevelDB | Sincronização automática para `~local_player` | Itens de inventário, armaduras, offhand e Ender Chest são mapeados de `level.dat`/`playerdata` para o jogador local Bedrock. |
| **Loot Tables de Mobs (Drops de Esmeraldas)** | `loot_tables/entities/*.json` no Behavior Pack | Conversão automática de pools, rolls, `set_count` e `looting_enchant` | Mobs no Bedrock recorrem aos drops vanilla padrão se o Behavior Pack não fornecer os arquivos de loot table convertidos. |
| **Ciclo de Dias e Spawn de Aldeões** | Entidades customizadas (`npc_<slug>`) e scoreboards | Invocação de entidades dedicadas com trocas (`economy_trade_table`) e inicialização em `init_world.mcfunction` | Sintaxe `/summon villager "Name"` é rejeitada no Bedrock; aldeões vanilla não aceitam NBT de trocas por comando. |
| **Sons de Portão e Mobs Especiais (`entity.illusioner.*`)** | Catálogo `sounds/sound_definitions.json` | Mapeamento formal de eventos sonoros e arquivos `.ogg` no Resource Pack | O Illusioner não existe nativamente no Bedrock; a engine exige registro explícito em `sound_definitions.json` para reproduzir o áudio. |
| **Limite de Tamanho de Áreas de Ticking** | `tickingarea add` (máx. 100 chunks por área) | Dimensionamento automático de coordenadas dentro do limite de 100 chunks | O Bedrock rejeita a criação de áreas de simulação contínua que ultrapassem 100 chunks (10x10 chunks). |

---

<a name="english-en"></a>
## English (EN)

When converting worlds and datapacks from **Minecraft Java Edition** to **Minecraft Bedrock Edition (1.20+ / 1.21+)**, several mechanics require technical adaptation due to core engine differences.

### Technical Comparison Table

| Java Edition Feature | Bedrock 1.20+/1.21+ Equivalent | Converter Strategy | Technical Reason |
| :--- | :--- | :--- | :--- |
| **`/forceload` command** | `/tickingarea` | Converted into permanent ticking areas during world initialization | Bedrock lacks chunk-based `/forceload`. Worlds support up to 10 ticking areas simultaneously. |
| **`/data merge block` command** | Native block & component mechanics | Replaced by native proximity or component behaviors | Bedrock does not support arbitrary runtime block NBT manipulation via commands. |
| **NBT tags in `/summon` (`{Offers:[...]}`)** | Native trade tables (`trading/*.json`) | Automated generation of JSON trade tables and custom entities | Bedrock `/summon` command does not accept compound NBT payloads. |
| **`/tellraw` with raw JSON** | `/tellraw` with `{"rawtext": [...]}` and section formatting | Converted to section sign formatting (`§a`, `§6`, etc.) | Bedrock uses a distinct rawtext syntax for formatted chat output. |
| **Spectral Arrow (`spectral_arrow`)** | Tipped arrows / regular high-damage arrows | Transparent fallback in NPC trade tables | Spectral arrows with glowing outlines are exclusive to Java Edition. |
| **Open books in item frames** | Regular item frame displaying written book item | Documented in reports and manuals | Bedrock item frames do not render open formatted multi-page book text on block faces. |
| **Block Chests & Containers** | `Chest`, `Barrel`, `ShulkerBox`, `Hopper`, `Dispenser` | Full preservation in LevelDB database | The converter preserves 100% of container block entities, items, slots, and counts in LevelDB. |
| **Playerdata and Inventories** | `~local_player` LevelDB entity | Automated synchronization to `~local_player` | Inventory, armor, offhand, and Ender Chest items from Java `level.dat`/`playerdata` are mapped to local Bedrock player. |
| **Mob Loot Tables (Emerald Drops)** | `loot_tables/entities/*.json` in Behavior Pack | Automated conversion of pools, rolls, `set_count`, and `looting_enchant` | Bedrock mobs fall back to vanilla loot unless the Behavior Pack explicitly supplies converted loot tables. |
| **Day Cycle & Specific Villager Spawns** | Custom entities (`npc_<slug>`) and scoreboards | Dedicated trade entity summoning (`economy_trade_table`) and initialization in `init_world.mcfunction` | `/summon villager "Name"` fails Bedrock syntax; vanilla villagers cannot receive NBT trades via command line. |
| **Gate & Special Mob Sounds (`entity.illusioner.*`)** | `sounds/sound_definitions.json` catalog | Explicit registration of audio events and `.ogg` files in Resource Pack | Illusioner is absent natively in Bedrock; engine mandates `sound_definitions.json` to map `/playsound` events to audio. |
| **Ticking Area Size Limit** | `tickingarea add` (max 100 chunks per area) | Automated chunk bounding box clamping within the 100-chunk ceiling | Bedrock silently fails or errors on any ticking area exceeding 100 chunks (10x10 chunks). |

