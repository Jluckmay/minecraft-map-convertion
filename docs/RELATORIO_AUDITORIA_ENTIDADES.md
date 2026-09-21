# Relatório de Auditoria de Entidades e Jogadores (Java 1.16.5)

## 1. Dados Globais do Mundo Java
- **Nome do Nível**: `Mazescapist` (`§4§lMazescapist`)
- **Versão Java**: 1.16.5 (DataVersion 2586)
- **Coordenadas de Spawn**: `X: 381, Y: 5, Z: -2171` (Lobby central do labirinto)
- **Dimensões Auditadas**:
  - Overworld (`region/`): 259 arquivos MCA
  - Nether (`DIM-1/region/`): 41 arquivos MCA
  - Total de entidades extraídas: **2.031 entidades**

## 2. Auditoria Individual de Jogadores (Playerdata)
Foram encontrados e auditados dois arquivos de playerdata no mundo Java:

| Jogador | UUID | Dimensão | Posição (X, Y, Z) | Modo | Vida | XP | Inventário | Ender Chest | Efeitos | Veículo |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **NereidRegulus** | `370fb06a-0d01-43b7-984c-8cbb7d03bfc5` | `minecraft:overworld` | `381.49, 5.00, -2170.52` | Sobrevivência (0) | 20.0 | Nível 0 (0.0) | **Vazio** | **Vazio** | Nenhum | Nenhum |
| **Cafeslayeur** | `7efa11a0-7b4f-4292-948e-796cceccd1ef` | `minecraft:overworld` | `381.53, 5.00, -2170.74` | Sobrevivência (0) | 20.0 | Nível 0 (0.0) | **Vazio** | **Vazio** | Nenhum | Nenhum |

Ambos os jogadores estavam posicionados exatamente no lobby de entrada do mapa, desprovidos de itens no inventário ou baú do fim, o que confirma que o mapa foi salvo em estado limpo de distribuição.

---

## 3. Censo Completo de Entidades nas Regiões Java
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

## 4. Entidades Especiais e Curadas

### 4.1. Suportes de Armadura (Armor Stands)
- **`[99998.5, 105.5, 99956.5]`**: Marcador nomeado `Beta Testers` (verde, negrito).
- **`[99996.5, 105.0, 99955.5]`**: Estátua de `Cyohg` (botas de diamante, calça de cota de malha, peitoral de ferro, cabeça customizada com textura URL: `b06f7164...`).
- **`[100000.5, 105.0, 99955.5]`**: Estátua de `LordOfGnou` (botas de malha, calça de ferro, peitoral de couro tingido de verde, cabeça customizada com textura URL: `dea1088f...`).
- **`[99979.5, 105.0, 99983.5]`**: Estátua de `NereidRegulus` (criador) com conjunto completo de armadura de couro tingido e cabeça customizada com textura URL: `9cb11941...`.
- **`[99979.5, 105.0, 99987.5]`**: Estátua de `Cafeslayeur` (criador) com botas e calça de couro tingido, peitoral de netherita e cabeça customizada com textura URL: `62794a25...`.
- **`[277.59, 1.0, -2197.21]`**: Suporte técnico de suporte ao mecanismo do labirinto.

### 4.2. Molduras com Itens (Item Frames)
- **Spawn / Lobby**:
  - `[377.03, 6.5, -2131.5]` e `[377.03, 6.5, -2133.5]`: Livro Escrito `"Objective"` por `Nereid` contendo os objetivos do labirinto e monumentos de lã.
  - `[385.97, 6.5, -2131.5]` e `[385.97, 6.5, -2133.5]`: Livro Escrito `"Rules"` por `Nereid` com regras de não alterar dificuldade para pacífico e evitar quebrar blocos.
- **Setor 13**:
  - `[963.5, 147.0, 1142.5]`: Salmão cru.
  - `[961.0, 146.5, 1144.5]`: Bacalhau cru.
  - `[963.5, 147.0, 1144.5]`: Peixe tropical.

### 4.3. NPCs Progressivos da Função `generates_npc.mcfunction`
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

### 4.4. NPCs de Exploração (Blocos de Comando)
11. **Ylva** - Armeira Selva (Armaduras personalizadas e netherita)
12. **Jonne** - Clérigo Selva (Poções customizadas e poções persistentes)
13. **Heri** - Armeiro Selva (Armas encantadas e tridente)
14. **Kai** - Flecheiro Selva (Flechas especiais com efeitos de poção)
15. **Angus** - Bibliotecário Selva (Livros encantados)


