# Invocação de Kai (Idempotente)
execute unless entity @e[type=mazerunner:npc_kai] run summon mazerunner:npc_kai 264 59 -2184
execute unless entity @e[type=mazerunner:npc_kai] run tellraw @a {"rawtext":[{"text":"A§a§l newcomer§r has arrived in the §6§l§oloading area§r!"}]}
