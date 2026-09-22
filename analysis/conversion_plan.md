# Plano Estratégico de Conversão Java -> Bedrock (Seção 2 e 42)

## 1. Estratégia de Recursos (Resource Pack)
- **Texturas de Tijolos Bedrock**: Converter variações de `blockstates/bedrock.json` para entradas ponderadas no `terrain_texture.json` com chave `"bedrock"` e gerar `blocks.json` e fallback `bedrock.png`.
- **Sons**: Mapear arquivos `.ogg` para a árvore nativa `sounds/` do Bedrock e registrar entradas em `sound_definitions.json`.
- **Manifest**: Versão do manifesto format_version 2, com `min_engine_version: [1, 20, 0]` e UUIDs RFC4122 v5 estáveis.

## 2. Estratégia de Comandos e Datapacks (Behavior Pack)
- **Parser AST**: Analisar tokens de comandos Java e gerar nós intermediários.
- **Subcomandos de Execute**: Traduzir sintaxe 1.16.5 para Bedrock 1.20+ (`as`, `at`, `positioned`, `if entity`).
- **Seletores**: Substituir `distance=..X` por `r=X`, `distance=X..Y` por `rm=X,r=Y`, `sort=nearest,limit=1` por `c=1`.
- **Forceload**: Traduzir coordenadas para `tickingarea add/remove` com bounding box calculada.
- **Spawners**: Converter `/data merge block ... {Delay:0}` para `/setblock ... mob_spawner`.
- **Aldeões e Trocas**: Extrair NBT de ofertas e gerar arquivos de trading (`trading/*.json`) e entidades customizadas.
- **Funções e Ciclos**: Organizar funções em `behavior_pack/functions/` e configurar inicialização em `tick.json`.

## 3. Estratégia do Mundo (LevelDB Injection)
- **Preservação de Command Blocks**: Manter os 641 blocos de comando nas posições originais no mundo Bedrock.
- **Atualização In-Place**: Ler blocos SSTable do LevelDB (`.ldb`), descomprimir formato tipo 4 da Mojang, substituir os comandos pela versão traduzida e recalcular o CRC32C mascarado.
- **Integração de Pacotes**: Inserir referências de pacotes em `world_behavior_packs.json` e `world_resource_packs.json`.

## 4. Validação e Empacotamento
- **Verificação de Resíduos**: Garantir 0 ocorrências de comandos com sintaxe Java inválida (`distance=`, `predicate=`, etc.).
- **Empacotamento Múltiplo**: Gerar `.mcworld` autônomo, `.mcpack` de recursos, `.mcpack` de comportamento e pacote unificado `.mcaddon`.
