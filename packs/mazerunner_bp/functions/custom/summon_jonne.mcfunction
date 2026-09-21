# Invocação de Jonne (Idempotente)
execute unless entity @e[type=mazerunner:npc_jonne] run summon mazerunner:npc_jonne 264 59 -2184
execute unless entity @e[type=mazerunner:npc_jonne] run tellraw @a {"rawtext":[{"text":"A§a§l newcomer§r has arrived in the §6§l§oloading area§r!"}]}
