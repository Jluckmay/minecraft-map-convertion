#!/usr/bin/env python3
"""
Suíte de Testes Automatizados e Universais:
Minecraft Map Converter & Bridge Tool: Java <-> Bedrock (1.26.40+)
Autor: João Lucas Mayrinck
"""

import os
import sys
import json
import zipfile
import tempfile
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from map_converter import (
    DatapackConverter,
    LootTableConverter,
    NPCTradeExtractor,
    MapConverterApp,
    sha256_file
)


class TestUniversalMapConverter(unittest.TestCase):
    """Testes unitários e de integração do motor de conversão universal."""

    def test_01_tellraw_color_conversion(self):
        """Testa conversão de tellraw Java com cores para Bedrock rawtext."""
        java_cmd = 'tellraw @a {"text":"Bem-vindo ao labirinto","color":"green"}'
        bedrock_cmd = DatapackConverter.convert_command(java_cmd)
        self.assertIn('"rawtext"', bedrock_cmd)
        self.assertIn("§aBem-vindo ao labirinto", bedrock_cmd)

    def test_02_playsound_translation(self):
        """Testa mapeamento de sons Java para identificadores Bedrock."""
        java_cmd = "playsound minecraft:entity.player.levelup master @p"
        bedrock_cmd = DatapackConverter.convert_command(java_cmd)
        self.assertIn("playsound random.levelup @p", bedrock_cmd)
        self.assertNotIn("master", bedrock_cmd)

    def test_03_forceload_and_data_merge(self):
        """Testa conversão de comandos exclusivos de Java (/forceload e /data merge)."""
        f_cmd = "forceload add 100 100 200 200"
        conv_f = DatapackConverter.convert_command(f_cmd)
        self.assertTrue(conv_f.startswith("# [Bedrock Conversion]"))

        d_cmd = "data merge block 10 20 30 {Delay:0}"
        conv_d = DatapackConverter.convert_command(d_cmd)
        self.assertTrue(conv_d.startswith("# [Bedrock Conversion]"))

    def test_04_loot_table_conversion(self):
        """Testa conversão de pools, rolls e funções em loot tables."""
        java_loot = {
            "pools": [
                {
                    "rolls": 1,
                    "entries": [
                        {
                            "type": "minecraft:item",
                            "name": "minecraft:emerald",
                            "weight": 1,
                            "functions": [
                                {"function": "minecraft:set_count", "count": {"min": 1, "max": 3}},
                                {"function": "minecraft:looting_enchant", "count": {"min": 0, "max": 1}}
                            ]
                        }
                    ]
                }
            ]
        }
        b_loot = LootTableConverter.convert(java_loot)
        self.assertEqual(len(b_loot["pools"]), 1)
        entry = b_loot["pools"][0]["entries"][0]
        self.assertEqual(entry["name"], "minecraft:emerald")
        self.assertEqual(len(entry["functions"]), 2)
        self.assertEqual(entry["functions"][0]["function"], "set_count")
        self.assertEqual(entry["functions"][1]["function"], "looting_enchant")

    def test_05_trade_extraction_and_metadata(self):
        """Testa extração de ofertas NBT e metadados de aldeões de comando summon."""
        cmd = (
            'summon villager 10 65 20 {'
            'CustomName:\'{"text":"Merchant_John"}\','
            'VillagerData:{profession:"minecraft:cleric",type:"minecraft:desert"},'
            'Offers:{Recipes:['
            '{buy:{id:"minecraft:emerald",Count:5b},sell:{id:"minecraft:potion",Count:1b}},'
            '{buy:{id:"minecraft:gold_ingot",Count:3b},buyB:{id:"minecraft:emerald",Count:1b},sell:{id:"minecraft:golden_apple",Count:1b}}'
            ']}}'
        )
        slug, disp_name, prof, biome = NPCTradeExtractor.extract_npc_metadata(cmd)
        self.assertEqual(slug, "merchant_john")
        self.assertEqual(disp_name, "Merchant_John")
        self.assertEqual(prof, "cleric")
        self.assertEqual(biome, "desert")

        trades = NPCTradeExtractor.parse_trades_from_command(cmd)
        self.assertEqual(len(trades), 2)
        self.assertEqual(trades[0]["buy"], "emerald")
        self.assertEqual(trades[0]["buy_count"], 5)
        self.assertEqual(trades[0]["sell"], "potion")
        self.assertEqual(trades[0]["sell_count"], 1)

        self.assertEqual(trades[1]["buy"], "gold_ingot")
        self.assertEqual(trades[1]["buyB"], "emerald")
        self.assertEqual(trades[1]["sell"], "golden_apple")

    def test_06_idempotent_summon_wrapping(self):
        """Testa inserção automática de cláusula de idempotência em invocações."""
        cmd = "summon namespace:npc_trader 100 64 200"
        conv = DatapackConverter.convert_command(cmd, known_npcs={"trader"})
        self.assertTrue(conv.startswith("execute unless entity @e[type=namespace:npc_trader] run summon"))

    def test_07_end_to_end_synthetic_conversion(self):
        """Testa o fluxo completo do conversor utilizando um mundo sintético em memória."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            java_zip_path = os.path.join(tmp_dir, "synthetic_java.zip")
            bedrock_mcworld_path = os.path.join(tmp_dir, "synthetic_bedrock.mcworld")
            out_dir = os.path.join(tmp_dir, "dist")
            packs_dir = os.path.join(tmp_dir, "packs")

            # Cria mock do Java zip
            with zipfile.ZipFile(java_zip_path, "w") as z:
                # Função com summon e tellraw
                fn_content = (
                    'summon villager 0 64 0 {CustomName:\'{"text":"Alex"}\',VillagerData:{profession:"minecraft:fletcher",type:"minecraft:plains"},Offers:{Recipes:[{buy:{id:"minecraft:stick",Count:32b},sell:{id:"minecraft:emerald",Count:1b}}]}}\n'
                    'tellraw @a {"text":"Villager spawned","color":"gold"}\n'
                )
                z.writestr("datapacks/custom_pack/data/custom/functions/spawn_trader.mcfunction", fn_content)
                # Loot table
                loot_content = json.dumps({"pools": [{"rolls": 1, "entries": [{"name": "minecraft:iron_ingot", "functions": []}]}]})
                z.writestr("datapacks/custom_pack/data/custom/loot_tables/entities/custom_mob.json", loot_content)

            # Cria mock do Bedrock mcworld inicial do Chunker
            with zipfile.ZipFile(bedrock_mcworld_path, "w") as z:
                z.writestr("db/CURRENT", "CURRENT LEVELDB")
                z.writestr("level.dat", b"MOCK_LEVEL_DAT")

            # Executa conversor
            app = MapConverterApp(
                java_zip=java_zip_path,
                bedrock_world=bedrock_mcworld_path,
                output_dir=out_dir,
                packs_dir=packs_dir,
                world_name="TestAdventure",
                keep_temp=False
            )
            app.run()

            # Verificações
            expected_mcworld = os.path.join(out_dir, "testadventure-bedrock.mcworld")
            expected_bp = os.path.join(out_dir, "testadventure-behavior-pack.mcpack")
            expected_rp = os.path.join(out_dir, "testadventure-resource-pack.mcpack")
            sha_file = os.path.join(out_dir, "SHA256SUMS.txt")

            self.assertTrue(os.path.exists(expected_mcworld), "MCWORLD final não gerado")
            self.assertTrue(os.path.exists(expected_bp), "Behavior pack não gerado")
            self.assertTrue(os.path.exists(expected_rp), "Resource pack não gerado")
            self.assertTrue(os.path.exists(sha_file), "SHA256SUMS não gerado")

            # Valida manifesto do BP
            bp_man_path = os.path.join(packs_dir, "testadventure_bp", "manifest.json")
            self.assertTrue(os.path.exists(bp_man_path))
            with open(bp_man_path, "r", encoding="utf-8") as f:
                bp_data = json.load(f)
                self.assertEqual(bp_data["format_version"], 2)
                self.assertEqual(bp_data["header"]["min_engine_version"], [1, 26, 40])

            # Valida trade table gerada para Alex
            trade_path = os.path.join(packs_dir, "testadventure_bp", "trading", "alex_trades.json")
            self.assertTrue(os.path.exists(trade_path), "Trade table do NPC Alex não foi gerada")
            with open(trade_path, "r", encoding="utf-8") as f:
                t_data = json.load(f)
                self.assertEqual(t_data["tiers"][0]["trades"][0]["wants"][0]["item"], "stick")
                self.assertEqual(t_data["tiers"][0]["trades"][0]["gives"][0]["item"], "emerald")


if __name__ == "__main__":
    unittest.main(verbosity=2)
