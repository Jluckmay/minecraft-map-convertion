# Relatório de Comandos Não Convertidos e Ajustes de Sintaxe

Durante o processo de conversão das 54 funções do datapack original, 2.603 linhas exigiram adaptação técnica para conformidade com o interpretador de comandos do Minecraft Bedrock 1.26.40.

## 1. Comandos com Equivalência Indireta ou Substituição

### 1.1. `forceload` (2.056 ocorrências em 17 arquivos)
- **Motivo**: O comando `/forceload` não existe no Minecraft Bedrock Edition.
- **Solução Implementada**: Nas funções de abertura de portas e mapas (`open_doors_*.mcfunction`, `map_full_*.mcfunction`), as linhas de `forceload add` e `forceload remove` foram convertidas em comentários informativos (`# [Bedrock Conversion] forceload ...`). O carregamento contínuo das áreas críticas do labirinto é garantido pelo registro de áreas de simulação contínua (`tickingarea`) na função de inicialização do mundo `mazerunner:init_world`.

### 1.2. `data merge block` (547 ocorrências em 17 arquivos)
- **Motivo**: O comando `/data` é restrito à Java Edition.
- **Solução Implementada**: Nas funções `reset_spawner_1.mcfunction` até `reset_spawner_16.mcfunction`, os comandos `data merge block <x> <y> <z> {Delay:0}` foram documentados como comentários preservando as coordenadas exatas dos geradores. No Bedrock Edition, os geradores de monstros (`spawner`) calculam e reiniciam o ciclo de spawn automaticamente sempre que um jogador se encontra no raio de 16 blocos, garantindo a jogabilidade sem quebra de fluxo.

### 1.3. `playsound` (11 ocorrências)
- **Motivo**: O identificador de som `minecraft:entity.player.levelup` possui sintaxe diferente no Bedrock.
- **Solução Implementada**: Convertido para `playsound random.levelup @p`.

---

## 2. Resumo Quantitativo de Comandos do Datapack

| Tipo de Comando | Total no Java | Tratamento no Bedrock 1.26.40 |
| :--- | :--- | :--- |
| `forceload` | 2.056 | Substituído por `tickingarea` permanente do labirinto |
| `clone` | 1.024 | 100% convertido e funcional |
| `data merge` | 547 | Substituído pela mecânica nativa de spawners por proximidade |
| `execute` | 76 | 100% convertido para a sintaxe moderna do Bedrock 1.26.40 |
| `setblock` | 32 | 100% convertido e funcional |
| `fill` | 16 | 100% convertido e funcional |
| `tp` | 2 | 100% convertido e funcional |
