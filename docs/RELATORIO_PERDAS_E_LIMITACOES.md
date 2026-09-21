# Relatório de Perdas, Fallbacks e Limitações Técnicas / Technical Limitations & Fallbacks Report

*Read in / Leia em:*
- [Português (PT-BR)](#português-pt-br)
- [English (EN)](#english-en)

---

<a name="português-pt-br"></a>
## Português (PT-BR)

| Elemento Original (Java) | Resultado no Bedrock 1.26.40 | Estratégia Adotada | Limitação / Motivo Técnico | Arquivo Responsável |
| :--- | :--- | :--- | :--- | :--- |
| **Comando `forceload add/remove`** | Comentado na função e coberto por `tickingarea` global | Criação de 2 `tickingarea` permanentes em `init_world` cobrindo o núcleo do labirinto e as 8 portas | Bedrock Edition não possui `/forceload` por chunk, utilizando o sistema de `tickingarea` (limitado a 10 por mundo) | `init_world.mcfunction`, `open_doors_*.mcfunction` |
| **Comando `data merge block ... {Delay:0}`** | Comentado nas funções de reset de spawner | Spawners do Bedrock ativam nativamente quando o jogador entra no raio de 16 blocos | Bedrock Edition não possui `/data` nem acesso direto ao NBT de tile entities via comando | `reset_spawner_*.mcfunction` |
| **Skins de Jogadores das Estátuas** | Armor Stands com armaduras tingidas e nomes coloridos | Preservação das peças exatas de armadura, cores hexadecimais e tags visuais | Não havia PNGs de skins locais fornecidos no projeto original e a política de segurança veda requisições a credenciais externas | `setup_hall_of_fame.mcfunction` |
| **Livros Escritos em Molduras** | Molduras contendo o item livro escrito / texto no lobby | Conteúdo textual dos livros (`Objective` e `Rules`) documentado e preservado em relatórios | No Bedrock, molduras não exibem o NBT de páginas abertas formatadas diretamente na face do bloco | `RELATORIO_AUDITORIA_ENTIDADES.md` |
| **Flecha Espectral (`spectral_arrow`) em trocas** | Flecha convencional de alto dano / flecha brilhante | Substituição transparente na tabela de troca do NPC Kai | Flechas espectrais com contorno brilhante são exclusivas do Minecraft Java Edition | `trading/kai_trades.json` |
| **Inventário dos Jogadores** | Inventário inicial limpo + função `starter_kit` | Jogadores iniciam no lobby; opção de invocar kit inicial via `/function mazerunner/starter_kit` | Chunker não transfere playerdata; auditoria comprovou que ambos os jogadores originais já estavam com inventários vazios | `mazerunner_bp/functions/mazerunner/starter_kit.mcfunction` |

---

<a name="english-en"></a>
## English (EN)

| Original Element (Java) | Bedrock 1.26.40 Result | Strategy Adopted | Technical Limitation / Reason | Responsible File |
| :--- | :--- | :--- | :--- | :--- |
| **`forceload add/remove` command** | Commented out in function and covered by global `tickingarea` | Creation of 2 permanent `tickingarea` entries in `init_world` covering the maze core and all 8 doors | Bedrock Edition lacks chunk-based `/forceload`, using `tickingarea` instead (limited to 10 per world) | `init_world.mcfunction`, `open_doors_*.mcfunction` |
| **`data merge block ... {Delay:0}` command** | Commented out in spawner reset functions | Bedrock spawners activate natively whenever a player enters within the 16-block radius | Bedrock Edition lacks `/data` and direct tile-entity NBT manipulation via commands | `reset_spawner_*.mcfunction` |
| **Statue Player Skins** | Armor Stands with dyed armors and colored display names | Preserved exact armor pieces, hex color codes, and visual name tags | No local skin PNGs were included in the original project, and security policy prohibits external credential queries | `setup_hall_of_fame.mcfunction` |
| **Written Books in Item Frames** | Item frames displaying written book item / lobby text | Textual content of books (`Objective` and `Rules`) documented and preserved in technical reports | In Bedrock Edition, item frames do not render open formatted multi-page book NBT on the block face | `RELATORIO_AUDITORIA_ENTIDADES.md` |
| **Spectral Arrow (`spectral_arrow`) in trades** | High-damage regular arrow / tipped arrow | Transparent fallback in NPC Kai's trade table | Glowing spectral arrows are exclusive to Minecraft Java Edition | `trading/kai_trades.json` |
| **Player Inventories** | Clean initial inventory + `starter_kit` function | Players spawn in the lobby; option to claim starter kit via `/function mazerunner/starter_kit` | Chunker does not transfer playerdata; audit verified both original players already had empty inventories | `mazerunner_bp/functions/mazerunner/starter_kit.mcfunction` |
