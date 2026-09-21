# Mazescapist Bedrock 1.26.40 World Initialization
scoreboard objectives add dayCounter dummy Day
tickingarea add 250 0 -2250 330 80 -2150 maze_core
tickingarea add 120 50 -2460 320 100 -1840 maze_doors
function mazerunner/setup_hall_of_fame
tellraw @a {"rawtext":[{"text":"§a[Mazescapist]§r World initialized for Bedrock 1.26.40!"}]}
