# Minecraft Map Converter & Bridge Tool (Java <-> Bedrock 1.26.40+)

[![Minecraft Bedrock](https://img.shields.io/badge/Minecraft%20Bedrock-1.26.40%2B-green.svg)](https://minecraft.net/)
[![Minecraft Java](https://img.shields.io/badge/Minecraft%20Java-1.16%2B-orange.svg)](https://minecraft.net/)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Author](https://img.shields.io/badge/Author-Jo%C3%A3o%20Lucas%20Mayrinck-blueviolet.svg)](#author--autor)

---

*Read in / Leia em:*
- [English (EN)](#english)
- [Português (PT-BR)](#português)

---

<a name="english"></a>
## English (EN)

### Overview
**Minecraft Map Converter & Bridge Tool** is an automated, robust conversion pipeline designed to bridge the fundamental gaps between Minecraft Java Edition and Minecraft Bedrock Edition (specifically optimized for **Bedrock 1.26.40+**).

While existing terrain tools (such as [Chunker](https://chunker.app) or Amulet) convert blocks, biomes, containers, and dimensions, they **do not convert entities, player inventories, custom villager NBT trades, or datapack logic**.

This tool solves this problem by analyzing the Java world directly, converting datapacks into native **Behavior Packs** and **Resource Packs**, extracting custom trades into Bedrock Trade Tables, translating commands with full idempotency, and packaging everything cleanly into importable `.mcworld` and `.mcpack` files.

### Key Features
- **Terrain Integrity**: Preserves the converted LevelDB database 100% untouched—no risky binary chunk writes.
- **Deep Region & Entity Audit**: Scans Anvil `.mca` files across all dimensions (Overworld, Nether, End) and decompresses zlib chunk payloads to detect all entities, tile entities, and command blocks.
- **Custom Villager & NPC Conversion**:
  - Automatically parses Java NBT `Offers:{Recipes:[...]}` from summon commands in functions and command blocks.
  - Generates Bedrock Trade Tables (`trading/*.json`) preserving exact emerald costs, items, and quantities.
  - Generates custom Behavior Pack entities (`entities/npc_*.json`) with damage immunity and fixed spatial positions.
  - Generates Resource Pack client definitions (`entity/npc_*.entity.json`) with corresponding textures and geometries.
- **Idempotent Command Conversion**:
  - Converts `.mcfunction` files to modern Bedrock 1.26.40 syntax.
  - Automatically wraps summon commands with `unless entity @e[type=...]` to ensure **zero duplication** upon repeated execution.
  - Converts JSON `/tellraw` commands into Bedrock `{"rawtext": [...]}` with embedded color formatting codes (`§a`, `§6`, etc.).
  - Translates sound event identifiers (e.g., `entity.player.levelup` $\rightarrow$ `random.levelup`).
  - Converts `/forceload` into safe documentation and continuous simulation areas (`tickingarea`).
- **Entity Loot Table Translation**:
  - Automatically converts custom mob loot tables (pools, rolls, `set_count`, `looting_enchant`, `killed_by_player`) to Bedrock JSON format.
- **Embedded Resource Extraction**:
  - Extracts custom block textures and generates `terrain_texture.json`.
  - Converts `icon.png` into `world_icon.jpeg` and `pack_icon.png`.
- **Containers & Player Inventory Preservation**:
  - Automatically preserves 100% of container blocks (chests, trapped chests, barrels, hoppers, shulker boxes, dispensers, droppers) in LevelDB.
  - Automatically synchronizes player inventories, armor slots, offhand, and Ender Chest items from Java `level.dat` and `playerdata` into Bedrock `~local_player`.
- **Packaging & Validation**:
  - Generates stable UUIDs v4 and manifest files configured for Bedrock 1.20+/1.21+.
  - Packages standalone `.mcpack` files, unified `.mcaddon`, and compiles `.mcworld` with SHA-256 integrity verification.

> [!NOTE]
> **Large Files Notice**: Heavy binary archives (`*.zip`, `*.mcworld` >50–100 MB) are excluded from the Git repository via `.gitignore` to adhere to GitHub file size limits. Place your input files into `inputs/` and run `python map_converter.py` to compile the final `.mcworld` locally.

### Requirements & Installation
Ensure you have Python 3.10 or higher installed:

```bash
git clone https://github.com/jluckmay/minecraft-map-convertion.git
cd map-convertion
pip install -r requirements.txt
```

### CLI Usage

```bash
# Display help and available options
python map_converter.py --help

# Run with custom input worlds
python map_converter.py --java inputs/my_world.zip --bedrock inputs/my_world_chunker.mcworld --output dist/

# Run automated test suite
python tests/test_conversion.py
```

#### CLI Arguments:
- `--java`: Path to the Java world ZIP archive.
- `--bedrock`: Path to the initial Bedrock `.mcworld` converted by Chunker.
- `--output`: Output directory for generated deliverables (`.mcworld`, `.mcpack`, `SHA256SUMS.txt`) [Default: `dist`].
- `--packs`: Output directory for unpacked Behavior and Resource Packs [Default: `packs`].
- `--name`: Custom name for the generated world and packs (Default: auto-detected from `level.dat`).
- `--keep-temp`: Preserves intermediate temporary world extraction directory.

### Technical Documentation & Reports
All in-depth technical documentation and manuals are available in bilingual format (PT-BR / EN) inside the [`docs/`](docs/) directory:
- 📱 [**Installation, Activation & Mobile (Android / iOS) Guide**](docs/INSTRUCOES_INSTALACAO_E_USO.md)
- 🛠️ [**Technical Conversion Architecture & Pipeline**](docs/ARQUITETURA_DE_CONVERSAO.md)
- 📊 [**World & Entity Audit Guide (Anvil Regions, NBT, Playerdata)**](docs/GUIA_AUDITORIA_DE_MUNDOS.md)
- 📜 [**Command Translation Guide (Java to Bedrock Syntax)**](docs/GUIA_TRADUCAO_COMANDOS.md)
- ⚠️ [**Technical Limitations & Engine Differences (Java vs Bedrock)**](docs/LIMITACOES_TECNICAS_JAVA_BEDROCK.md)

---

<a name="português"></a>
## Português (PT-BR)

### Visão Geral
O **Minecraft Map Converter & Bridge Tool** é um utilitário automatizado de conversão e ponte complementar projetado para suprir as lacunas estruturais entre o Minecraft Java Edition e o Minecraft Bedrock Edition (otimizado para **Bedrock 1.26.40+**).

Enquanto ferramentas como o [Chunker](https://chunker.app) ou o Amulet convertem com excelência os blocos, biomas, dimensões e contêineres, **elas não convertem entidades, inventários de jogadores, trocas NBT customizadas de aldeões ou a lógica de datapacks**.

Esta ferramenta soluciona esse desafio auditando diretamente os arquivos Java, convertendo datapacks em **Behavior Packs** e **Resource Packs** nativos, traduzindo comandos com garantia matemática de **idempotência** (sem duplicação de entidades), gerando tabelas de troca Bedrock nativas e empacotando o resultado em arquivos prontos `.mcworld` e `.mcpack`.

### Funcionalidades Principais
- **Preservação Integral do Terreno**: Mantém o banco LevelDB convertido 100% intocado, sem escritas manuais ou riscos de corrupção nos chunks.
- **Auditoria Profunda de Regiões MCA**: Faz a leitura dos cabeçalhos dos arquivos `.mca` de todas as dimensões, descomprime os blocos zlib e extrai todas as entidades, tile entities e blocos de comando.
- **Conversão Completa de NPCs e Comércio**:
  - Extrai as receitas NBT `{Offers:{Recipes:[...]}}` de comandos em funções e blocos de comando.
  - Gera tabelas de troca Bedrock (`trading/*.json`) preservando preços em esmeraldas, itens e quantidades.
  - Cria entidades customizadas no Behavior Pack (`entities/npc_*.json`) com invulnerabilidade e posição travada.
  - Cria definições de cliente no Resource Pack (`entity/npc_*.entity.json`) com modelos e texturas correspondentes.
- **Comandos Idempotentes**:
  - Converte `.mcfunction` para a sintaxe moderna do Bedrock 1.26.40.
  - Adiciona automaticamente a cláusula `unless entity @e[type=...]` para impedir duplicações mesmo se a função for acionada repetidamente.
  - Converte comandos `/tellraw` para a sintaxe Bedrock `{"rawtext": [...]}` com códigos de formatação de cores (`§a`, `§6`, etc.).
  - Traduz eventos de som (`entity.player.levelup` $\rightarrow$ `random.levelup`).
  - Adapta `/forceload` para áreas contínuas (`tickingarea`) e documentação técnica.
- **Conversão de Tabelas de Saque (Loot Tables)**:
  - Traduz as tabelas de saque de monstros (pools, rolls, looting, contagens) para o formato JSON do Bedrock.
- **Extração de Recursos e Texturas**:
  - Extrai texturas personalizadas de blocos e gera o arquivo `terrain_texture.json`.
  - Gera `world_icon.jpeg` e `pack_icon.png` a partir do `icon.png` original.
- **Preservação de Baús, Contêineres e Inventário**:
  - Preserva 100% dos blocos de contêineres (`Chest`, `TrappedChest`, `Barrel`, `ShulkerBox`, `Hopper`, `Dispenser`, `Dropper`) com todos os itens, slots e quantidades no LevelDB.
  - Sincroniza automaticamente inventário, armaduras, offhand e Ender Chest do jogador (`level.dat` e `playerdata`) para `~local_player` no Bedrock.
- **Empacotamento e Hashes SHA-256**:
  - Cria manifestos válidos com UUIDs v4 exclusivos e compatibilidade declarada com Bedrock 1.20+/1.21+.
  - Gera o `.mcworld` final pronto para importação, o `.mcaddon` unificado e os pacotes independentes `.mcpack`.

> [!NOTE]
> **Aviso sobre Arquivos Pesados**: Arquivos binários pesados (`*.zip`, `*.mcworld` >50–100 MB) estão excluídos do repositório Git via `.gitignore` para respeitar os limites de tamanho do GitHub. Coloque seus arquivos originais na pasta `inputs/` e execute o pipeline para gerar o `.mcworld` localmente.

---

### Estrutura do Projeto / Project Structure

```text
map-convertion/
├── .gitignore                       # Ignora temporários e mundos pesados (*.zip, *.mcworld, *.mcpack)
├── LICENSE                          # Licença MIT (Copyright 2026 João Lucas Mayrinck)
├── README.md                        # Documentação bilíngue completa (EN/PT)
├── requirements.txt                 # Dependências Python (nbtlib, amulet-leveldb, Pillow)
├── CONVERSION_REPORT.md             # Relatório consolidado final da conversão
│
├── converter/                       # Módulos Python desacoplados da arquitetura de conversão
│   ├── world/                       # Anvil MCA, LevelDB nativo C++ e sincronização de inventários
│   ├── commands/                    # Tradutor de sintaxe de comandos Java -> Bedrock
│   ├── behavior_pack/               # Gerador de funções, entidades, trading e loot tables
│   └── resource_pack/               # Mapeamento de texturas, terrain atlas e variações
│
├── scripts/                         # Fases modulares automatizadas (1 a 12)
│   ├── phase1_analyze_world.py      # Fase 1: Extração e inspeção do mundo Java
│   ├── phase2_extract_command_blocks.py # Fase 2: Varredura de MCA e conexões em cadeia
│   ├── phase3_inventory_commands.py # Fase 3: Inventário de comandos e compatibilidade
│   ├── phase4_analyze_resources.py  # Fase 4: Análise de texturas, blockstates e áudios
│   ├── phase5_to_9_convert_all.py   # Fases 5-9: Conversão RP/BP, LevelDB e inventários
│   ├── phase10_validate.py          # Fase 10: Motor de validação automática (0 inconformidades)
│   ├── phase11_package.py           # Fase 11: Empacotamento (.mcworld, .mcaddon, .mcpack)
│   └── phase12_report.py            # Fase 12: Geração de CONVERSION_REPORT.md
│
├── inputs/                          # Arquivos de entrada (apenas o mundo Java)
│   ├── java-version.zip             # Mundo Java original (.zip)
│   └── README.md                    # Instruções de uso dos arquivos de entrada
│
├── expected/                        # Arquivos de exemplo e referência externa (gabarito)
│   ├── bedrock-version.mcworld      # Template de referência do Chunker
│   ├── maze-runner-resource-pack.mcpack # Resource Pack de referência do MinecraftMaps
│   └── README.md                    # Documentação de referência
│
├── output/                          # Diretório oficial dos artefatos Bedrock compilados
│   ├── converted_map.mcworld        # Mundo final completo pronto para PC e celular
│   ├── converted_map.mcaddon        # Addon unificado (BP + RP)
│   ├── converted_behavior_pack.mcpack # Behavior Pack avulso
│   └── converted_resource_pack.mcpack # Resource Pack avulso
│
├── docs/                            # Manuais técnicos e guias de arquitetura
│   ├── INSTRUCOES_INSTALACAO_E_USO.md # Guia completo para PC e Celular (Android/iOS)
│   ├── ARQUITETURA_DE_CONVERSAO.md
│   ├── GUIA_AUDITORIA_DE_MUNDOS.md
│   ├── GUIA_TRADUCAO_COMANDOS.md
│   └── LIMITACOES_TECNICAS_JAVA_BEDROCK.md
│
└── tests/                           # Suíte de testes automatizados
    ├── test_modular_pipeline.py     # Testes da arquitetura modular
    └── test_conversion.py           # Testes unitários do motor de conversão
```

---

### Documentação Técnica / Technical Reports
Todos os guias técnicos e manuais de operação estão centralizados no diretório [`docs/`](docs/):
- 📱 [**Instruções de Instalação, Ativação e Uso (PC e Celular Android / iOS)**](docs/INSTRUCOES_INSTALACAO_E_USO.md)
- 🛠️ [**Arquitetura Técnica de Conversão do Pipeline**](docs/ARQUITETURA_DE_CONVERSAO.md)
- 📊 [**Guia de Auditoria de Mundos e Entidades (Anvil MCA, NBT, Playerdata)**](docs/GUIA_AUDITORIA_DE_MUNDOS.md)
- 📜 [**Guia de Tradução de Comandos (Java $\rightarrow$ Bedrock 1.20+/1.21+)**](docs/GUIA_TRADUCAO_COMANDOS.md)
- ⚠️ [**Limitações Técnicas e Diferenças de Engine (Java vs Bedrock)**](docs/LIMITACOES_TECNICAS_JAVA_BEDROCK.md)

---

### Author / Autor
**João Lucas Mayrinck**

---

### License / Licença
Este projeto é distribuído sob a licença **MIT**. Veja o arquivo [`LICENSE`](LICENSE) para mais detalhes.
This project is licensed under the **MIT License**. See the [`LICENSE`](LICENSE) file for details.
