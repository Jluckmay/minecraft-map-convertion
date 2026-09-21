# Relatório Técnico de Conversão (Java 1.16.5 para Bedrock 1.26.40)

## 1. Visão Geral
A conversão do mapa **Mazescapist (MazeRunner)** para **Minecraft Bedrock Edition 1.26.40** foi estruturada sobre o terreno convertido pelo Chunker, complementando todas as lacunas de entidades, lógica, pacotes e comandos.

- **Mundo Bedrock Final**: `mazescapist-bedrock-1.26.40.mcworld`
- **Behavior Pack**: `mazerunner-behavior-pack.mcpack` (UUID Header: `ceba1432-a9c9-5ff3-828f-429a43f6630a`)
- **Resource Pack**: `mazerunner-resource-pack.mcpack` (UUID Header: `15bb3f51-336b-5fc8-882f-6e22db197541`)

---

## 2. Conversão e Implementação dos NPCs
No Bedrock Edition, comandos `/summon` não aceitam tags NBT compostas como `{Offers:[...]}`. Para garantir fidelidade matemática e visual sem duplicação de entidades, foi adotada a seguinte arquitetura:

1. **Entidades Customizadas no Behavior Pack**:
   - Cada NPC foi registrado como entidade estável no namespace `mazerunner:npc_<nome>` (ex: `mazerunner:npc_bruce`, `mazerunner:npc_ylva`).
   - Cada entidade possui imunidade completa a dano de monstros e jogadores, movimentação travada na posição de serviço e tabela de troca nativa Bedrock acoplada.
2. **Tabelas de Troca Bedrock (`trading/`)**:
   - Foram convertidas 15 tabelas de troca JSON em `mazerunner_bp/trading/`, replicando fielmente cada esmeralda cobrada e cada item entregue.
3. **Idempotência Garantida**:
   - As funções de summon utilizam a verificação `unless entity @e[type=mazerunner:npc_<nome>]`. Se a função for executada repetidamente, o NPC não será duplicado.

---

## 3. Conversão das Tabelas de Saque (Loot Tables)
O datapack continha 21 loot tables customizadas onde monstros derrotados fornecem esmeraldas (moeda do labirinto). Todas foram convertidas para a sintaxe Bedrock:
- Pools, rolls e funções `set_count` e `looting_enchant` adaptadas para o padrão Bedrock.
- Entidades abrangidas: Blaze, Cave Spider, Creeper, Drowned, Enderman, Evoker, Ghast, Guardian, Hoglin, Husk, Magma Cube, Phantom, Shulker, Skeleton, Slime, Spider, Stray, Vindicator, Witch, Wither Skeleton e Zombie.

---

## 4. Conversão de Funções e Comandos
Foram convertidas 54 funções `.mcfunction` originais do datapack MazeRunner, além de criadas 10 funções auxiliares para bosses, NPCs de exploração e inicialização do mundo:
- **`mazerunner:init_world`**: Configura os placares de objetivos (`dayCounter`), registra áreas ativas (`tickingarea`) para manter o centro do labirinto e as portas funcionais e invoca as estátuas do Hall da Fama.
- **`mazerunner:setup_hall_of_fame`**: Invoca as estátuas dos criadores e testadores com nomes visíveis e armaduras equivalentes.
- **`mazerunner:starter_kit`**: Permite aos jogadores receber suprimentos básicos iniciais.
- **`custom:generates_npc`**: Totalmente adaptada para sintaxe Bedrock 1.26.40, idempotente e com mensagens `tellraw` formatadas em cores.
- **`custom:generates_chest`**: Mantém o clonamento periódico dos baús de suprimentos para a área de carregamento.
- **`custom:open_doors_1..8` & `custom:close_all_doors`**: Portas automáticas do labirinto abrem e fecham sem perda de blocos.

---

## 5. Recursos Visuais e Texturas
- As texturas personalizadas das rochas-mãe (`bedrock_0.png` até `bedrock_4.png`) extraídas do recurso Java foram convertidas e registradas no Resource Pack Bedrock em `textures/blocks/` e `terrain_texture.json`.
- O ícone original `icon.png` foi processado e incluído como `pack_icon.png` nos pacotes e `world_icon.jpeg` no arquivo do mundo.
