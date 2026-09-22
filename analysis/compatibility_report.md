# Relatório de Compatibilidade Java -> Bedrock (Seção 28)

Classificação detalhada dos componentes encontrados por nível de compatibilidade:

### [GREEN] Conversão Direta
- **Scoreboards Dummy**: `scoreboard objectives add <name> dummy` e operações numéricas de players.
- **Tags de Entidades**: `tag @e add <name>`, `tag @e remove <name>` e seletores `@e[tag=...]`.
- **Comandos Básicos de Mundo**: `gamerule`, `weather`, `time`, `difficulty`, `tp`, `clear`, `kill`.
- **Blocos Básicos**: `clone`, `setblock` e `fill` (com remoção de prefixos `minecraft:`).

### [YELLOW] Conversão com Adaptação de Sintaxe
- **Subcomandos de Execute**: `execute as`, `at`, `positioned`, `positioned as`, `if/unless entity` (adaptados para sintaxe Bedrock 1.20+).
- **Seletores de Distância**: `distance=..X` adaptado para `r=X`, `distance=X..Y` adaptado para `rm=X,r=Y`.
- **Seletores de Limite**: `limit=1,sort=nearest` adaptados para `c=1`.
- **Áudio e Efeitos**: `playsound` mapeando IDs Java (`entity.player.levelup`) para Bedrock (`random.levelup`) e removendo categoria `master`.
- **Textos Formatados**: `tellraw` e `title` convertidos do formato JSON Java para o formato `{"rawtext":[...]}` com códigos de cor `§`.
- **Forceload**: `/forceload add/remove` traduzidos para cálculos de coordenadas em `tickingarea add/remove`.

### [ORANGE] Conversão com Reimplementação
- **NBT em Invocação de Entidades**: `/summon villager` com NBT de ofertas (`Recipes:[...]`) e nomes personalizados convertidos para entidades customizadas (`custom:npc_<nome>`) e tabelas de trocas Bedrock (`trading/*.json`).
- **Spawners**: `/data merge block <x> <y> <z> {Delay:0}` convertidos para `setblock <x> <y> <z> mob_spawner`.
- **Itens com NBT Especial**: Livros e itens com NBT complexo normalizados para identificadores de item Bedrock com metadados.

### [RED] Sem Equivalente Direto / Intervenção Especial
- **Comandos de NBT Dinâmico Arbitrário**: `/data get/modify` em runtime não possuem equivalente direto em comandos vanilla Bedrock (tratados via scoreboards e tags auxiliares).
- **Efeito Glowing**: O efeito `glowing` é exclusivo da Java Edition e foi substituído por `invisibility` invertido ou marcador de partícula no Bedrock.

