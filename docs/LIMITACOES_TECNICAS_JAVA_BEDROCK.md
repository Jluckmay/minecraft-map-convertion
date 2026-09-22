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