---

# Tabela Detalhada de Mapeamento de Entidades (Java 1.16.5 para Bedrock 1.26.40)

| Identificador Java | Qtd | Dimensão | Posição | Rotação | Nome | UUID (Exemplo) | Tags | Equipamentos | Efeitos | Variante | Comportamento | Destino Bedrock | Arquivo Responsável |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `minecraft:strider` | 359 | nether | `Ex: [-460.8, 31.5, -475.9]` | `Ex: [27.2, 0.0]` | Nenhum | `[-181037...` | Nenhuma | Padrão | Nenhum | Padrão | Passivo | strider (Bedrock vanilla) | `Nativo Bedrock / Spawn` |
| `minecraft:sheep` | 282 | overworld | `Ex: [-84.7, 76.0, -20.3]` | `Ex: [315.0, 0.0]` | Nenhum | `[1977375...` | Nenhuma | Padrão | Nenhum | Cor 0 | Passivo | sheep (Bedrock vanilla) | `Nativo Bedrock / Spawn` |
| `minecraft:item` | 213 | overworld | `Ex: [-503.1, 68.0, -2035.3]` | `Ex: [344.7, 0.0]` | Nenhum | `[-273602...` | Nenhuma | Padrão | Nenhum | Padrão | Objeto / Estático | item (Drop temporário desnecessário) | `Descarte / Não transferido` |
| `minecraft:pig` | 195 | overworld | `Ex: [-134.8, 80.0, -121.3]` | `Ex: [228.1, 0.0]` | Nenhum | `[2985300...` | Nenhuma | Padrão | Nenhum | Padrão | Passivo | pig (Bedrock vanilla) | `Nativo Bedrock / Spawn` |
| `minecraft:chicken` | 178 | overworld | `Ex: [-147.5, 80.0, 14.7]` | `Ex: [51.4, 0.0]` | Nenhum | `[6919859...` | Nenhuma | Padrão | Nenhum | Padrão | Passivo | chicken (Bedrock vanilla) | `Nativo Bedrock / Spawn` |
| `minecraft:cow` | 149 | overworld | `Ex: [-134.0, 75.0, -52.0]` | `Ex: [315.0, 0.0]` | Nenhum | `[-177355...` | Nenhuma | Padrão | Nenhum | Padrão | Passivo | cow (Bedrock vanilla) | `Nativo Bedrock / Spawn` |
| `minecraft:falling_block` | 136 | overworld | `Ex: [637.5, 154.0, -3024.5]` | `Ex: [0.0, 0.0]` | Nenhum | `N/A` | Nenhuma | Padrão | Nenhum | Padrão | Objeto / Estático | sand (Bloco estático / queda) | `custom/enable_block_fall.mcfunction` |
| `minecraft:rabbit` | 133 | overworld | `Ex: [-7128.0, 65.0, -75.0]` | `Ex: [270.6, 0.0]` | Nenhum | `N/A` | Nenhuma | Padrão | Nenhum | Padrão | Passivo | rabbit (Bedrock vanilla) | `Nativo Bedrock / Spawn` |
| `minecraft:shulker` | 109 | overworld | `Ex: [4984.5, 78.0, -5040.5]` | `Ex: [0.0, 0.0]` | Nenhum | `[-159923...` | Nenhuma | Padrão | Nenhum | Padrão | Hostil | shulker (Bedrock) + Loot de Esmeraldas | `loot_tables/entities/shulker.json` |
| `minecraft:wolf` | 37 | overworld | `Ex: [-558.5, 69.0, -1879.5]` | `Ex: [135.0, 0.0]` | Nenhum | `[7955051...` | Nenhuma | Padrão | Nenhum | Padrão | Passivo | wolf (Bedrock vanilla) | `Nativo Bedrock / Spawn` |
| `minecraft:llama` | 36 | overworld | `Ex: [-126.0, 104.0, 165.0]` | `Ex: [336.6, 0.0]` | Nenhum | `[-137019...` | Nenhuma | Padrão | Nenhum | Padrão | Passivo | llama (Bedrock vanilla) | `Nativo Bedrock / Spawn` |
| `minecraft:horse` | 36 | overworld | `Ex: [-44.0, 71.0, 1045.0]` | `Ex: [22.4, 0.0]` | Nenhum | `N/A` | Nenhuma | Padrão | Nenhum | Var 2 | Passivo | horse (Bedrock vanilla) | `Nativo Bedrock / Spawn` |
| `minecraft:fox` | 31 | overworld | `Ex: [-506.6, 65.0, -2100.5]` | `Ex: [136.8, 0.0]` | Nenhum | `[-208539...` | Nenhuma | Padrão | Nenhum | Padrão | Passivo | fox (Bedrock vanilla) | `Nativo Bedrock / Spawn` |
| `minecraft:bee` | 29 | overworld | `Ex: [-508.8, 83.0, -2168.3]` | `Ex: [41.9, 0.0]` | Nenhum | `[-142219...` | Nenhuma | Padrão | Nenhum | Padrão | Passivo | bee (Bedrock vanilla) | `Nativo Bedrock / Spawn` |
| `minecraft:creeper` | 17 | overworld | `Ex: [-48.9, 41.0, -59.0]` | `Ex: [321.6, 0.0]` | Nenhum | `[-469665...` | Nenhuma | Padrão | Nenhum | Padrão | Hostil | creeper (Bedrock) + Loot de Esmeraldas | `loot_tables/entities/creeper.json` |
| `minecraft:zombie` | 12 | overworld | `Ex: [-44.2, 41.0, -45.2]` | `Ex: [135.5, 0.0]` | Nenhum | `[-161632...` | Nenhuma | Customizado | Sim | Padrão | Hostil | zombie (Bedrock) + Loot de Esmeraldas | `loot_tables/entities/zombie.json` |
| `minecraft:pig` | 10 | nether | `Ex: [268.5, 139.0, -177.7]` | `Ex: [353.6, 0.0]` | Nenhum | `[9164434...` | Nenhuma | Padrão | Nenhum | Padrão | Passivo | pig (Bedrock vanilla) | `Nativo Bedrock / Spawn` |
| `minecraft:turtle` | 9 | overworld | `Ex: [-7113.0, 63.0, -171.0]` | `Ex: [197.0, 0.0]` | Nenhum | `N/A` | Nenhuma | Padrão | Nenhum | Padrão | Passivo | turtle (Bedrock vanilla) | `Nativo Bedrock / Spawn` |
| `minecraft:bat` | 8 | overworld | `Ex: [-54.5, 38.1, -18.5]` | `Ex: [1666.8, 0.0]` | Nenhum | `[1887004...` | Nenhuma | Padrão | Nenhum | Padrão | Passivo | bat (Bedrock vanilla) | `Nativo Bedrock / Spawn` |
| `minecraft:skeleton` | 8 | overworld | `Ex: [-41.5, 43.0, -31.5]` | `Ex: [167.8, 0.0]` | {"text":"Steve"} | `[7876474...` | Nenhuma | Padrão | Nenhum | Padrão | Hostil | skeleton (Bedrock) + Loot de Esmeraldas | `loot_tables/entities/skeleton.json` |
| `minecraft:item_frame` | 7 | overworld | `Ex: [377.0, 6.5, -2131.5]` | `Ex: [270.0, 0.0]` | Nenhum | `[5758764...` | Nenhuma | Padrão | Nenhum | Padrão | Objeto / Estático | frame (Bedrock item frame) | `Nativo Bedrock / Chunker` |
| `minecraft:item` | 6 | nether | `Ex: [-501.8, 57.3, -286.9]` | `Ex: [12.8, 0.0]` | Nenhum | `[1872257...` | Nenhuma | Padrão | Nenhum | Padrão | Objeto / Estático | item (Drop temporário desnecessário) | `Descarte / Não transferido` |
| `minecraft:armor_stand` | 6 | overworld | `Ex: [277.6, 1.0, -2197.2]` | `Ex: [0.0, 0.0]` | {"color":"#00FFFF","text":"Cafeslayeur"}, {"color":"aqua","text":"NereidRegulus"} (+3) | `[1622464...` | LordOfGnou, beta, cyohg, DAY_COUNTER | Customizado | Nenhum | Padrão | Objeto / Estático | armor_stand (Bedrock) | `mazerunner/setup_hall_of_fame.mcfunction` |
| `minecraft:phantom` | 5 | nether | `Ex: [762.4, 176.7, -201.6]` | `Ex: [-112.7, -7.2]` | Nenhum | `[-193903...` | Smoke | Padrão | Sim | Padrão | Hostil | phantom (Bedrock) + Loot de Esmeraldas | `loot_tables/entities/phantom.json` |
| `minecraft:polar_bear` | 3 | overworld | `Ex: [7092.0, 68.0, -138.0]` | `Ex: [87.4, 0.0]` | Nenhum | `N/A` | Nenhuma | Padrão | Nenhum | Padrão | Passivo | polar_bear (Bedrock vanilla) | `Nativo Bedrock / Spawn` |
| `minecraft:spider` | 2 | overworld | `Ex: [-44.6, 43.0, -32.6]` | `Ex: [91.8, 0.0]` | Nenhum | `[1899448...` | Nenhuma | Padrão | Nenhum | Padrão | Hostil | spider (Bedrock) + Loot de Esmeraldas | `loot_tables/entities/spider.json` |
| `minecraft:elder_guardian` | 2 | overworld | `Ex: [279.2, 30.1, -1633.2]` | `Ex: [250.8, 0.0]` | Nenhum | `[4835902...` | Nenhuma | Padrão | Nenhum | Padrão | Hostil | elder_guardian (Bedrock) + Loot de Esmeraldas | `loot_tables/entities/elder_guardian.json` |
| `minecraft:parrot` | 2 | overworld | `Ex: [370.5, 10.3, -2658.5]` | `Ex: [63.3, 0.0]` | Nenhum | `[4850095...` | Nenhuma | Padrão | Nenhum | Padrão | Passivo | parrot (Bedrock vanilla) | `Nativo Bedrock / Spawn` |
| `minecraft:ravager` | 2 | overworld | `Ex: [982.0, 136.0, 1170.1]` | `Ex: [1.1, 0.0]` | Nenhum | `[-102072...` | Nenhuma | Padrão | Nenhum | Padrão | Hostil | ravager (Bedrock) + Loot de Esmeraldas | `loot_tables/entities/ravager.json` |
| `minecraft:vex` | 2 | overworld | `Ex: [6964.4, 24.1, 7062.5]` | `Ex: [63.2, 0.0]` | Nenhum | `[-207428...` | Nenhuma | Padrão | Nenhum | Padrão | Hostil | vex (Bedrock) + Loot de Esmeraldas | `loot_tables/entities/vex.json` |
| `minecraft:skeleton` | 1 | nether | `[-217.3, 141.0, -422.5]` | `[99.1, 0.0]` | Nenhum | `[-201140...` | Nenhuma | Customizado | Nenhum | Padrão | Hostil | skeleton (Bedrock) + Loot de Esmeraldas | `loot_tables/entities/skeleton.json` |
| `minecraft:wither_skeleton` | 1 | nether | `[-208.3, 142.0, -408.5]` | `[90.0, 0.0]` | Nenhum | `[6227976...` | Nenhuma | Customizado | Nenhum | Padrão | Hostil | wither_skeleton (Bedrock) + Loot de Esmeraldas | `loot_tables/entities/wither_skeleton.json` |
| `minecraft:evoker_fangs` | 1 | nether | `[164.5, 173.4, -602.2]` | `[0.0, 0.0]` | Nenhum | `[1928464...` | Nenhuma | Padrão | Nenhum | Padrão | Objeto / Estático | evoker_fangs (Bedrock vanilla) | `Nativo Bedrock / Spawn` |
| `minecraft:experience_orb` | 1 | overworld | `[-271.8, 85.0, -1537.8]` | `[149.3, 0.0]` | Nenhum | `[1240336...` | Nenhuma | Padrão | Nenhum | Padrão | Objeto / Estático | experience_orb (Bedrock vanilla) | `Nativo Bedrock / Spawn` |
| `minecraft:villager` | 1 | overworld | `[967.2, 135.0, 1180.2]` | `[313.0, 0.0]` | {"text":"Angus"} | `[2887626...` | Vil, Angus | Padrão | Nenhum | jungle | Passivo | mazerunner:npc_angus | `entities/npc_angus.json / custom/summon_angus.mcfunction` |
| `minecraft:wither_skeleton` | 1 | overworld | `[6977.5, 22.0, 7090.4]` | `[1.9, 0.0]` | Nenhum | `[-914953...` | Nenhuma | Customizado | Sim | Padrão | Hostil | wither_skeleton (Bedrock) + Loot de Esmeraldas | `loot_tables/entities/wither_skeleton.json` |
| `minecraft:ghast` | 1 | overworld | `[4968.6, 137.6, -4957.0]` | `[-116.4, 0.0]` | Nenhum | `[5705136...` | Nenhuma | Padrão | Nenhum | Padrão | Hostil | ghast (Bedrock) + Loot de Esmeraldas | `loot_tables/entities/ghast.json` |
