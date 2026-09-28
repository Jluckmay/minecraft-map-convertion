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
                    try:
                        with open(src_f, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        desc = data.get("minecraft:client_entity", {}).get("description", {})
                        if desc:
                            desc["materials"] = {
                                "default": "villager_v2",
                                "masked": "villager_v2_masked"
                            }
                            desc["render_controllers"] = [
                                "controller.render.npc_villager_base",
                                "controller.render.npc_villager_masked"
                            ]
                            if "textures" in desc:
                                if "default" in desc["textures"] and "base" not in desc["textures"]:
                                    desc["textures"]["base"] = desc["textures"]["default"]
                                if desc["textures"].get("profession") == "textures/entity/villager2/professions/mason":
                                    desc["textures"]["profession"] = "textures/entity/villager2/professions/stonemason"
                            if "animations" not in desc:
                                desc["animations"] = {
                                    "general": "animation.villager.general",
                                    "look_at_target": "animation.common.look_at_target",
                                    "move": "animation.villager.move",
                                    "raise_arms": "animation.villager.raise_arms"
                                }
                            if "animation_controllers" not in desc:
                                desc["animation_controllers"] = [
                                    {"general": "controller.animation.villager_v2.general"},
                                    {"move": "controller.animation.villager_v2.move"},
                                    {"raise_arms": "controller.animation.villager_v2.raise_arms"}
                                ]
                        with open(dst_f, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2)
                    except Exception:
                        shutil.copyfile(src_f, dst_f)

                    # Cria aliases úteis para caracteres especiais como ø/o
                    if ef == "npc_j_rn.entity.json":
                        try:
                            with open(src_f, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            desc = data.get("minecraft:client_entity", {}).get("description", {})
                            if desc:
                                desc["identifier"] = f"{safe_name}:npc_jorn"
                                desc["materials"] = {
                                    "default": "villager_v2",
                                    "masked": "villager_v2_masked"
                                }
                                desc["render_controllers"] = [
                                    "controller.render.npc_villager_base",
                                    "controller.render.npc_villager_masked"
                                ]
                            with open(os.path.join(target_ent_dir, "npc_jorn.entity.json"), "w", encoding="utf-8") as f:
                                json.dump(data, f, indent=2)
                        except Exception:
                            pass

        # 7. Render Controllers para NPCs Villagers (evita que fiquem invisíveis no Bedrock)
        rc_dir = os.path.join(target_rp_dir, "render_controllers")
        os.makedirs(rc_dir, exist_ok=True)
        rc_data = {
            "format_version": "1.8.0",
            "render_controllers": {
                "controller.render.npc_villager_base": {
                    "geometry": "Geometry.default",
                    "materials": [
                        {"*": "Material.default"}
                    ],
                    "textures": [
                        "Texture.default"
                    ]
                },
                "controller.render.npc_villager_masked": {
                    "geometry": "Geometry.default",
                    "materials": [
                        {"*": "Material.masked"}
                    ],
                    "textures": [
                        "Texture.biome",
                        "Texture.profession"
                    ]
                },
                "controller.render.villager_v2": {
                    "geometry": "Geometry.default",
                    "materials": [
                        {"*": "Material.default"}
                    ],
                    "textures": [
                        "Texture.default"
                    ]
                }
            }
        }
        with open(os.path.join(rc_dir, "npc_villager.render_controllers.json"), "w", encoding="utf-8") as f:
            json.dump(rc_data, f, indent=2)

        # 8. Definições de névoa customizada do Nether para The End (fogs/ e biomas do cliente)
        fogs_dir = os.path.join(target_rp_dir, "fogs")
        os.makedirs(fogs_dir, exist_ok=True)

        def make_fog_def(identifier: str, fog_color: str = "#8c1414", fog_start: float = 6.0, fog_end: float = 42.0):
            return {
                "format_version": "1.16.100",
                "minecraft:fog_settings": {
                    "description": {
                        "identifier": identifier
                    },
                    "distance": {
                        "air": {
                            "fog_start": fog_start,
                            "fog_end": fog_end,
                            "fog_color": fog_color,
                            "render_distance_type": "fixed"
                        },
                        "weather": {
                            "fog_start": fog_start,
                            "fog_end": fog_end,
                            "fog_color": fog_color,
                            "render_distance_type": "fixed"
                        }
                    },
                    "volumetric": {
                        "density": {
                            "air": {
                                "max_density": 0.35,
                                "uniform": True
                            }
                        },
                        "media_coefficients": {
                            "air": {
                                "scattering": [0.35, 0.08, 0.08],
                                "absorption": [0.1, 0.1, 0.1]
                            }
                        }
                    }
                }
            }

        fog_configs = {
            "nether_fog.json": (f"{safe_name}:nether_fog", "#8c1414", 6.0, 42.0),
            "nether_fog_simple.json": ("nether_fog", "#8c1414", 6.0, 42.0),
            "nether_fog_custom.json": ("custom:nether_fog", "#8c1414", 6.0, 42.0),
            "fog_the_end.json": ("minecraft:fog_the_end", "#8c1414", 6.0, 42.0),
            "fog_hell.json": (f"{safe_name}:fog_hell", "#8c1414", 6.0, 42.0),
            "fog_hell_vanilla.json": ("minecraft:fog_hell", "#8c1414", 6.0, 42.0),
            "fog_basalt_deltas.json": (f"{safe_name}:fog_basalt_deltas", "#685959", 2.0, 28.0),
            "fog_basalt_deltas_vanilla.json": ("minecraft:fog_basalt_deltas", "#685959", 2.0, 28.0),
            "fog_crimson_forest.json": (f"{safe_name}:fog_crimson_forest", "#8c1414", 6.0, 42.0),
            "fog_crimson_forest_vanilla.json": ("minecraft:fog_crimson_forest", "#8c1414", 6.0, 42.0),
            "fog_warped_forest.json": (f"{safe_name}:fog_warped_forest", "#163b40", 8.0, 46.0),
            "fog_warped_forest_vanilla.json": ("minecraft:fog_warped_forest", "#163b40", 8.0, 46.0),
            "fog_soulsand_valley.json": (f"{safe_name}:fog_soulsand_valley", "#1b2632", 4.0, 32.0),
            "fog_soulsand_valley_vanilla.json": ("minecraft:fog_soulsand_valley", "#1b2632", 4.0, 32.0),
        }
        for fname, (ident, color, f_start, f_end) in fog_configs.items():
            with open(os.path.join(fogs_dir, fname), "w", encoding="utf-8") as f:
                json.dump(make_fog_def(ident, color, f_start, f_end), f, indent=2)

        biomes_dir = os.path.join(target_rp_dir, "biomes")
        os.makedirs(biomes_dir, exist_ok=True)
        all_nether_end_biomes = [
            # The End biomes
            "the_end", "end_highlands", "end_midlands", "end_barrens", "small_end_islands",
            # Nether biomes
            "basalt_deltas", "nether_wastes", "crimson_forest", "warped_forest", "soulsand_valley", "hell"
        ]
        biomes_dict = {}
        for b_name in all_nether_end_biomes:
            # Bare identifier
            cb_data = {
                "format_version": "1.21.40",
                "minecraft:client_biome": {
                    "description": {
                        "identifier": b_name
                    },
                    "components": {
                        "minecraft:fog_appearance": {
                            "fog_identifier": f"{safe_name}:nether_fog"
                        },
                        "minecraft:sky_color": {
                            "sky_color": "#380808"
                        }
                    }
                }
            }
            with open(os.path.join(biomes_dir, f"{b_name}.client_biome.json"), "w", encoding="utf-8") as f:
                json.dump(cb_data, f, indent=2)

            # Namespaced identifier
            cb_data_ns = {
                "format_version": "1.21.40",
                "minecraft:client_biome": {
                    "description": {
                        "identifier": f"minecraft:{b_name}"
                    },
                    "components": {
                        "minecraft:fog_appearance": {
                            "fog_identifier": f"{safe_name}:nether_fog"
                        },
                        "minecraft:sky_color": {
                            "sky_color": "#380808"
                        }
                    }
                }
            }
            with open(os.path.join(biomes_dir, f"minecraft_{b_name}.client_biome.json"), "w", encoding="utf-8") as f:
                json.dump(cb_data_ns, f, indent=2)

            biomes_dict[b_name] = {
                "fog_identifier": f"{safe_name}:nether_fog",
                "water_surface_color": "#701414",
                "inherit_from_prior_fog": False
            }
            biomes_dict[f"minecraft:{b_name}"] = {
                "fog_identifier": f"{safe_name}:nether_fog",
                "water_surface_color": "#701414",
                "inherit_from_prior_fog": False
            }

        biomes_client_legacy = {"biomes": biomes_dict}
        with open(os.path.join(target_rp_dir, "biomes_client.json"), "w", encoding="utf-8") as f:
            json.dump(biomes_client_legacy, f, indent=2)

        return {
            "header_uuid": rp_header_uuid,
            "module_uuid": rp_module_uuid,
            "textures_count": len(copied_textures),
            "has_variations": len(bedrock_vars) > 0
        }

