# Minecraft Map Converter & Bridge Tool (Java <-> Bedrock 1.26.40+)

[![Minecraft Bedrock](https://img.shields.io/badge/Minecraft%20Bedrock-1.26.40%2B-green.svg)](https://minecraft.net/)
[![Minecraft Java](https://img.shields.io/badge/Minecraft%20Java-1.16.5%2B-orange.svg)](https://minecraft.net/)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Author](https://img.shields.io/badge/Author-Jo%C3%A3o%20Lucas%20Mayrinck-blueviolet.svg)](#author--autor)

---

*Read in / Leia em:*
- [English (#english)](#english)
- [Português (#português)](#português)

---

<a name="english"></a>
## English

### Overview
**Minecraft Map Converter & Bridge Tool** is an automated, robust conversion pipeline designed to bridge the fundamental gaps between Minecraft Java Edition and Minecraft Bedrock Edition (specifically tailored for **Bedrock 1.26.40+**).

While existing terrain tools (such as Chunker or Amulet) successfully convert blocks, biomes, containers, and dimensions, they **do not convert entities, player inventories, custom villager NBT trades, or datapack logic**.

This tool solves this problem by analyzing the Java world directly, converting datapacks into native **Behavior Packs** and **Resource Packs**, extracting custom trades into Bedrock Trade Tables, translating commands with full idempotency, and packaging everything cleanly into importable `.mcworld` and `.mcpack` files.

### Key Features
- **Terrain Integrity**: Preserves the converted LevelDB database 100% untouched—no risky binary chunk writes.
- **Deep Region & Entity Audit**: Scans Anvil `.mca` files across all dimensions (Overworld, Nether) and decompresses zlib chunk payloads to detect all entities, tile entities, and command blocks.
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
  - Converts `/forceload` and `/data merge block` into safe documentation and continuous simulation areas (`tickingarea`).
- **Entity Loot Table Translation**:
  - Automatically converts custom mob loot tables (pools, rolls, `set_count`, `looting_enchant`, `killed_by_player`) to Bedrock JSON format (e.g., restoring mob emerald drop economies).
- **Embedded Resource Extraction**:
  - Extracts custom block textures (e.g., bedrock wall variants) and generates `terrain_texture.json`.
  - Converts `icon.png` into `world_icon.jpeg` and `pack_icon.png`.
- **Packaging & Validation**:
  - Generates stable UUIDs v4 and manifest files configured for Bedrock 1.26.40.
  - Packages the final `.mcworld` and standalone `.mcpack` files with SHA-256 integrity verification.

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

# Run with default directories (auto-discovers inputs/ or root files)
python map_converter.py

# Custom execution
python map_converter.py --java inputs/java-version.zip --bedrock inputs/bedrock-version.mcworld --output dist/

# Run automated integrity test suite
python tests/test_conversion.py
```

#### CLI Arguments:
- `--java`: Path to the Java world ZIP archive (Default: auto-resolves `inputs/java-version.zip` or `java-version.zip`).
- `--bedrock`: Path to the initial Bedrock `.mcworld` converted by Chunker (Default: auto-resolves `inputs/bedrock-version.mcworld` or `bedrock-version.mcworld`).
- `--output`: Output directory for generated deliverables (`.mcworld`, `.mcpack`, `SHA256SUMS.txt`) [Default: `dist`].
- `--packs`: Output directory for unpacked Behavior and Resource Packs [Default: `packs`].
- `--keep-temp`: Preserves intermediate temporary world extraction directory (`dist/work_bedrock`).

---

<a name="português"></a>
## Português

### Visão Geral
O **Minecraft Map Converter & Bridge Tool** é um utilitário automatizado de conversão e ponte complementar projetado para suprir as lacunas estruturais entre o Minecraft Java Edition e o Minecraft Bedrock Edition (otimizado para **Bedrock 1.26.40+**).

Enquanto ferramentas como o Chunker ou o Amulet convertem com excelência os blocos, biomas, dimensões e contêineres, **elas não convertem entidades, inventários de jogadores, trocas NBT customizadas de aldeões ou a lógica de datapacks**.

Esta ferramenta soluciona esse desafio auditando diretamente os arquivos Java, convertendo datapacks em **Behavior Packs** e **Resource Packs** nativos, traduzindo comandos com garantia matemática de **idempotência** (sem duplicação de entidades), gerando tabelas de troca Bedrock nativas e empacotando o resultado em arquivos prontos `.mcworld` e `.mcpack`.

### Funcionalidades Principais
- **Preservação Integral do Terreno**: Mantém o banco LevelDB convertido 100% intocado, sem escritas manuais ou riscos de corrupção nos chunks.
- **Auditoria Profunda de Regiões MCA**: Faz a leitura dos cabeçalhos dos arquivos `.mca` do Overworld e Nether, descomprime os blocos zlib e extrai todas as entidades, tile entities e blocos de comando.
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
  - Adapta `/forceload` e `/data merge block` para áreas contínuas (`tickingarea`) e documentação técnica.
- **Conversão de Tabelas de Saque (Loot Tables)**:
  - Traduz as tabelas de saque de monstros (pools, rolls, looting, contagens) para o formato JSON do Bedrock (recompondo drops de esmeraldas e economia).
- **Extração de Recursos e Texturas**:
  - Extrai texturas de blocos do pacote de recursos Java e gera o arquivo `terrain_texture.json`.
  - Gera `world_icon.jpeg` e `pack_icon.png` a partir do `icon.png` original.
- **Empacotamento e Hashes SHA-256**:
  - Cria manifestos válidos com UUIDs v4 exclusivos e compatibilidade declarada com Bedrock 1.26.40.
  - Gera o `.mcworld` final pronto para importação e os pacotes independentes `.mcpack`.

---

### Estrutura do Projeto / Project Structure

```text
minecraft-map-convertion/
├── .gitignore                       # Ignora temporários e artefatos voláteis
├── LICENSE                          # Licença MIT (Copyright 2026 João Lucas Mayrinck)
├── README.md                        # Documentação bilíngue completa
├── requirements.txt                 # Dependências Python (nbtlib, Pillow)
├── map_converter.py                 # CLI e script principal de conversão
│
├── dist/                            # Entregáveis finais prontos para uso
│   ├── mazescapist-bedrock-1.26.40.mcworld  # Mundo Bedrock pronto com pacotes integrados
│   ├── mazerunner-behavior-pack.mcpack     # Behavior Pack independente
│   ├── mazerunner-resource-pack.mcpack     # Resource Pack independente
│   └── SHA256SUMS.txt                      # Checksums SHA-256 dos entregáveis
│
├── docs/                            # Manuais técnicos e relatórios de auditoria
│   ├── INSTRUCOES_INSTALACAO_E_TESTES.md   # Guia de instalação, testes e instruções para celular (Android / iOS)
│   ├── RELATORIO_AUDITORIA_ENTIDADES.md    # Censo e auditoria detalhada de 2031 entidades Java
│   ├── RELATORIO_CONVERSAO.md              # Relatório técnico completo de conversão
│   ├── RELATORIO_PERDAS_E_LIMITACOES.md    # Mapeamento de limitações e fallbacks adotados
│   └── RELATORIO_COMANDOS_NAO_CONVERTIDOS.md # Auditoria de comandos e adaptações
│
├── inputs/                          # Arquivos-fonte originais
│   ├── java-version.zip             # Mundo Java Edition 1.16.5 original
│   ├── bedrock-version.mcworld      # Saída de terreno convertida pelo Chunker
│   └── README.md                    # Documentação e hashes das fontes
│
├── packs/                           # Código-fonte aberto dos pacotes Bedrock
│   ├── mazerunner_bp/               # Behavior Pack descompactado (entities, trading, functions, loot_tables)
│   └── mazerunner_rp/               # Resource Pack descompactado (textures, entity)
│
├── tests/                           # Suíte de testes automatizados
│   └── test_conversion.py           # Testes de integridade, JSON e manifestos
│
└── _backups/                        # Cópias de segurança originais imutáveis
    ├── java-version.zip.bak
    └── bedrock-version.mcworld.bak
```

---

### Documentação Técnica / Technical Reports
Todos os relatórios aprofundados e manuais de operação estão centralizados no diretório [`docs/`](docs/):
- 📱 [**Instruções de Instalação, Testes e Uso no Celular (Android / iOS)**](docs/INSTRUCOES_INSTALACAO_E_TESTES.md)
- 📊 [**Relatório de Auditoria de Entidades Java (Censo Completo)**](docs/RELATORIO_AUDITORIA_ENTIDADES.md)
- 🛠️ [**Relatório Geral de Conversão Java $\rightarrow$ Bedrock**](docs/RELATORIO_CONVERSAO.md)
- ⚠️ [**Relatório de Perdas, Fallbacks e Limitações da Engine**](docs/RELATORIO_PERDAS_E_LIMITACOES.md)
- 📜 [**Relatório de Comandos Não Convertidos e Adaptados**](docs/RELATORIO_COMANDOS_NAO_CONVERTIDOS.md)

---

### Author / Autor
**João Lucas Mayrinck**

---

### License / Licença
Este projeto é distribuído sob a licença **MIT**. Veja o arquivo [`LICENSE`](LICENSE) para mais detalhes.
This project is licensed under the **MIT License**. See the [`LICENSE`](LICENSE) file for details.
