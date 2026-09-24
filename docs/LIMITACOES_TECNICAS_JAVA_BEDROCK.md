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
| **Sensores de Luz Solar no Subsolo (Ciclo Dia/Noite)** | Motor automatizado de 24.000 ticks em `tick.mcfunction` (`cycle_morning` e `cycle_night`) | Substituição de daylight detectors subterrâneos por relógio em software com sincronização de score | No Bedrock, sensores sob blocos opacos têm `sky light = 0` constante e nunca emitem pulso de redstone ao mudar o dia. |
| **Exibição de Placar em Rawtext (`DAY_COUNTER`)** | Rawtext `{"score": {"name": "@p", "objective": "dayCounter"}}` | Sincronização contínua de `DAY_COUNTER` para `@a` e substituição de nomes dummy por `@p` no rawtext | O parser JSON do Bedrock não resolve scores de fake players como `DAY_COUNTER`, exigindo seletores válidos (`@p` ou `@s`). |
| **Spawn de Aldeões em Dias Específicos** | Entidades customizadas (`npc_<slug>`) com faixa `matches X..` e guarda `unless entity` | Invocação resiliente e anúncio único no chat | Checagem estrita de um único tick pode ser perdida em transições; o range `matches X..` com guarda garante spawn sem duplicação. |
| **Sons de Portão e Mobs Especiais (`entity.illusioner.*`)** | Catálogo `sounds/sound_definitions.json` | Mapeamento formal de eventos sonoros e arquivos `.ogg` no Resource Pack | O Illusioner não existe nativamente no Bedrock; a engine exige registro explícito em `sound_definitions.json` para reproduzir o áudio. |
| **Limite Global de Ticking Areas (100 Chunks no Mundo)** | `tickingarea add` (máx. 100 chunks somados em todo o mundo) | Dimensionamento compacto em 2 áreas estratégicas totalizando 76 chunks | O Bedrock rejeita qualquer ticking area se a soma de chunks de todas as áreas do mundo exceder 100 chunks. |

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
| **Underground Daylight Detectors (Day/Night Cycle)** | Automated 24,000 tick engine in `tick.mcfunction` (`cycle_morning` and `cycle_night`) | Software-driven daytime clock replacing buried daylight detectors with scoreboard sync | In Bedrock, detectors under opaque blocks have constant `sky light = 0` and never trigger day/night pulses. |
| **Rawtext Score Display (`DAY_COUNTER`)** | Rawtext `{"score": {"name": "@p", "objective": "dayCounter"}}` | Continuous sync from `DAY_COUNTER` to `@a` and dummy name conversion to `@p` | Bedrock JSON parser does not resolve arbitrary dummy scoreboard names; requires valid entity selectors (`@p` or `@s`). |
| **Day-Specific Villager Spawning** | Custom entities (`npc_<slug>`) with `matches X..` and `unless entity` guard | Resilient summoning and single-fire chat announcements | Single-tick exact checks can be missed during chunk loads; `matches X..` with existence guard guarantees idempotency. |
| **Gate & Special Mob Sounds (`entity.illusioner.*`)** | `sounds/sound_definitions.json` catalog | Explicit registration of audio events and `.ogg` files in Resource Pack | Illusioner is absent natively in Bedrock; engine mandates `sound_definitions.json` to map `/playsound` events to audio. |
| **World Ticking Area Limit (100 Chunks Total)** | `tickingarea add` (max 100 chunks combined world-wide) | Compact 2-area strategic layout totaling 76 chunks | Bedrock rejects any ticking area addition once the world-wide total chunk sum exceeds 100 chunks. |

