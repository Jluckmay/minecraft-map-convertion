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
        os.makedirs(target_rp_dir, exist_ok=True)
        tex_dir = os.path.join(target_rp_dir, "textures", "blocks")
        os.makedirs(tex_dir, exist_ok=True)

        # 1. UUIDs estáveis
        rp_header_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{safe_name}.rp.header.1.20.0"))
        rp_module_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{safe_name}.rp.module.1.20.0"))

        manifest = {
            "format_version": 2,
            "header": {
                "name": f"{world_name} Resource Pack",
                "description": f"Resource Pack for {world_name} (Bedrock 1.20+)",
                "uuid": rp_header_uuid,
                "version": [1, 0, 0],
                "min_engine_version": [1, 20, 0]
            },
            "modules": [{
                "type": "resources",
                "description": f"{world_name} RP Resources",
                "uuid": rp_module_uuid,
                "version": [1, 0, 0]
            }]
        }
        with open(os.path.join(target_rp_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        # 2. Copia texturas
        copied_textures = []
        for root, _, files in os.walk(source_rp_dir):
            for file in files:
                if file.endswith(".png"):
                    src = os.path.join(root, file)
                    dst = os.path.join(tex_dir, file)
                    shutil.copyfile(src, dst)
                    copied_textures.append(file)

        # 3. Analisa blockstates para variações de textura
        bedrock_variations = []
        bs_path = os.path.join(source_rp_dir, "assets", "minecraft", "blockstates", "bedrock.json")
        if os.path.exists(bs_path):
            try:
                with open(bs_path, "r", encoding="utf-8") as f:
                    bs = json.load(f)
                variants = bs.get("variants", {}).get("", [])
                if isinstance(variants, list):
                    for var in variants:
                        model = var.get("model", "")
                        weight = var.get("weight", 1)
                        num = model.split("/")[-1]
                        tex_key = f"bedrock_{num}"
                        if f"{tex_key}.png" in copied_textures:
                            bedrock_variations.append({
                                "path": f"textures/blocks/{tex_key}",
                                "weight": weight
                            })
            except Exception:
                pass

        # Fallback de variações se não houver blockstate
        if not bedrock_variations:
            for i in range(5):
                tname = f"bedrock_{i}.png"
                if tname in copied_textures:
                    bedrock_variations.append({
                        "path": f"textures/blocks/bedrock_{i}",
                        "weight": 20
                    })

        # 4. terrain_texture.json
        texture_data = {}
        for f in copied_textures:
            base = os.path.splitext(f)[0]
            texture_data[base] = {"textures": f"textures/blocks/{base}"}

        if bedrock_variations:
            texture_data["bedrock"] = {"textures": {"variations": bedrock_variations}}
            texture_data["minecraft_bedrock"] = texture_data["bedrock"]

            # Fallback bedrock.png
            b0_path = os.path.join(tex_dir, "bedrock_0.png")
            b_fallback = os.path.join(tex_dir, "bedrock.png")
            if os.path.exists(b0_path) and not os.path.exists(b_fallback):
                shutil.copyfile(b0_path, b_fallback)

        terrain_texture = {
            "resource_pack_name": safe_name,
            "texture_name": "atlas.terrain",
            "padding": 8,
            "num_mip_levels": 4,
            "texture_data": texture_data
        }
        with open(os.path.join(target_rp_dir, "textures", "terrain_texture.json"), "w", encoding="utf-8") as f:
            json.dump(terrain_texture, f, indent=2)

        # 5. blocks.json
        blocks_def = {
            "format_version": [1, 1, 0],
            "bedrock": {
                "sound": "stone",
                "textures": "bedrock"
            },
            "minecraft:bedrock": {
                "sound": "stone",
                "textures": "minecraft_bedrock"
            }
        }
        with open(os.path.join(target_rp_dir, "blocks.json"), "w", encoding="utf-8") as f:
            json.dump(blocks_def, f, indent=2)

        # 6. Copia sons
        sounds_src = os.path.join(source_rp_dir, "assets", "minecraft", "sounds")
        if os.path.isdir(sounds_src):
            sounds_dst = os.path.join(target_rp_dir, "sounds")
            shutil.copytree(sounds_src, sounds_dst, dirs_exist_ok=True)

        return {
            "header_uuid": rp_header_uuid,
            "module_uuid": rp_module_uuid,
            "textures_count": len(copied_textures),
            "has_variations": len(bedrock_variations) > 0
        }

