# Instruções de Instalação, Ativação e Uso / Installation, Activation & Usage Guide (Bedrock 1.26.40+)

*Read in / Leia em:*
- [Português (PT-BR)](#português-pt-br)
- [English (EN)](#english-en)

---

<a name="português-pt-br"></a>
## Português (PT-BR)

Este guia orienta como importar, ativar e jogar qualquer mundo e pacotes convertidos para o **Minecraft Bedrock Edition 1.26.40+**.

### 1. Arquivos Gerados (Diretório `dist/`)

Após executar o conversor `map_converter.py`, os seguintes arquivos serão gerados na pasta `dist/`:
1. **`<nome_do_mundo>-bedrock.mcworld`**: Arquivo de mundo completo pronto para importação, já com o terreno LevelDB e os pacotes vinculados.
2. **`<nome_do_mundo>-behavior-pack.mcpack`**: Pacote de Comportamento (Behavior Pack) independente com entidades customizadas, tabelas de troca, loot tables e funções.
3. **`<nome_do_mundo>-resource-pack.mcpack`**: Pacote de Recursos (Resource Pack) independente com texturas de blocos e definições visuais de cliente.
4. **`SHA256SUMS.txt`**: Assinaturas de integridade e verificação criptográfica SHA-256 dos entregáveis gerados.

---

### 2. Como Instalar no PC (Windows / macOS)

#### Opção A: Importação Direta do Mundo (Recomendada)
1. Dê um duplo-clique no arquivo `.mcworld` gerado em `dist/`.
2. O Minecraft Bedrock iniciará automaticamente e realizará a importação do mundo.
3. O mundo aparecerá na sua lista de mundos com os pacotes de comportamento e recursos já ativados.

#### Opção B: Instalação Manual dos Pacotes
Caso deseje utilizar os pacotes em outro mundo:
1. Dê um duplo-clique no arquivo `.mcpack` de recursos e aguarde a notificação de importação.
2. Dê um duplo-clique no arquivo `.mcpack` de comportamento e aguarde a notificação de importação.
3. Nas configurações do seu mundo de destino, ative ambos os pacotes.

---

### 3. Como Instalar e Jogar no Celular (Android e iOS)

Os arquivos `.mcworld` e `.mcpack` são 100% compatíveis com Minecraft Bedrock Edition em dispositivos móveis (smartphones e tablets).

#### 3.1. No Android
1. **Transferência do Arquivo**:
   - Transfira o arquivo `.mcworld` gerado para o celular (via cabo USB, Google Drive, Telegram, WhatsApp ou download direto).
2. **Importação Direta**:
   - Abra o gerenciador de arquivos do aparelho (ex: *Arquivos*, *Files do Google* ou *ZArchiver*).
   - Toque sobre o arquivo `.mcworld`.
   - Selecione **"Abrir com Minecraft"** (ou escolha Minecraft no menu de aplicativos).
   - O jogo iniciará com a notificação: *"Importação do mundo iniciada..."* e *"Importação concluída com sucesso"*.
3. **Resolução de Problemas**:
   - Se o gerenciador do sistema tentar abrir o arquivo como compactado (ZIP), utilize o aplicativo gratuito **ZArchiver**: toque e segure no arquivo, selecione *Abrir como* > *Minecraft*.

#### 3.2. No iPhone / iPad (iOS)
1. **Transferência do Arquivo**:
   - Envie o arquivo `.mcworld` via **AirDrop** ou salve-o no aplicativo **Arquivos (Files)** via iCloud Drive ou Safari.
2. **Importação**:
   - No app **Arquivos**, toque sobre o arquivo `.mcworld`.
   - Toque no botão Compartilhar (ícone com seta para cima) e selecione o **Minecraft**.
   - O Minecraft abrirá e importará o mundo automaticamente.

#### 3.3. Dicas de Desempenho no Celular
- **Distância de Renderização**: Para mapas grandes ou labirintos complexos, recomenda-se configurar entre 6 e 10 pedaços (chunks) em aparelhos intermediários para obter 60 FPS consistentes.
- **Controles**: Mapas de aventura com trechos de parkour funcionam melhor com o layout de toque moderno com joystick ou conectando um controle Bluetooth (Xbox, PlayStation ou genérico).

---

### 4. Inicialização no Jogo
Ao entrar no mundo pela primeira vez como operador (com cheats ativados):
- Se o mapa possuir funções de inicialização geradas, execute no chat:
  ```mcfunction
  /function <namespace>/init_world
  ```

---

<a name="english-en"></a>
## English (EN)

This guide explains how to import, activate, and play any converted world and packs on **Minecraft Bedrock Edition 1.26.40+**.

### 1. Generated Deliverables (`dist/` Directory)

After running the `map_converter.py` tool, the following files are produced in the `dist/` directory:
1. **`<world_name>-bedrock.mcworld`**: Complete world file ready to import, containing the LevelDB terrain and pre-linked Behavior/Resource packs.
2. **`<world_name>-behavior-pack.mcpack`**: Standalone Behavior Pack containing custom entities, trade tables, loot tables, and functions.
3. **`<world_name>-resource-pack.mcpack`**: Standalone Resource Pack containing block textures and client definitions.
4. **`SHA256SUMS.txt`**: Cryptographic SHA-256 integrity checksums for all generated files.

---

### 2. How to Install on PC (Windows / macOS)

#### Option A: Direct World Import (Recommended)
1. Double-click the generated `.mcworld` file inside `dist/`.
2. Minecraft Bedrock will launch automatically and import the world.
3. The world will appear in your worlds list with all packs pre-activated.

#### Option B: Standalone Pack Installation
To use the converted packs in another world:
1. Double-click the Resource Pack `.mcpack` file and wait for the import notification.
2. Double-click the Behavior Pack `.mcpack` file and wait for the import notification.
3. In your target world settings, activate both packs.

---

### 3. How to Install and Play on Mobile (Android & iOS)

The generated `.mcworld` and `.mcpack` files are 100% compatible with Minecraft Bedrock Edition on mobile devices (smartphones and tablets).

#### 3.1. On Android
1. **File Transfer**:
   - Transfer the `.mcworld` file to your mobile device (via USB cable, Google Drive, Telegram, WhatsApp, or browser download).
2. **Direct Import**:
   - Open your file manager (e.g., *Files by Google*, *Files*, or *ZArchiver*).
   - Tap the `.mcworld` file.
   - Choose **"Open with Minecraft"** (or select Minecraft from the app list).
   - Minecraft will launch and show *"World import started..."* followed by *"World import completed successfully"*.
3. **Troubleshooting**:
   - If your file manager attempts to treat it as a ZIP, use the free app **ZArchiver**: long-press the file, select *Open as* > *Minecraft*.

#### 3.2. On iPhone / iPad (iOS)
1. **File Transfer**:
   - Send the `.mcworld` file via **AirDrop** or save it to the **Files** app via iCloud Drive / Safari.
2. **Import**:
   - In the **Files** app, tap the `.mcworld` file.
   - Tap the Share button (square with arrow) and select **Minecraft**.
   - Minecraft will open and import the world automatically.

#### 3.3. Mobile Performance Tips
- **Render Distance**: For large adventure maps, setting render distance between 6 and 10 chunks on mid-range devices ensures smooth 60 FPS gameplay.
- **Controls**: For adventure maps requiring precise movement, connecting a Bluetooth gamepad (Xbox, PlayStation, or generic) is highly recommended.

---

### 4. In-Game Initialization
When entering the world for the first time as operator (with cheats enabled):
- If the converted map includes an initialization function, run in chat:
  ```mcfunction
  /function <namespace>/init_world
  ```
