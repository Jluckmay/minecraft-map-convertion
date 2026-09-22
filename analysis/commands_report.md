# Relatório de Inventário de Comandos Java Edition

- **Total de Comandos**: 4392
- **Em Command Blocks**: 639
- **Em Datapacks**: 3753
- **Comandos com NBT**: 660

## Frequência de Comandos e Equivalência Bedrock

| Comando Java | Quantidade | Equivalente Bedrock | Status de Conversão |
| :--- | :---: | :--- | :--- |
| `forceload` | 2056 | `tickingarea` | YELLOW (Conversão para tickingarea add/remove) |
| `clone` | 1052 | `clone` | GREEN (Suporte direto) |
| `data` | 547 | `—` | ORANGE (Reimplementação via scoreboards/setblock) |
| `execute` | 174 | `execute` | YELLOW (Requer tradução de seletores e sintaxe 1.20+) |
| `setblock` | 145 | `setblock` | GREEN (Remoção de namespace minecraft:) |
| `fill` | 88 | `fill` | GREEN (Remoção de namespace minecraft:) |
| `particle` | 84 | `particle` | YELLOW (Mapeamento de nomes de partículas Java -> Bedrock) |
| `playsound` | 61 | `playsound` | YELLOW (Mapeamento de sound events e remoção de channel) |
| `tp` | 39 | `tp` | GREEN (Suporte direto) |
| `function` | 38 | `function` | YELLOW (namespace:nome -> namespace/nome) |
| `tellraw` | 34 | `tellraw` | YELLOW (Conversão para rawtext nativo Bedrock) |
| `effect` | 30 | `effect` | YELLOW (effect give <target> <effect> <duration> <amplifier>) |
| `summon` | 21 | `summon` | YELLOW/ORANGE (NBT requer conversão em entidade customizada Bedrock) |
| `title` | 5 | `title` | YELLOW (Conversão para rawtext nativo Bedrock) |
| `scoreboard` | 4 | `scoreboard` | GREEN (Suporte direto para dummy e operações) |
| `give` | 3 | `give` | YELLOW (Remoção de NBT complexo / mapping) |
| `gamerule` | 3 | `gamerule` | GREEN (Suporte direto com valores case-insensitive) |
| `time` | 2 | `time` | GREEN (Suporte direto) |
| `kill` | 2 | `kill` | GREEN (Suporte direto com seletores) |
| `setworldspawn` | 2 | `—` | RED (Sem mapeamento direto) |
| `difficulty` | 1 | `difficulty` | GREEN (Suporte direto) |
| `gamemode` | 1 | `—` | RED (Sem mapeamento direto) |

## Subcomandos de `/execute`

| Subcomando | Ocorrências | Estratégia Bedrock |
| :--- | :---: | :--- |
| `execute run` | 154 | Suportado nativamente na nova sintaxe execute Bedrock 1.20+ |
| `execute if` | 120 | Suportado nativamente na nova sintaxe execute Bedrock 1.20+ |
| `execute as` | 79 | Suportado nativamente na nova sintaxe execute Bedrock 1.20+ |
| `execute positioned` | 69 | Suportado nativamente na nova sintaxe execute Bedrock 1.20+ |
| `execute unless` | 3 | Suportado nativamente na nova sintaxe execute Bedrock 1.20+ |

## Seletores e Argumentos Utilizados

| Seletor / Argumento | Contagem | Classificação | Equivalente Bedrock |
| :--- | :---: | :--- | :--- |
| `@a` | 225 | [GREEN] | Suporte direto `@a` |
| `@p` | 115 | [GREEN] | Suporte direto `@p` |
| `distance=` | 66 | [YELLOW] | `r=X` ou `rm=X,r=Y` |
| `dx=` | 55 | [GREEN] | `dx=...` direto |
| `dy=` | 55 | [GREEN] | `dy=...` direto |
| `dz=` | 55 | [GREEN] | `dz=...` direto |
| `x=` | 43 | [GREEN] | `x=...` direto |
| `y=` | 43 | [GREEN] | `y=...` direto |
| `z=` | 43 | [GREEN] | `z=...` direto |
| `@e` | 23 | [GREEN] | Suporte direto `@e` |
| `tag=` | 14 | [GREEN] | `tag=...` direto |
| `type=` | 13 | [GREEN] | `type=...` direto |
| `@s` | 6 | [GREEN] | Suporte direto `@s` |
| `nbt=` | 1 | [ORANGE] | Requer tag auxiliar ou scoreboard |
| `gamemode=` | 1 | [RED] | Requer revisão manual |
