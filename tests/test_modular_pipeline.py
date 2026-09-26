#!/usr/bin/env python3
"""
Testes Unitários da Arquitetura Modular do Conversor (converter/)
Autor: João Lucas Mayrinck
"""

import os
import sys
import unittest
import json
import tempfile
import io
import nbtlib

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from converter.commands.translator import CommandTranslator
from converter.world.leveldb_manager import BedrockLevelDBManager
from converter.resource_pack.rp_generator import ResourcePackGenerator
from converter.behavior_pack.bp_generator import BehaviorPackGenerator
from converter.world.anvil_reader import AnvilReader
from converter.world.inventory_manager import PlayerInventoryManager

class TestModularConverterPipeline(unittest.TestCase):
    """Testes unitários dos novos componentes modulares."""

    def test_translator_execute_and_selectors(self):
        """Testa tradução de execute com múltiplos seletores e argumentos."""
        cmd = "/execute as @a at @s if entity @e[type=minecraft:zombie,distance=..25] run playsound minecraft:entity.player.levelup master @p"
        res = CommandTranslator.translate(cmd)
        self.assertFalse(res.startswith("/"))
        self.assertIn("@e[type=zombie,r=25]", res)
        self.assertIn("playsound random.levelup @p", res)
        self.assertNotIn("master", res)

    def test_translator_forceload_to_tickingarea(self):
        """Testa conversão de forceload para tickingarea."""
        cmd = "forceload add 10 20 12 22"
        res = CommandTranslator.translate(cmd)
        self.assertTrue(res.startswith("tickingarea add 160 0 320 207 319 367"))

    def test_translator_tellraw_formatting(self):
        """Testa conversão de tellraw com cores para rawtext com códigos de formatação."""
        cmd = 'tellraw @a {"text":"Fim de jogo","color":"red"}'
        res = CommandTranslator.translate(cmd)
        self.assertIn('"rawtext"', res)
        self.assertIn("§cFim de jogo", res)

    def test_leveldb_manager_block_build_and_parse(self):
        """Testa codificação e decodificação de blocos SSTable LevelDB."""
        entries = [(b"key_a", b"value_1"), (b"key_b", b"value_2")]
        block_bytes = BedrockLevelDBManager.build_block(entries)
        parsed = BedrockLevelDBManager.parse_block_entries(block_bytes)
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0], (b"key_a", b"value_1"))
        self.assertEqual(parsed[1], (b"key_b", b"value_2"))

    def test_anvil_reader_chain_building(self):
        """Testa reconstrução lógica de cadeias de command blocks."""
        mock_cbs = [
            {
                "x": 0, "y": 64, "z": 0, "dimension": "overworld",
                "type": "minecraft:command_block", "command": "say 1",
                "facing": "east", "auto": False, "conditional": False
            },
            {
                "x": 1, "y": 64, "z": 0, "dimension": "overworld",
                "type": "minecraft:chain_command_block", "command": "say 2",
                "facing": "east", "auto": True, "conditional": False
            }
        ]
        cbs, chains = AnvilReader.build_command_chains(mock_cbs)
        self.assertEqual(len(chains), 1)
        self.assertEqual(chains[0]["length"], 2)
        self.assertEqual(cbs[0]["next_block"], [1, 64, 0])
        self.assertEqual(cbs[1]["prev_block"], [0, 64, 0])

    def test_behavior_pack_trades_extraction(self):
        """Testa extração de receitas de aldeões de comando /summon."""
        cmd = 'summon villager 0 64 0 {CustomName:\'{"text":"Comerciante"}\',Offers:{Recipes:[{buy:{id:"minecraft:emerald",Count:5b},sell:{id:"minecraft:diamond",Count:1b}}]}}'
        trades = BehaviorPackGenerator.extract_trades_from_command(cmd)
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0]["wants"][0]["item"], "emerald")
        self.assertEqual(trades[0]["wants"][0]["quantity"], 5)
        self.assertEqual(trades[0]["gives"][0]["item"], "diamond")
        self.assertEqual(trades[0]["gives"][0]["quantity"], 1)

    def test_translator_particle_conversion(self):
        """Testa tradução de /particle com múltiplos argumentos Java para sintaxe Bedrock."""
        cmd = "/particle cloud 176.1 64 -2144.1 0 14 0 0.03 500 force"
        res = CommandTranslator.translate(cmd)
        self.assertEqual(res, "particle minecraft:basic_smoke_particle 176.1 64 -2144.1")

    def test_translator_title_array_to_titleraw(self):
        """Testa conversão de title com JSON array para titleraw com rawtext."""
        cmd = '/title @a title ["",{"text":"Day ","color":"gray"},{"score":{"name":"DAY_COUNTER","objective":"dayCounter"}}]'
        res = CommandTranslator.translate(cmd)
        self.assertTrue(res.startswith("titleraw @a title"))
        self.assertIn('"rawtext"', res)
        self.assertIn("§7Day ", res)
        self.assertIn('"score"', res)

    def test_translator_summon_custom_name(self):
        """Testa conversão de summon com CustomName para sintaxe Bedrock com entidade customizada e idempotência."""
        cmd = 'summon villager 264 59 -2184 {CustomName:\'{"text":"Bruce"}\'}'
        res = CommandTranslator.translate(cmd)
        self.assertEqual(res, 'execute unless entity @e[name="Bruce"] run summon villager_v2 264 59 -2184 0 0 custom:spawn_bruce "Bruce"')

        # Para mob não aldeão, verifica sintaxe válida Bedrock com nametag
        cmd_mob = 'summon zombie 264 59 -2184 {CustomName:\'{"text":"Boss"}\'}'
        res_mob = CommandTranslator.translate(cmd_mob)
        self.assertEqual(res_mob, 'summon zombie 264 59 -2184 0 0 "" "Boss"')

    def test_inventory_manager_create_bedrock_item(self):
        """Testa construção de item Bedrock a partir de dados Java."""
        item_data = {
            "id": "minecraft:iron_sword",
            "count": 1,
            "damage": 15,
            "tag": nbtlib.Compound({"display": nbtlib.Compound({"Name": nbtlib.String('{"text":"Espada"}')})})
        }
        b_item = PlayerInventoryManager.create_bedrock_item(0, item_data)
        self.assertEqual(int(b_item["Slot"]), 0)
        self.assertEqual(str(b_item["Name"]), "minecraft:iron_sword")
        self.assertEqual(int(b_item["Count"]), 1)
        self.assertEqual(int(b_item["Damage"]), 15)
        self.assertIn("tag", b_item)

    def test_inventory_manager_extract_java_player_data(self):
        """Testa extração de inventário de diretório Java (mesmo com inventário vazio)."""
        java_world_dir = os.path.join(BASE_DIR, "extracted", "java_world")
        if os.path.isdir(java_world_dir):
            pdata = PlayerInventoryManager.extract_java_player_data(java_world_dir)
            self.assertIn("inventory", pdata)
            self.assertIn("armor", pdata)
            self.assertIn("offhand", pdata)
            self.assertIn("ender_items", pdata)

if __name__ == "__main__":
    unittest.main(verbosity=2)

