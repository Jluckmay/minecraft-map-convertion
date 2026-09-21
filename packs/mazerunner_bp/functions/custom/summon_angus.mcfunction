# Invocação de Angus (Idempotente)
execute unless entity @e[type=mazerunner:npc_angus] run summon mazerunner:npc_angus 264 59 -2184
execute unless entity @e[type=mazerunner:npc_angus] run tellraw @a {"rawtext":[{"text":"A§a§l newcomer§r has arrived in the §6§l§oloading area§r!"}]}
