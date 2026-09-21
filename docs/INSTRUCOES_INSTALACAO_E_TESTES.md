# Instruções de Instalação, Ativação e Testes / Installation, Activation & Testing Instructions (Bedrock 1.26.40)

*Read in / Leia em:*
- [Português (PT-BR)](#português-pt-br)
- [English (EN)](#english-en)

---

<a name="português-pt-br"></a>
## Português (PT-BR)

### 1. Arquivos Entregues (Diretório `dist/`)
1. **`dist/mazescapist-bedrock-1.26.40.mcworld`**: Mundo completo pronto para uso no Minecraft Bedrock 1.26.40 com os pacotes já vinculados e ativados.
2. **`dist/mazerunner-behavior-pack.mcpack`**: Behavior Pack independente (NPCs, comércio, loot de esmeraldas e funções).
3. **`dist/mazerunner-resource-pack.mcpack`**: Resource Pack independente (texturas de blocos, definições visuais e ícone).
4. **`dist/SHA256SUMS.txt`**: Assinaturas de integridade e verificação criptográfica SHA-256 de todos os pacotes.

---

### 2. Como Instalar no PC (Windows / Mac)

#### Opção A: Importação Direta do Mundo (Recomendada)
1. Dê um duplo-clique no arquivo `dist/mazescapist-bedrock-1.26.40.mcworld`.
2. O Minecraft Bedrock iniciará automaticamente e fará a importação do mundo.
3. O mundo aparecerá na lista de mundos com o nome **§4§lMazescapist** e com o ícone original configurado.
4. Os pacotes de comportamento e textura já estão associados nas configurações do mundo.

#### Opção B: Instalação Manual dos Pacotes
Caso deseje utilizar os pacotes em outro mundo:
1. Dê um duplo clique em `dist/mazerunner-resource-pack.mcpack` e aguarde a mensagem de importação concluída.
2. Dê um duplo clique em `dist/mazerunner-behavior-pack.mcpack` e aguarde a mensagem de importação concluída.
3. Nas configurações do seu mundo, ative o pacote de recursos e o pacote de comportamento.

---

### 3. Como Instalar e Jogar no Celular (Android e iOS)

O arquivo `.mcworld` e os pacotes `.mcpack` são 100% compatíveis com Minecraft Bedrock 1.26.40 para dispositivos móveis (smartphones e tablets).

#### 3.1. No Android
1. **Transferência do Arquivo**:
   - Transfira o arquivo `dist/mazescapist-bedrock-1.26.40.mcworld` para o seu celular (via cabo USB, Google Drive, Telegram, WhatsApp ou download direto).
2. **Importação Direta**:
   - Abra o gerenciador de arquivos do seu aparelho (ex: *Arquivos*, *Files do Google* ou *ZArchiver*).
   - Localize o arquivo `mazescapist-bedrock-1.26.40.mcworld` e toque nele.
   - Selecione **"Abrir com Minecraft"** (ou escolha o Minecraft se aparecer o menu "Abrir como...").
   - O jogo abrirá automaticamente com a notificação: *"Importação do mundo iniciada..."* e em seguida *"Importação do mundo concluída com sucesso"*.
3. **Caso o gerenciador nativo não abra diretamente**:
   - Se o seu aparelho tentar abrir como arquivo compactado (ZIP), utilize o aplicativo gratuito **ZArchiver**: toque e segure no arquivo, selecione *Abrir como* > *Minecraft*.

#### 3.2. No iPhone / iPad (iOS)
1. **Transferência do Arquivo**:
   - Envie o arquivo `dist/mazescapist-bedrock-1.26.40.mcworld` via **AirDrop** do Mac/PC ou salve-o no aplicativo **Arquivos (Files)** via iCloud Drive ou Safari.
2. **Importação**:
   - Abra o app **Arquivos** e toque sobre o arquivo `mazescapist-bedrock-1.26.40.mcworld`.
   - Toque no ícone de compartilhamento (quadrado com seta para cima) e selecione o ícone do **Minecraft**.
   - O Minecraft abrirá e importará o mapa automaticamente.

#### 3.3. Dicas de Jogabilidade e Desempenho no Celular
- **Distância de Renderização**: Recomenda-se configurar entre 6 e 10 pedaços (chunks) em aparelhos intermediários para obter 60 FPS estáveis.
- **Teclado na Tela / Comandos**: Para rodar comandos (`/function mazerunner/init_world`), toque no ícone de chat no topo da tela, clique no botão `/` e cole o comando.
- **Controles de Toque**: Recomenda-se usar o layout de toque moderno com "Mira e Joystick" ou conectar um controle bluetooth.

---

### 4. Procedimento de Inicialização no Jogo
Ao entrar no mundo pela primeira vez como operador (com cheats ativados):

1. **Inicializar Mecanismos e Placar**:
   Abra o chat e execute:
   ```mcfunction
   /function mazerunner/init_world
   ```
   Este comando irá:
   - Registrar o placar de dias (`dayCounter`);
   - Configurar as áreas contínuas (`tickingarea`) do labirinto e das portas;
   - Criar as estátuas comemorativas do Hall da Fama no local original.

2. **Obter Kit Inicial (Opcional)**:
   ```mcfunction
   /function mazerunner/starter_kit
   ```

---

### 5. Testes de Validação Recomendados

1. **Teste de Idempotência dos NPCs**:
   ```mcfunction
   /scoreboard players set DAY_COUNTER dayCounter 4
   /function custom/generates_npc
   ```
   - O aldeão **Bruce** aparecerá na área de carregamento (`264, 59, -2184`) com suas trocas originais.
   - Execute `/function custom/generates_npc` uma segunda vez.
   - **Resultado esperado**: Nenhum aldeão duplicado será gerado.

2. **Teste de Portas do Labirinto**:
   ```mcfunction
   /function custom/open_doors_1
   ```
   - A Porta 1 abrirá instantaneamente sem corrupção de blocos.
   ```mcfunction
   /function custom/close_all_doors
   ```
   - Todas as portas se fecharão perfeitamente.

3. **Teste de Loot de Monstros**:
   - Invoque um Zumbi ou Blaze e derrote-o.
   - **Resultado esperado**: O monstro dropará esmeraldas conforme a economia do datapack.

---

### 6. Hashes de Integridade (SHA-256)

Consulte o arquivo [`dist/SHA256SUMS.txt`](../dist/SHA256SUMS.txt) para as assinaturas mais recentes geradas pela ferramenta de build.

---

<a name="english-en"></a>
## English (EN)

### 1. Delivered Files (`dist/` Directory)
1. **`dist/mazescapist-bedrock-1.26.40.mcworld`**: Complete world ready to play on Minecraft Bedrock 1.26.40 with attached and pre-activated packs.
2. **`dist/mazerunner-behavior-pack.mcpack`**: Standalone Behavior Pack (custom NPCs, trading tables, emerald drops, and functions).
3. **`dist/mazerunner-resource-pack.mcpack`**: Standalone Resource Pack (block textures, client entity definitions, and icon).
4. **`dist/SHA256SUMS.txt`**: SHA-256 cryptographic verification checksums for all packages.

---

### 2. How to Install on PC (Windows / Mac)

#### Option A: Direct World Import (Recommended)
1. Double-click the `dist/mazescapist-bedrock-1.26.40.mcworld` file.
2. Minecraft Bedrock will launch automatically and import the world.
3. The world will appear in your world list named **§4§lMazescapist** with its custom icon.
4. Behavior and Resource packs are already activated in the world settings.

#### Option B: Standalone Pack Installation
If you want to use the packs in another world:
1. Double-click `dist/mazerunner-resource-pack.mcpack` and wait for the import notification.
2. Double-click `dist/mazerunner-behavior-pack.mcpack` and wait for the import notification.
3. In your target world settings, activate both packs.

---

### 3. How to Install and Play on Mobile (Android & iOS)

The `.mcworld` and `.mcpack` files are 100% compatible with Minecraft Bedrock 1.26.40 on mobile devices (smartphones and tablets).

#### 3.1. On Android
1. **File Transfer**:
   - Transfer `dist/mazescapist-bedrock-1.26.40.mcworld` to your device (via USB cable, Google Drive, Telegram, WhatsApp, or browser download).
2. **Direct Import**:
   - Open your file manager app (e.g., *Files by Google*, *Files*, or *ZArchiver*).
   - Tap on the `mazescapist-bedrock-1.26.40.mcworld` file.
   - Choose **"Open with Minecraft"** (or select Minecraft from the "Open with..." menu).
   - Minecraft will launch and show: *"World import started..."* followed by *"World import completed successfully"*.
3. **Troubleshooting**:
   - If your system file manager tries to extract it as a ZIP, use the free app **ZArchiver**: long-press the file, tap *Open as* > *Minecraft*.

#### 3.2. On iPhone / iPad (iOS)
1. **File Transfer**:
   - AirDrop `dist/mazescapist-bedrock-1.26.40.mcworld` from your Mac/PC or download it to the **Files** app via Safari / iCloud Drive.
2. **Import**:
   - In the **Files** app, tap the `mazescapist-bedrock-1.26.40.mcworld` file.
   - Tap the Share button (square with an arrow pointing up) and select **Minecraft**.
   - Minecraft will launch and import the world automatically.

#### 3.3. Mobile Performance & Gameplay Tips
- **Render Distance**: Set between 6 and 10 chunks on mid-range devices to maintain a smooth 60 FPS.
- **On-Screen Keyboard / Commands**: Tap the chat icon at the top of the screen, tap the `/` button, and paste command functions.
- **Touch Controls**: The maze has parkour sections; using the modern "Crosshair & Joystick" layout or a Bluetooth gamepad is recommended.

---

### 4. In-Game Initialization Procedure
Upon loading into the world for the first time as operator (with cheats enabled):

1. **Initialize Game Mechanics & Scoreboards**:
   Open chat and run:
   ```mcfunction
   /function mazerunner/init_world
   ```
   This command will:
   - Register the day counter scoreboard (`dayCounter`);
   - Set up permanent ticking areas (`tickingarea`) for the maze core and doors;
   - Spawn the commemorative Hall of Fame statues at their original positions.

2. **Claim Starter Kit (Optional)**:
   ```mcfunction
   /function mazerunner/starter_kit
   ```

---

### 5. Recommended Validation Tests

1. **NPC Idempotency Test**:
   ```mcfunction
   /scoreboard players set DAY_COUNTER dayCounter 4
   /function custom/generates_npc
   ```
   - Villager **Bruce** appears in the loading hub (`264, 59, -2184`) with original trades.
   - Run `/function custom/generates_npc` a second time.
   - **Expected Result**: No duplicate villager is spawned.

2. **Maze Doors Test**:
   ```mcfunction
   /function custom/open_doors_1
   ```
   - Door 1 opens instantly without block desynchronization.
   ```mcfunction
   /function custom/close_all_doors
   ```
   - All 8 doors close securely.

3. **Mob Emerald Drops Test**:
   - Spawn a Zombie or Blaze and defeat it.
   - **Expected Result**: The mob drops emeralds as defined in the datapack economy.

---

### 6. Integrity Hashes (SHA-256)

Refer to [`dist/SHA256SUMS.txt`](../dist/SHA256SUMS.txt) for the latest build signatures.
