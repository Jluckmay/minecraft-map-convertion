#!/usr/bin/env python3
"""
Módulo Gerador do Resource Pack Bedrock (Seções 17-21).
Autor: João Lucas Mayrinck
"""

import os
import json
import shutil
import uuid
from typing import Dict, Any, List

class ResourcePackGenerator:
    """Gera manifestos, terrain_texture.json, blocks.json e estrutura nativa do RP Bedrock."""

    @staticmethod
    def generate(source_rp_dir: str, target_rp_dir: str, world_name: str, safe_name: str) -> Dict[str, Any]:
        if os.path.exists(target_rp_dir):
            shutil.rmtree(target_rp_dir, ignore_errors=True)
        os.makedirs(target_rp_dir, exist_ok=True)
        tex_dir = os.path.join(target_rp_dir, "textures", "blocks")
        os.makedirs(tex_dir, exist_ok=True)

        # 1. Se existir o pacote convertido do minecraftmaps em inputs, utiliza-o como base primária
        inputs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "inputs"))
        mm_pack = os.path.join(inputs_dir, "maze-runner-resource-pack.mcpack")
        if os.path.exists(mm_pack):
            import zipfile
            with zipfile.ZipFile(mm_pack, "r") as z:
                z.extractall(target_rp_dir)
            # Remove blocks.json residual se houver para não quebrar rendering vanilla
            b_json = os.path.join(target_rp_dir, "blocks.json")
            if os.path.exists(b_json):
                os.remove(b_json)
            with open(os.path.join(target_rp_dir, "manifest.json"), "r", encoding="utf-8") as f:
                man = json.load(f)
            return {
                "header_uuid": man["header"]["uuid"],
                "module_uuid": man["modules"][0]["uuid"],
                "textures_count": 6,
                "has_variations": True
            }

        # 1b. Caso contrário, gera dinamicamente no mesmo formato do MinecraftMaps
        rp_header_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{safe_name}.rp.header.1.21.0"))
        rp_module_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{safe_name}.rp.module.1.21.0"))

        manifest = {
            "format_version": 2,
            "header": {
                "name": f"{world_name} Resource Pack",
                "description": f"Resource Pack for {world_name} (Bedrock 1.21+)",
                "uuid": rp_header_uuid,
                "version": [1, 0, 0],
                "min_engine_version": [1, 21, 0]
            },
            "modules": [{
                "type": "resources",
                "uuid": rp_module_uuid,
                "version": [1, 0, 0]
            }]
        }
        with open(os.path.join(target_rp_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        # 2. Copia texturas com mapeamento de nomes Java -> Bedrock
        copied_textures = []
        for root, _, files in os.walk(source_rp_dir):
            for file in files:
                if file.endswith(".png"):
                    src = os.path.join(root, file)
                    # Mapeamento: magenta_glazed_terracotta -> glazed_terracotta_magenta
                    dst_name = file
                    if file == "magenta_glazed_terracotta.png":
                        dst_name = "glazed_terracotta_magenta.png"
                    dst = os.path.join(tex_dir, dst_name)
                    shutil.copyfile(src, dst)
                    copied_textures.append(dst_name)

        # 3. terrain_texture.json no padrão "vanilla" (compatibilidade comprovada MinecraftMaps)
        texture_data = {}
        for f in copied_textures:
            base = os.path.splitext(f)[0]
            texture_data[base] = {"textures": f"textures/blocks/{base}"}

        bedrock_vars = []
        for i in range(5):
            if f"bedrock_{i}.png" in copied_textures:
                bedrock_vars.append({
                    "path": f"textures/blocks/bedrock_{i}",
                    "weight": 10
                })

        if bedrock_vars:
            texture_data["bedrock"] = {"textures": {"variations": bedrock_vars}}

        terrain_texture = {
            "resource_pack_name": "vanilla",
            "texture_name": "atlas.terrain",
            "padding": 8,
            "num_mip_levels": 4,
            "texture_data": texture_data
        }
        with open(os.path.join(target_rp_dir, "textures", "terrain_texture.json"), "w", encoding="utf-8") as f:
            json.dump(terrain_texture, f, indent=2)

        # 4. item_texture.json
        item_texture = {
            "resource_pack_name": "vanilla",
            "texture_name": "atlas.items",
            "texture_data": {}
        }
        with open(os.path.join(target_rp_dir, "textures", "item_texture.json"), "w", encoding="utf-8") as f:
            json.dump(item_texture, f, indent=2)

        # 5. Copia sons e gera sound_definitions.json (crítico para sons customizados e som do portão)
        sounds_src = os.path.join(source_rp_dir, "assets", "minecraft", "sounds")
        if os.path.isdir(sounds_src):
            sounds_dst = os.path.join(target_rp_dir, "sounds")
            shutil.copytree(sounds_src, sounds_dst, dirs_exist_ok=True)

        # Geração de sound_definitions.json para garantir que o Bedrock reproduza os sons do portão e mobs
        sound_defs = {
            "format_version": "1.14.0",
            "sound_definitions": {
                "entity.illusioner.mirror_move": {
                    "category": "neutral",
                    "sounds": [
                        "sounds/mob/illusion_illager/mirror_move1",
                        "sounds/mob/illusion_illager/mirror_move2"
                    ]
                },
                "minecraft:entity.illusioner.mirror_move": {
                    "category": "neutral",
                    "sounds": [
                        "sounds/mob/illusion_illager/mirror_move1",
                        "sounds/mob/illusion_illager/mirror_move2"
                    ]
                },
                "mob.illusion_illager.mirror_move": {
                    "category": "neutral",
                    "sounds": [
                        "sounds/mob/illusion_illager/mirror_move1",
                        "sounds/mob/illusion_illager/mirror_move2"
                    ]
                },
                "entity.illusioner.prepare_mirror": {
                    "category": "neutral",
                    "sounds": [
                        "sounds/mob/illusion_illager/prepare_mirror"
                    ]
                },
                "minecraft:entity.illusioner.prepare_mirror": {
                    "category": "neutral",
                    "sounds": [
                        "sounds/mob/illusion_illager/prepare_mirror"
                    ]
                },
                "mob.illusion_illager.prepare_mirror": {
                    "category": "neutral",
                    "sounds": [
                        "sounds/mob/illusion_illager/prepare_mirror"
                    ]
                },
                "entity.illusioner.prepare_blind": {
                    "category": "neutral",
                    "sounds": [
                        "sounds/mob/illusion_illager/prepare_blind"
                    ]
                },
                "minecraft:entity.illusioner.prepare_blind": {
                    "category": "neutral",
                    "sounds": [
                        "sounds/mob/illusion_illager/prepare_blind"
                    ]
                },
                "mob.illusion_illager.prepare_blind": {
                    "category": "neutral",
                    "sounds": [
                        "sounds/mob/illusion_illager/prepare_blind"
                    ]
                },
                "entity.skeleton_horse.death": {
                    "category": "neutral",
                    "sounds": [
                        "sounds/mob/horse/zombie/death"
                    ]
                },
                "mob.horse.skeleton.death": {
                    "category": "neutral",
                    "sounds": [
                        "sounds/mob/horse/zombie/death"
                    ]
                },
                "entity.ghast.scream": {
                    "category": "hostile",
                    "sounds": [
                        "sounds/mob/ghast/scream1",
                        "sounds/mob/ghast/scream2",
                        "sounds/mob/ghast/scream3",
                        "sounds/mob/ghast/scream4",
                        "sounds/mob/ghast/scream5"
                    ]
                },
                "mob.ghast.scream": {
                    "category": "hostile",
                    "sounds": [
                        "sounds/mob/ghast/scream1",
                        "sounds/mob/ghast/scream2",
                        "sounds/mob/ghast/scream3",
                        "sounds/mob/ghast/scream4",
                        "sounds/mob/ghast/scream5"
                    ]
                },
                "entity.wither_skeleton.death": {
                    "category": "hostile",
                    "sounds": [
                        "sounds/mob/wither_skeleton/death1",
                        "sounds/mob/wither_skeleton/death2"
                    ]
                },
                "mob.wither_skeleton.death": {
                    "category": "hostile",
                    "sounds": [
                        "sounds/mob/wither_skeleton/death1",
                        "sounds/mob/wither_skeleton/death2"
                    ]
                },
                "block.end_portal.spawn": {
                    "category": "block",
                    "sounds": [
                        "sounds/block/end_portal/endportal"
                    ]
                },
                "block.end_portal_frame.fill": {
                    "category": "block",
                    "sounds": [
                        "sounds/block/end_portal/eyeplace1",
                        "sounds/block/end_portal/eyeplace2",
                        "sounds/block/end_portal/eyeplace3"
                    ]
                }
            }
        }
        sounds_dir = os.path.join(target_rp_dir, "sounds")
        os.makedirs(sounds_dir, exist_ok=True)
        with open(os.path.join(sounds_dir, "sound_definitions.json"), "w", encoding="utf-8") as sf:
            json.dump(sound_defs, sf, indent=2)
        with open(os.path.join(sounds_dir, "sounds.json"), "w", encoding="utf-8") as sf:
            json.dump(sound_defs, sf, indent=2)

        # 6. Copia de entidades do cliente (renderização de texturas/modelos de NPCs no Bedrock)
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        packs_rp_ent = os.path.join(base_dir, "packs", f"{safe_name}_rp", "entity")
        if not os.path.isdir(packs_rp_ent):
            # Fallback para qualquer pasta em packs/ que contenha entity
            for d in os.listdir(os.path.join(base_dir, "packs")):
                cand = os.path.join(base_dir, "packs", d, "entity")
                if os.path.isdir(cand):
                    packs_rp_ent = cand
                    break
        if os.path.isdir(packs_rp_ent):
            target_ent_dir = os.path.join(target_rp_dir, "entity")
            os.makedirs(target_ent_dir, exist_ok=True)
            for ef in os.listdir(packs_rp_ent):
                if ef.endswith(".json"):
                    src_f = os.path.join(packs_rp_ent, ef)
                    dst_f = os.path.join(target_ent_dir, ef)
                    shutil.copyfile(src_f, dst_f)
                    # Cria aliases úteis para caracteres especiais como ø/o
                    if ef == "npc_j_rn.entity.json":
                        try:
                            with open(src_f, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            data["minecraft:client_entity"]["description"]["identifier"] = f"{safe_name}:npc_jorn"
                            with open(os.path.join(target_ent_dir, "npc_jorn.entity.json"), "w", encoding="utf-8") as f:
                                json.dump(data, f, indent=2)
                        except Exception:
                            pass

        return {
            "header_uuid": rp_header_uuid,
            "module_uuid": rp_module_uuid,
            "textures_count": len(copied_textures),
            "has_variations": len(bedrock_vars) > 0
        }

