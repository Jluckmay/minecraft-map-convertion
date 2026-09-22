# Instruções de Instalação, Ativação e Uso / Installation, Activation & Usage Guide
### Minecraft Bedrock Edition (PC, Android & iOS)

*Read in / Leia em:*
- [Português (PT-BR)](#português-pt-br)
- [English (EN)](#english-en)

---

<a name="português-pt-br"></a>
## Português (PT-BR)

Este guia prático e detalhado explica como instalar, importar e jogar mundos e pacotes convertidos no **Minecraft Bedrock Edition (versões 1.20+ e 1.21+)** no Computador (Windows) e especialmente em celulares/tablets (**Android** e **iOS/iPhone/iPad**).

---

### 1. Arquivos Gerados (Diretório `output/`)

Ao final do pipeline de conversão, quatro formatos de entrega são gerados em [`output/`](file:///c:/Users/jluck/OneDrive/Pictures/Documentos/codes/Github/Originais/map-convertion/output/):

1. **`converted_map.mcworld`** (Recomendado):
   - Arquivo tudo-em-um contendo o mapa completo, terreno LevelDB, command blocks atualizados, baús preservados e os pacotes de comportamento e recursos já embutidos e ativados.
2. **`converted_map.mcaddon`**:
   - Pacote unificado contendo o Behavior Pack e o Resource Pack juntos para instalação em mundos existentes.
3. **`converted_behavior_pack.mcpack`**:
   - Pacote de Comportamento avulso (funções `.mcfunction`, entidades e NPCs customizados, tabelas de comércio e loot tables).
4. **`converted_resource_pack.mcpack`**:
   - Pacote de Recursos avulso (texturas de tijolos na bedrock com variações ponderadas, terracota e áudios).

---

### 2. Preservação de Baús, Contêineres e Inventário do Jogador

Diferente de ferramentas convencionais, este conversor garante a integridade dos itens:
- **Baús e Contêineres de Bloco**: Todos os baús (`Chest`, `TrappedChest`), barris (`Barrel`), caixas de shulker (`ShulkerBox`), funis (`Hopper`), ejetores (`Dispenser`) e liberadores (`Dropper`) têm seus itens, quantidades, slots e NBTs mantidos 100% preservados no banco LevelDB.
- **Inventário do Jogador**: Os itens do inventário principal (slots 0 a 35), armaduras (capacete, peitoral, calça, botas), mão secundária (*offhand*) e baú do fim (*Ender Chest*) presentes no `level.dat` ou em `playerdata` do Java são sincronizados diretamente na entidade `~local_player` do Bedrock.

---

### 3. Instalação no Celular / Mobile (Guia Detalhado)

Instalar arquivos no Minecraft pelo celular pode ser mais desafiador do que no PC devido a restrições de segurança do sistema operacional (como o *Scoped Storage* do Android). Siga os métodos testados abaixo:

#### 3.1. No Android (Android 11, 12, 13, 14 e 15)

> [!WARNING]
> **Atenção ao Scoped Storage**: A partir do Android 11, o Google bloqueou o acesso direto de gerenciadores de arquivos à pasta `/Android/data/com.mojang.minecraftpe/`. **Não tente copiar ou colar arquivos manualmente nessa pasta**. O método correto é a associação de aplicativo via "Abrir Com".

##### Método A: Usando o ZArchiver (Método Mais Seguro e Recomendado)
1. Baixe o aplicativo gratuito **ZArchiver** na Google Play Store.
2. Transfira o arquivo `converted_map.mcworld` para a pasta **Download** do celular.
3. Abra o **ZArchiver** e navegue até a pasta **Download**.
4. Toque sobre o arquivo `converted_map.mcworld`:
   - Toque no ícone de **seta diagonal** ao lado de "Exibir" (ou selecione **"Abrir com"**).
   - Escolha **Minecraft** na lista de aplicativos.
   - Selecione **"Sempre"** ou **"Desta vez"**.
5. O Minecraft abrirá automaticamente exibindo no topo da tela:
   - *"Importação do mundo iniciada..."*
   - *"Importação do mundo concluída com sucesso"*.
6. O mapa estará disponível no topo da sua lista de mundos em **Jogar**.

##### Método B: Download Direto pelo Navegador Móvel
1. Se você baixou o arquivo diretamente pelo navegador do celular (**Google Chrome**, **Samsung Internet** ou **Brave**):
2. Ao concluir o download, toque diretamente na **notificação de download concluído** na barra de status do Android.
3. O Android chamará automaticamente o manipulador de arquivos do Minecraft, disparando a importação direta sem precisar de gerenciador de arquivos.

##### Método C: Usando o app "Files" Nativo ou CX File Explorer
1. No gerenciador **Arquivos** nativo do Android ou no **CX File Explorer**:
2. Localize o arquivo `converted_map.mcworld`.
3. Toque no arquivo e escolha **Minecraft**.

##### Resolução de Problemas no Android:
- **Problema de Extensão Dupla (`.mcworld.zip` ou `.bin`)**: Alguns navegadores ou aplicativos de chat renomeiam o arquivo adicionando `.zip` ao final. No ZArchiver, toque e segure o arquivo, selecione **Renomear** e remova o `.zip`, deixando exatamente com a terminação `.mcworld`.
- **Minecraft não aparece na lista de "Abrir Com"**: Vá em *Configurações do Android > Aplicativos > Minecraft > Abrir por padrão* e verifique se as associações estão ativas. Reinicie o celular caso necessário.
- **Armazenamento do Minecraft**: Dentro do jogo, vá em *Configurações > Armazenamento > Local de Armazenamento do Arquivo*. Recomenda-se deixar em **"Aplicação"** (padrão) para importações diretas, ou **"Externo"** caso utilize cópia de backups.

---

#### 3.2. No iPhone e iPad (iOS / iPadOS)

O iOS possui integração nativa simples com extensões do Minecraft:

##### Método A: Pelo Aplicativo "Arquivos" (Files)
1. Baixe o arquivo `converted_map.mcworld` no Safari ou transfira via Google Drive/iCloud.
2. Abra o aplicativo **Arquivos** (Files nativo da Apple).
3. Vá na aba **Explorar** e abra a pasta **Transferências** (Downloads) ou *No Meu iPhone*.
4. Dê um **toque simples** sobre o arquivo `converted_map.mcworld`.
5. O sistema operacional iniciará o Minecraft automaticamente e executará a importação.
6. *Alternativa*: Se o toque simples abrir apenas uma tela de visualização, toque e segure no arquivo, selecione **Compartilhar** e toque no ícone do **Minecraft**.

##### Método B: Transferência Instantânea via AirDrop
1. Se você possui um Mac ou outro dispositivo Apple, envie o arquivo `.mcworld` via **AirDrop** para o iPhone/iPad.
2. No popup que surgir na tela do iPhone, toque em **Abrir com Minecraft**.
3. A importação começará imediatamente.

---

### 4. Como Instalar no Computador (Windows 10/11)

1. Dê um duplo-clique no arquivo `output/converted_map.mcworld`.
2. O Minecraft Bedrock iniciará automaticamente e importará o mundo.
3. O mundo aparecerá na sua lista pronto para jogar, com Resource Pack e Behavior Pack integrados.

---

### 5. Dicas de Jogabilidade e Desempenho no Celular

- **Distância de Renderização**: Em celulares intermediários, defina a distância de renderização entre **6 e 10 pedaços (chunks)** nas configurações de vídeo para manter 60 FPS estáveis.
- **Esquema de Controle**: Para mapas com labirintos e áreas de salto, recomenda-se ativar o layout de toque moderno com joystick virtual (*Configurações > Toque > Selecionar Esquema de Controle > Joystick e tocar para interagir*) ou conectar um controle Bluetooth (Xbox, DualShock/DualSense ou controle mobile).
- **Ativação Inicial de Redstone**: Ao entrar no mundo, as áreas de ticking permanentes mantêm as portas ativas e sincronizadas automaticamente.

---

<a name="english-en"></a>
## English (EN)

This comprehensive guide explains how to install, import, and play converted worlds and packages on **Minecraft Bedrock Edition (versions 1.20+ and 1.21+)** across PC (Windows) and mobile devices (**Android** and **iOS/iPhone/iPad**).

---

### 1. Generated Deliverables (`output/` Directory)

The conversion pipeline generates four delivery packages in [`output/`](file:///c:/Users/jluck/OneDrive/Pictures/Documentos/codes/Github/Originais/map-convertion/output/):

1. **`converted_map.mcworld`** (Recommended):
   - All-in-one world package with converted LevelDB terrain, updated command blocks, preserved chests, and pre-activated Behavior and Resource packs.
2. **`converted_map.mcaddon`**:
   - Unified addon package containing both Behavior and Resource packs for installation into existing worlds.
3. **`converted_behavior_pack.mcpack`**:
   - Standalone Behavior Pack (`.mcfunction` scripts, custom entities/NPCs, trade tables, and loot tables).
4. **`converted_resource_pack.mcpack`**:
   - Standalone Resource Pack (bedrock brick texture variations, glazed terracotta, and custom sounds).

---

### 2. Preservation of Chests, Containers, and Player Inventory

Unlike standard converters, this tool guarantees data preservation:
- **Block Containers**: Normal chests (`Chest`), trapped chests (`TrappedChest`), barrels (`Barrel`), shulker boxes (`ShulkerBox`), hoppers (`Hopper`), dispensers (`Dispenser`), and droppers (`Dropper`) retain 100% of their item IDs, quantities, slot mappings, and NBTs in LevelDB.
- **Player Inventory**: Main inventory slots (0 to 35), armor slots (helmet, chestplate, leggings, boots), offhand item, and Ender Chest items from Java `level.dat` or `playerdata` are directly mapped and synchronized into Bedrock's `~local_player` compound.

---

### 3. Mobile Installation Guide (Android & iOS)

Installing files on mobile devices requires specific steps due to operating system security policies (such as Android Scoped Storage).

#### 3.1. On Android (Android 11, 12, 13, 14, and 15)

> [!WARNING]
> **Scoped Storage Notice**: Android 11+ restricts file managers from writing directly to `/Android/data/com.mojang.minecraftpe/`. **Do not attempt to paste files manually into system directories**. Use the system "Open With" intent association.

##### Method A: Using ZArchiver (Recommended & Most Reliable)
1. Install the free **ZArchiver** app from Google Play Store.
2. Copy or download `converted_map.mcworld` to your device's **Download** folder.
3. Open **ZArchiver** and navigate to **Download**.
4. Tap the `converted_map.mcworld` file:
   - Tap the **diagonal arrow icon** next to "View" (or long-press and choose **"Open with"**).
   - Select **Minecraft** from the application list.
   - Choose **"Always"** or **"Just Once"**.
5. Minecraft will launch automatically with top-screen banners:
   - *"World import started..."*
   - *"World import finished successfully"*.
6. Find the imported map at the top of your worlds list in **Play**.

##### Method B: Direct Browser Notification Tap
1. When downloading the `.mcworld` file directly using **Google Chrome**, **Samsung Internet**, or **Brave**:
2. Tap the **Download Completed** notification in your Android status bar.
3. Android will automatically invoke Minecraft's MIME handler to import the world.

##### Method C: Native "Files" App or CX File Explorer
1. In the default Android **Files** app or **CX File Explorer**:
2. Tap the `.mcworld` file and choose **Minecraft**.

##### Android Troubleshooting:
- **Double Extension Issue (`.mcworld.zip` or `.bin`)**: If a browser renames the file to `.zip` or `.bin`, use ZArchiver to rename it and remove the trailing extension so it ends strictly in `.mcworld`.
- **Minecraft Missing from App List**: Navigate to *Android Settings > Apps > Minecraft > Set as default* and verify file associations.
- **File Storage Location**: Inside Minecraft, check *Settings > Storage > File Storage Location*. Keep it set to **"Application"** for direct imports.

---

#### 3.2. On iPhone and iPad (iOS / iPadOS)

##### Method A: Apple "Files" App
1. Download `converted_map.mcworld` using Safari or transfer via iCloud Drive.
2. Open the built-in **Files** app.
3. Go to the **Browse** tab and open **Downloads** (or *On My iPhone*).
4. Tap the `converted_map.mcworld` file once.
5. iOS will immediately launch Minecraft and import the world.
6. *Fallback*: If a single tap shows a file preview, touch and hold the file, select **Share**, and tap the **Minecraft** app icon.

##### Method B: Instant AirDrop Transfer
1. Send the `.mcworld` file from a Mac or PC via **AirDrop** to your iPhone/iPad.
2. In the prompt on your iOS screen, choose **Open with Minecraft**.
3. Import starts instantly.

---

### 4. Installation on PC (Windows 10/11)

1. Double-click the generated `output/converted_map.mcworld` file.
2. Minecraft Bedrock launches automatically and imports the world.
3. The world appears in your worlds list with all packs linked and activated.

---

### 5. Performance and Mobile Gameplay Tips

- **Render Distance**: On mobile devices, set render distance between **6 and 10 chunks** in *Video Settings* for consistent 60 FPS performance.
- **Controls**: For adventure and puzzle maps, enable the modern touch controls with virtual joystick (*Settings > Touch > Touch Control Scheme > Joystick & tap to interact*) or connect a Bluetooth controller (Xbox, PlayStation, or mobile gamepad).
