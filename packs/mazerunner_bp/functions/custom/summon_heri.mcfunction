# Invocação de Heri (Idempotente)
execute unless entity @e[type=mazerunner:npc_heri] run summon mazerunner:npc_heri 264 59 -2184
execute unless entity @e[type=mazerunner:npc_heri] run tellraw @a {"rawtext":[{"text":"A§a§l newcomer§r has arrived in the §6§l§oloading area§r!"}]}
