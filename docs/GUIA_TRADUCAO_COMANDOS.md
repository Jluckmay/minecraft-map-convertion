# Guia de Tradução de Comandos / Command Translation Guide (Java -> Bedrock 1.26.40+)

*Read in / Leia em:*
- [Português (PT-BR)](#português-pt-br)
- [English (EN)](#english-en)

---

<a name="português-pt-br"></a>
## Português (PT-BR)

Este guia documenta como o motor do `map_converter.py` traduz a sintaxe de comandos da Java Edition para a sintaxe moderna do Bedrock Edition 1.26.40+.

### 1. Principais Regras de Tradução

#### 1.1. `/tellraw`
- **Java**:
  ```mcfunction
  tellraw @a {"text":"Ola mundo","color":"green"}
  ```
- **Bedrock 1.26.40**:
  ```mcfunction
  tellraw @a {"rawtext":[{"text":"§aOla mundo"}]}
  ```
- O conversor mapeia atributos de cor (`green` $\rightarrow$ `§a`, `gold` $\rightarrow$ `§6`, `red` $\rightarrow$ `§c`, etc.) diretamente no payload `rawtext`.

#### 1.2. `/playsound`
- **Java**:
  ```mcfunction
  playsound minecraft:entity.player.levelup master @p
  playsound minecraft:entity.illusioner.prepare_mirror master @a 173 64 -2148 0.7 1 0.03
  ```
- **Bedrock 1.26.40**:
  ```mcfunction
  playsound random.levelup @p
  playsound entity.illusioner.prepare_mirror @a 173 64 -2148 0.7 1 0.03
  ```
- O canal de áudio (`master`, `hostile`, etc.) é removido automaticamente por não ser suportado nessa posição pelo Bedrock, e os eventos customizados são mapeados e registrados formalmente no catálogo `sounds/sound_definitions.json`.

#### 1.3. `/summon` de Aldeões/NPCs e Mobs com Nome Customizado
- **Java (Aldeão com Ofertas/Nome)**:
  ```mcfunction
  execute if score DAY_COUNTER dayCounter matches 4 run summon minecraft:villager 264 59 -2184 {CustomName:'{"text":"Bruce"}'}
  ```
- **Bedrock 1.26.40**:
  ```mcfunction
  execute if score DAY_COUNTER dayCounter matches 4 run execute unless entity @e[type=mazescapist:npc_bruce] run summon mazescapist:npc_bruce 264 59 -2184
  ```
- O conversor detecta o aldeão nomeado com trocas, direciona para a entidade customizada com Behavior Pack (`economy_trade_table`) e insere a verificação `unless entity` para garantir idempotência.
- Para mobs comuns com nome customizado, gera a sintaxe posicional válida do Bedrock:
  ```mcfunction
  summon zombie 264 59 -2184 0 0 "" "Boss"
  ```

#### 1.4. `/forceload` $\rightarrow$ `/tickingarea`
- O comando `/forceload` da Java Edition é documentado como comentário na função e substituído pela criação de simulação contínua com `/tickingarea` na inicialização do mundo, respeitando o limite máximo do motor de 100 chunks por área.

#### 1.5. Resolução de Placar em `/tellraw` e `/titleraw`
- A Java Edition resolve placares de fake players nativamente em JSON (ex: `{"score": {"name": "DAY_COUNTER", "objective": "dayCounter"}}`).
- O Bedrock Edition também resolve nativamente nomes literais de fake players no componente `score` do `rawtext`. O tradutor preserva o nome `DAY_COUNTER` original, enquanto o behavior pack inicializa e sincroniza o contador com `@a` (`scoreboard players operation @a dayCounter = DAY_COUNTER dayCounter`).

---

<a name="english-en"></a>
## English (EN)

This guide documents how the `map_converter.py` engine translates Java Edition command syntax into modern Bedrock Edition 1.26.40+ syntax.

### 1. Core Translation Rules

#### 1.1. `/tellraw`
- **Java**:
  ```mcfunction
  tellraw @a {"text":"Hello world","color":"green"}
  ```
- **Bedrock 1.26.40**:
  ```mcfunction
  tellraw @a {"rawtext":[{"text":"§aHello world"}]}
  ```
- The converter maps color attributes (`green` $\rightarrow$ `§a`, `gold` $\rightarrow$ `§6`, `red` $\rightarrow$ `§c`, etc.) directly into the `rawtext` payload.

#### 1.2. `/playsound`
- **Java**:
  ```mcfunction
  playsound minecraft:entity.player.levelup master @p
  playsound minecraft:entity.illusioner.prepare_mirror master @a 173 64 -2148 0.7 1 0.03
  ```
- **Bedrock 1.26.40**:
  ```mcfunction
  playsound random.levelup @p
  playsound entity.illusioner.prepare_mirror @a 173 64 -2148 0.7 1 0.03
  ```
- The audio channel parameter (`master`, `hostile`, etc.) is stripped because Bedrock does not support it in this position, and custom sound events are formally registered in the `sounds/sound_definitions.json` catalog.

#### 1.3. `/summon` with Named NPCs and Entities
- **Java (Villager with Custom Name/Offers)**:
  ```mcfunction
  execute if score DAY_COUNTER dayCounter matches 4 run summon minecraft:villager 264 59 -2184 {CustomName:'{"text":"Bruce"}'}
  ```
- **Bedrock 1.26.40**:
  ```mcfunction
  execute if score DAY_COUNTER dayCounter matches 4 run execute unless entity @e[type=mazescapist:npc_bruce] run summon mazescapist:npc_bruce 264 59 -2184
  ```
- The converter detects custom traders, delegates to dedicated Behavior Pack entities with `economy_trade_table`, and inserts `unless entity` guards to ensure zero duplication upon repeated execution.
- Standard mobs with custom names are translated into valid Bedrock positional syntax:
  ```mcfunction
  summon zombie 264 59 -2184 0 0 "" "Boss"
  ```

#### 1.4. `/forceload` $\rightarrow$ `/tickingarea`
- Java `/forceload` lines are documented as informative comments in functions and replaced by persistent simulation areas using `/tickingarea` during world initialization, respecting the 100-chunk world-wide engine limit.

#### 1.5. `/tellraw` and `/titleraw` Scoreboard Resolution
- Java Edition resolves dummy player scoreboards natively in JSON text (e.g. `{"score": {"name": "DAY_COUNTER", "objective": "dayCounter"}}`).
- Bedrock Edition natively resolves literal fake player names in the `rawtext` score component (`{"score": {"name": "DAY_COUNTER", "objective": "dayCounter"}}`). The translator preserves the original scoreboard holder name directly, while the behavior pack initializes and synchronizes the day counter to `@a` (`scoreboard players operation @a dayCounter = DAY_COUNTER dayCounter`).

#### 1.6. Motor Automatizado de Ciclo Dia/Noite (`tick.mcfunction`)
- Como sensores de luz solar sob blocos opacos permanecem inertes no Bedrock (`sky light = 0`), a alternância de dia e noite é dirigida com precisão em software pelo `tick.mcfunction` (relógio de 24.000 ticks):
  - **Tick 12.000 (Pôr do Sol)**: Executa `cycle_night.mcfunction` (fechamento dos portões com bedrock, reprodução de áudio de portões e incremento do placar `DAY_COUNTER`).
  - **Tick 24.000 (Nascer do Sol)**: Executa `cycle_morning.mcfunction` (abertura dos portões, áudio, exibição do título "Day X", invocação de aldeões com `matches X..` e clonagem de baús de suprimentos).


