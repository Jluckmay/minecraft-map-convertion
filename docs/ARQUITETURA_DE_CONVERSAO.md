# Arquitetura Técnica de Conversão / Technical Conversion Architecture (Java -> Bedrock 1.26.40+)

*Read in / Leia em:*
- [Português (PT-BR)](#português-pt-br)
- [English (EN)](#english-en)

---

<a name="português-pt-br"></a>
## Português (PT-BR)

### 1. Visão Geral do Pipeline
A ferramenta atua como uma ponte técnica entre o **Minecraft Java Edition** e o **Minecraft Bedrock Edition (1.26.40+)**, complementando as conversões de terreno (feitas por ferramentas como o Chunker) com toda a lógica dinâmica, entidades, comércio e recursos visuais.

```text
[ Mundo Java (.zip) ]           [ Terreno Chunker (.mcworld) ]
         │                                    │
         ▼                                    ▼
┌──────────────────┐               ┌──────────────────┐
│ Auditoria Anvil  │               │ Descompactação   │
│ MCA, NBT, Datapack│               │ de Nível LevelDB │
└────────┬─────────┘               └────────┬─────────┘
         │                                  │
         ├──────────────────────────────────┤
         │
         ▼
┌────────────────────────────────────────────────────────┐
│             Motor de Conversão Complementar            │
│  - Extração NBT de trocas de aldeões (Trade Tables)    │
│  - Criação de Entidades Customizadas (BP/RP)           │
│  - Tradução e Modernização de Funções (.mcfunction)    │
│  - Conversão de Tabelas de Saque (Loot Tables)         │
│  - Extração de Texturas de Blocos (terrain_texture)    │
└────────────────────────┬───────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
┌──────────────────┐           ┌──────────────────┐
│  Pacotes Avulsos │           │  Mundo Integrado │
│  .mcpack (BP/RP) │           │  .mcworld final  │
└──────────────────┘           └──────────────────┘
```

---

### 2. Conversão de Comércio de Aldeões e NPCs Customizados
No Bedrock Edition, comandos `/summon` não aceitam tags NBT compostas como `{Offers:[...]}`. O conversor implementa a seguinte arquitetura nativa:
1. **Extração NBT Automatizada**:
   - O código inspeciona funções `.mcfunction` e blocos de comando em busca de `/summon villager ... {Offers:{Recipes:[...]}}`.
   - Lê os itens de compra (`buy`, `buyB`), itens de venda (`sell`), preços e quantidades.
2. **Geração de Tabelas de Troca Bedrock (`trading/*.json`)**:
   - Cria arquivos JSON nativos com níveis (`tiers`) e regras de comércio correspondentes.
3. **Definições de Entidades Customizadas**:
   - Gera definições de comportamento (`entities/npc_<id>.json`) com componentes de invulnerabilidade e posição de serviço.
   - Gera definições de cliente (`entity/npc_<id>.entity.json`) com modelos de aldeão e texturas por bioma e profissão.
4. **Idempotência Automática**:
   - Os comandos de summon recebem automaticamente a cláusula `unless entity @e[type=...]` para evitar duplicação em execuções repetidas.

---

### 3. Tradução de Tabelas de Saque (Loot Tables)
Converte tabelas de saque de entidades de datapacks Java para o formato Bedrock:
- Pools, rolls, funções `set_count` e `looting_enchant`.
- Preserva a economia customizada de drops de monstros do mapa.

---

### 4. Modernização de Funções (.mcfunction)
- Converte comandos `/tellraw` no formato JSON da Java Edition para a sintaxe `rawtext` do Bedrock, convertendo atributos de cores para códigos de seção (`§a`, `§6`, etc.).
- Traduz identificadores de eventos sonoros (`playsound`).
- Converte `/forceload` para áreas contínuas de simulação (`tickingarea`).

---

### 5. Catálogo de Definições de Áudio (`sound_definitions.json`)
- O Bedrock Edition exige o registro formal de qualquer evento de som customizado no catálogo `sounds/sound_definitions.json` do Resource Pack.
- Mapeia eventos sonoros como os do Illusioner (usados no Java para o efeito de pedra abrindo/fechando os portões), ghasts, cavalos-esqueleto e outros efeitos para os arquivos `.ogg` empacotados, evitando que comandos `/playsound` toquem em silêncio.

---

<a name="english-en"></a>
## English (EN)

### 1. Pipeline Overview
The tool serves as an automated engineering bridge between **Minecraft Java Edition** and **Minecraft Bedrock Edition (1.26.40+)**, complementing terrain conversion tools (such as Chunker) with dynamic logic, entities, trading systems, and visual assets.

---

### 2. Custom Villager Trading & NPC Conversion
In Bedrock Edition, `/summon` commands do not accept compound NBT tags such as `{Offers:[...]}`. The converter implements a native architecture:
1. **Automated NBT Extraction**:
   - Inspects `.mcfunction` files and command blocks for `/summon villager ... {Offers:{Recipes:[...]}}`.
   - Parses purchase items (`buy`, `buyB`), sell items (`sell`), prices, and quantities.
2. **Bedrock Trade Table Generation (`trading/*.json`)**:
   - Emits native Bedrock trade tables with tiers and trade definitions.
3. **Custom Entity Architecture**:
   - Generates behavior definitions (`entities/npc_<id>.json`) with damage resistance and locked coordinates.
   - Generates client entity definitions (`entity/npc_<id>.entity.json`) with biome clothing and profession textures.
4. **Guaranteed Idempotency**:
   - Summon commands are wrapped with `unless entity @e[type=...]` to ensure zero duplication upon repeated execution.

---

### 3. Loot Table Translation
Converts datapack mob loot tables from Java JSON to Bedrock JSON:
- Pools, rolls, `set_count`, and `looting_enchant` functions.
- Preserves custom monster drop economies across any map.

---

### 4. Function Modernization (.mcfunction)
- Translates Java `/tellraw` JSON objects into Bedrock `rawtext` syntax with embedded section color codes (`§a`, `§6`, etc.).
- Translates Java sound events to Bedrock sound identifiers (`playsound`).
- Adapts `/forceload` chunk loading into simulation areas (`tickingarea`).

---

### 5. Sound Definitions Catalog (`sound_definitions.json`)
- Bedrock Edition requires explicit event registration in `sounds/sound_definitions.json` inside the Resource Pack for custom audio.
- Binds sound events such as Illusioner effects (used in Java for sliding stone maze gate open/close audio), ghasts, and skeleton horses to local `.ogg` assets, preventing `/playsound` commands from producing silence.

