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
  ```
- **Bedrock 1.26.40**:
  ```mcfunction
  playsound random.levelup @p
  ```

#### 1.3. `/summon` com Garantia de Idempotência
- Comandos de invocação de NPCs em funções são envolvidos automaticamente com verificação de existência para evitar duplicação:
  ```mcfunction
  execute unless entity @e[type=namespace:npc_name] run summon namespace:npc_name <x> <y> <z>
  ```

#### 1.4. `/forceload` $\rightarrow$ `/tickingarea`
- O comando `/forceload` da Java Edition é documentado como comentário na função e substituído pela criação de simulação contínua com `/tickingarea` na inicialização do mundo.

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
  ```
- **Bedrock 1.26.40**:
  ```mcfunction
  playsound random.levelup @p
  ```

#### 1.3. `/summon` with Guaranteed Idempotency
- NPC summon commands inside `.mcfunction` files are automatically wrapped with existence checks to prevent duplication:
  ```mcfunction
  execute unless entity @e[type=namespace:npc_name] run summon namespace:npc_name <x> <y> <z>
  ```

#### 1.4. `/forceload` $\rightarrow$ `/tickingarea`
- Java `/forceload` lines are documented as informative comments in functions and replaced by persistent simulation areas using `/tickingarea` during world initialization.
