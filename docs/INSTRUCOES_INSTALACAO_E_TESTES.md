# Instruções de Instalação, Ativação e Testes (Bedrock 1.26.40)

## 1. Arquivos Entregues (Diretório `dist/`)
1. **`dist/mazescapist-bedrock-1.26.40.mcworld`**: Mundo completo pronto para uso no Minecraft Bedrock 1.26.40 com os pacotes já vinculados e ativados.
2. **`dist/mazerunner-behavior-pack.mcpack`**: Behavior Pack independente (NPCs, comércio, loot de esmeraldas e funções).
3. **`dist/mazerunner-resource-pack.mcpack`**: Resource Pack independente (texturas de blocos, definições visuais e ícone).
4. **`dist/SHA256SUMS.txt`**: Assinaturas de integridade e verificação criptográfica SHA-256 de todos os pacotes.

---

## 2. Como Instalar no PC (Windows / Mac)

### Opção A: Importação Direta do Mundo (Recomendada)
1. Dê um duplo-clique no arquivo `mazescapist-bedrock-1.26.40.mcworld`.
2. O Minecraft Bedrock iniciará automaticamente e fará a importação do mundo.
3. O mundo aparecerá na lista de mundos com o nome **§4§lMazescapist** e com o ícone original configurado.
4. Os pacotes de comportamento e textura já estão associados nas configurações do mundo.

### Opção B: Instalação Manual dos Pacotes
Caso deseje utilizar os pacotes em outro mundo:
1. Dê um duplo clique em `mazerunner-resource-pack.mcpack` e aguarde a mensagem de importação concluída.
2. Dê um duplo clique em `mazerunner-behavior-pack.mcpack` e aguarde a mensagem de importação concluída.
3. Nas configurações do seu mundo, ative o pacote de recursos e o pacote de comportamento.

---

## 3. Como Instalar e Jogar no Celular (Android e iOS)

O arquivo `.mcworld` e os pacotes `.mcpack` são 100% compatíveis com Minecraft Bedrock 1.26.40 para dispositivos móveis (smartphones e tablets).

### 3.1. No Android
1. **Transferência do Arquivo**:
   - Transfira o arquivo `mazescapist-bedrock-1.26.40.mcworld` para o seu celular (via cabo USB, Google Drive, Telegram, WhatsApp ou download direto).
2. **Importação Direta**:
   - Abra o gerenciador de arquivos do seu aparelho (ex: *Arquivos*, *Files do Google* ou *ZArchiver*).
   - Localize o arquivo `mazescapist-bedrock-1.26.40.mcworld` e toque nele.
   - Selecione **"Abrir com Minecraft"** (ou escolha o Minecraft se aparecer o menu "Abrir como...").
   - O jogo abrirá automaticamente com a notificação no topo da tela: *"Importação do mundo iniciada..."* e em seguida *"Importação do mundo concluída com sucesso"*.
3. **Caso o gerenciador nativo não abra diretamente**:
   - Se o seu aparelho tentar abrir como arquivo compactado (ZIP), utilize o aplicativo gratuito **ZArchiver**: toque e segure no arquivo, selecione *Abrir como* > *Minecraft*.

### 3.2. No iPhone / iPad (iOS)
1. **Transferência do Arquivo**:
   - Envie o arquivo `mazescapist-bedrock-1.26.40.mcworld` via **AirDrop** do Mac/PC ou salve-o no aplicativo **Arquivos (Files)** via iCloud Drive/download no Safari.
2. **Importação**:
   - Abra o app **Arquivos** e toque sobre o arquivo `mazescapist-bedrock-1.26.40.mcworld`.
   - Toque no ícone de compartilhamento (quadrado com seta para cima) e selecione o ícone do **Minecraft**.
   - O Minecraft abrirá e importará o mapa automaticamente.

### 3.3. Dicas de Jogabilidade e Desempenho no Celular
- **Distância de Renderização**: Devido à grande escala do labirinto, recomenda-se configurar a *Distância de Renderização* entre 6 e 10 pedaços (chunks) em aparelhos intermediários para obter 60 FPS estáveis.
- **Teclado na Tela / Comandos**: Para rodar o comando de inicialização (`/function mazerunner/init_world`), toque no ícone de chat no topo da tela, clique no botão `/` (barra) e cole o comando.
- **Controles de Toque**: O labirinto possui trechos com desafios de parkour e passagens rápidas; recomenda-se usar o layout de toque moderno com "Mira e Joystick" ou conectar um controle bluetooth (Xbox, PS4/PS5 ou genérico).

---

## 4. Procedimento de Inicialização no Jogo
Ao entrar no mundo pela primeira vez como operador (com cheats ativados):

1. **Inicializar Mecanismos e Placar**:
   Abra o chat e execute o comando:
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

## 5. Testes de Validação Recomendados

1. **Teste de Idempotência dos NPCs**:
   Execute no chat:
   ```mcfunction
   /scoreboard players set DAY_COUNTER dayCounter 4
   /function custom/generates_npc
   ```
   - O aldeão **Bruce** aparecerá na área de carregamento (`264, 59, -2184`) com suas trocas originais.
   - Execute o comando `/function custom/generates_npc` uma segunda vez.
   - **Resultado esperado**: Nenhum aldeão duplicado será gerado.

2. **Teste de Portas do Labirinto**:
   Execute:
   ```mcfunction
   /function custom/open_doors_1
   ```
   - A Porta 1 abrirá instantaneamente sem corrupção de blocos.
   Execute:
   ```mcfunction
   /function custom/close_all_doors
   ```
   - Todas as portas se fecharão perfeitamente.

3. **Teste de Loot de Monstros**:
   Invoque um Zumbi ou Blaze e derrote-o:
   - **Resultado esperado**: O monstro dropará esmeraldas conforme a economia do datapack.

---

## 6. Hashes de Integridade (SHA-256)

| Arquivo | Tamanho | Hash SHA-256 |
| :--- | :--- | :--- |
| `mazescapist-bedrock-1.26.40.mcworld` | 75.353.550 bytes | `f78d76a13c7152a725ed319eb660f52b2df65a1bb3e9090ae6007e419a68043c` |
| `mazerunner-behavior-pack.mcpack` | 65.634 bytes | `4d47ed85fb6f54976e7ebcc0ba68bef96fd5bdca1343947b9fc061dfe7e3d3bd` |
| `mazerunner-resource-pack.mcpack` | 20.734 bytes | `70daacd2dd958f9fa9f644f9c3dae7b361dddbb67790f17121adfec631b56197` |
| `bedrock-version.mcworld` (Original) | 75.289.246 bytes | `28c99e1f83982fbc72b01179ef22de7a7a84e69880bcc21a76f12558606ee5f1` |
| `java-version.zip` (Original) | 224.707.649 bytes | `16ac4e38618a47bee3771bb97dd48024ceb6c350a55fa264bdd6cd99cf42833a` |
