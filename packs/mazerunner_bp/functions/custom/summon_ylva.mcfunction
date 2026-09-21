# Invocação de Ylva (Idempotente)
execute unless entity @e[type=mazerunner:npc_ylva] run summon mazerunner:npc_ylva 264 59 -2184
execute unless entity @e[type=mazerunner:npc_ylva] run tellraw @a {"rawtext":[{"text":"A§a§l newcomer§r has arrived in the §6§l§oloading area§r!"}]}
