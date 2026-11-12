"""
Builds the Blossom SMP biome datapack for Minecraft Java 1.21.11 (data pack format 94.1).

Every biome is built from vanilla 1.21.11 worldgen pieces (read from misode/mcmeta) plus a few
blossom: features. Feature lists are ordered with the same rule Minecraft uses at startup
(FeatureSorter), and the script refuses to write the pack if the order could ever form a cycle,
because that crashes the server with "Feature order cycle found".
"""
import json, os, shutil, sys, zipfile
from collections import defaultdict

MC = sys.argv[1]            # .../mcmeta/data/minecraft
OUT = sys.argv[2]           # output folder for the datapack
W = MC + '/worldgen/'

def vjson(kind, name):
    return json.load(open(f'{W}{kind}/{name}.json'))

overworld = [v.split(':')[1] for v in json.load(open(MC + '/tags/worldgen/biome/is_overworld.json'))['values']]
vanilla = {b: vjson('biome', b) for b in overworld}

# ------------------------------------------------------------------ custom placed / configured features
placed, configured = {}, {}

def sapling_state(sapling):
    # azalea has no growth stage; real saplings do
    if sapling in ("minecraft:azalea", "minecraft:flowering_azalea"):
        return {"Name": sapling}
    return {"Name": sapling, "Properties": {"stage": "0"}}

def trees(name, feature, count, sapling):
    placed[name] = {"feature": feature, "placement": [
        {"type": "minecraft:count", "count": count},
        {"type": "minecraft:in_square"},
        {"type": "minecraft:surface_water_depth_filter", "max_water_depth": 0},
        {"type": "minecraft:heightmap", "heightmap": "OCEAN_FLOOR"},
        {"type": "minecraft:biome"},
        {"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:would_survive",
            "state": sapling_state(sapling)}}]}

def rare_trees(name, feature, chance, sapling):
    placed[name] = {"feature": feature, "placement": [
        {"type": "minecraft:rarity_filter", "chance": chance},
        {"type": "minecraft:in_square"},
        {"type": "minecraft:surface_water_depth_filter", "max_water_depth": 0},
        {"type": "minecraft:heightmap", "heightmap": "OCEAN_FLOOR"},
        {"type": "minecraft:biome"},
        {"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:would_survive",
            "state": sapling_state(sapling)}}]}

def patch(name, feature, count, heightmap="MOTION_BLOCKING"):
    placed[name] = {"feature": feature, "placement": [
        {"type": "minecraft:count", "count": count},
        {"type": "minecraft:in_square"},
        {"type": "minecraft:heightmap", "heightmap": heightmap},
        {"type": "minecraft:biome"}]}

def flower_patch(name, blocks, tries=64, spread=7):
    """A random patch of single-block flowers (same shape as vanilla's flower features)."""
    configured[name] = {"type": "minecraft:flower", "config": {
        "feature": {"feature": {"type": "minecraft:simple_block", "config": {"to_place": {
            "type": "minecraft:weighted_state_provider",
            "entries": [{"data": {"Name": b}, "weight": w} for b, w in blocks]}}},
            "placement": [{"type": "minecraft:block_predicate_filter",
                           "predicate": {"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}}]},
        "tries": tries, "xz_spread": spread, "y_spread": 2}}

# Sakura Forest
trees("sakura_trees", "minecraft:cherry_bees_005", 14, "minecraft:cherry_sapling")
patch("sakura_petal_carpets", "minecraft:flower_cherry", 4)
# Blossom Meadows
rare_trees("meadow_lone_cherries", "minecraft:cherry_bees_005", 5, "minecraft:cherry_sapling")
flower_patch("meadow_flowers", [("minecraft:allium", 2), ("minecraft:azure_bluet", 3), ("minecraft:oxeye_daisy", 3),
                                ("minecraft:cornflower", 3), ("minecraft:pink_tulip", 3), ("minecraft:white_tulip", 2),
                                ("minecraft:lily_of_the_valley", 1), ("minecraft:poppy", 2)])
patch("meadow_flowers", "blossom:meadow_flowers", 3)
# Moonlight Garden
trees("moonlight_azaleas", "minecraft:azalea_tree", 3, "minecraft:azalea")
trees("moonlight_pale_oaks", "minecraft:pale_oak", 1, "minecraft:pale_oak_sapling")
patch("moonlight_eyeblossoms", "minecraft:flower_pale_garden", 8)
patch("moonlight_fireflies", "minecraft:patch_firefly_bush", 2, "MOTION_BLOCKING_NO_LEAVES")
flower_patch("moonlight_flowers", [("minecraft:lily_of_the_valley", 4), ("minecraft:azure_bluet", 3),
                                   ("minecraft:white_tulip", 2), ("minecraft:cornflower", 2), ("minecraft:torchflower", 1)])
patch("moonlight_flowers", "blossom:moonlight_flowers", 2)
# Emerald Grove
trees("emerald_giant_trees", "minecraft:mega_jungle_tree", 4, "minecraft:jungle_sapling")
placed["emerald_ore_rich"] = {"feature": "minecraft:ore_emerald", "placement": [
    {"type": "minecraft:count", "count": 40}, {"type": "minecraft:in_square"},
    {"type": "minecraft:height_range", "height": {"type": "minecraft:trapezoid",
        "max_inclusive": {"absolute": 160}, "min_inclusive": {"absolute": -16}}},
    {"type": "minecraft:biome"}]}
# Frosted Blossom Valley
trees("frosted_cherries", "minecraft:cherry_bees_005", 7, "minecraft:cherry_sapling")
trees("frosted_spruces", "minecraft:spruce", 2, "minecraft:spruce_sapling")
placed["frosted_ice_spikes"] = {"feature": "minecraft:ice_spike", "placement": [
    {"type": "minecraft:rarity_filter", "chance": 24}, {"type": "minecraft:in_square"},
    {"type": "minecraft:heightmap", "heightmap": "MOTION_BLOCKING"}, {"type": "minecraft:biome"}]}
# Ancient Blossom Sanctuary
trees("sanctuary_ancient_cherries", "minecraft:cherry_bees_005", 5, "minecraft:cherry_sapling")
rare_trees("sanctuary_great_oaks", "minecraft:fancy_oak_bees", 2, "minecraft:oak_sapling")
flower_patch("sanctuary_rare_flowers", [("minecraft:torchflower", 4), ("minecraft:lily_of_the_valley", 3),
                                        ("minecraft:allium", 2), ("minecraft:blue_orchid", 2), ("minecraft:white_tulip", 1)],
             tries=48, spread=5)
patch("sanctuary_rare_flowers", "blossom:sanctuary_rare_flowers", 2)
placed["sanctuary_diamonds"] = {"feature": "minecraft:ore_diamond_large", "placement": [
    {"type": "minecraft:count", "count": 3}, {"type": "minecraft:in_square"},
    {"type": "minecraft:height_range", "height": {"type": "minecraft:trapezoid",
        "max_inclusive": {"above_bottom": 80}, "min_inclusive": {"above_bottom": -80}}},
    {"type": "minecraft:biome"}]}

# where each custom placed feature goes (step index, Minecraft's GenerationStep.Decoration)
STEP_OF = {k: 9 for k in placed}
STEP_OF["emerald_ore_rich"] = 6
STEP_OF["sanctuary_diamonds"] = 6

# ------------------------------------------------------------------ biome designs
def base_steps(biome, keep_veg=False):
    steps = [list(s) for s in vanilla[biome]['features']]
    if not keep_veg:
        steps[9] = []
    return steps

def spawners(monsters, creatures, ambient=True):
    def e(t, w, lo, hi):
        return {"type": "minecraft:" + t, "maxCount": hi, "minCount": lo, "weight": w}
    return {
        "ambient": [e("bat", 10, 8, 8)] if ambient else [],
        "axolotls": [], "misc": [],
        "creature": [e(*c) for c in creatures],
        "monster": [e(*m) for m in monsters],
        "underground_water_creature": [e("glow_squid", 10, 4, 6)],
        "water_ambient": [], "water_creature": []}

NORMAL_MONSTERS = [("spider", 100, 4, 4), ("zombie", 95, 4, 4), ("zombie_villager", 5, 1, 1),
                   ("skeleton", 100, 4, 4), ("creeper", 100, 4, 4), ("slime", 100, 4, 4),
                   ("enderman", 10, 1, 4), ("witch", 5, 1, 1)]
FARM = [("sheep", 12, 4, 4), ("pig", 10, 4, 4), ("chicken", 10, 4, 4), ("cow", 8, 4, 4), ("rabbit", 4, 2, 3)]

def music(sound):
    return {"default": {"max_delay": 24000, "min_delay": 12000, "sound": "minecraft:" + sound}}

def chimes(chance):
    # "mood" is copied from the vanilla overworld (cave sounds), so these biomes keep them
    return {"additions": {"sound": "minecraft:block.amethyst_block.chime", "tick_chance": chance},
            "mood": {"block_search_extent": 8, "offset": 2.0, "sound": "minecraft:ambient.cave", "tick_delay": 6000}}

BIOMES = {
    "sakura_forest": dict(
        base="cherry_grove", temperature=0.5, downfall=0.8, precip=True,
        veg=["minecraft:glow_lichen", "minecraft:patch_tall_grass_2", "minecraft:patch_grass_plain",
             "minecraft:flower_cherry", "blossom:sakura_trees", "blossom:sakura_petal_carpets",
             "minecraft:patch_firefly_bush_near_water"],
        effects={"grass_color": "#a8d36f", "foliage_color": "#b6db61", "water_color": "#6cc2e6"},
        attributes={"minecraft:audio/background_music": music("music.overworld.cherry_grove"),
                    "minecraft:visual/sky_color": "#8ab0ff", "minecraft:visual/fog_color": "#e9dbe4",
                    "minecraft:visual/water_fog_color": "#5db7ef",
                    "minecraft:visual/ambient_particles": [{"particle": {"type": "minecraft:cherry_leaves"}, "probability": 0.004}]},
        spawners=spawners(NORMAL_MONSTERS, [("rabbit", 4, 2, 3), ("sheep", 8, 2, 4), ("pig", 6, 1, 2), ("fox", 2, 2, 3)])),

    "blossom_meadows": dict(
        base="meadow", temperature=0.6, downfall=0.7, precip=True,
        veg=["minecraft:glow_lichen", "minecraft:patch_tall_grass_2", "minecraft:patch_grass_meadow",
             "minecraft:flower_meadow", "minecraft:trees_meadow", "minecraft:wildflowers_meadow",
             "blossom:meadow_lone_cherries", "blossom:meadow_flowers", "minecraft:patch_firefly_bush_near_water"],
        effects={"grass_color": "#8fd46c", "foliage_color": "#7cc65b", "water_color": "#3fa0e6"},
        attributes={"minecraft:audio/background_music": music("music.overworld.meadow"),
                    "minecraft:visual/sky_color": "#82adff", "minecraft:visual/water_fog_color": "#2f7fd0",
                    "minecraft:visual/ambient_particles": [{"particle": {"type": "minecraft:cherry_leaves"}, "probability": 0.0006}]},
        spawners=spawners(NORMAL_MONSTERS, FARM + [("horse", 2, 2, 4), ("donkey", 1, 1, 2)])),

    "moonlight_garden": dict(
        base="plains", temperature=0.6, downfall=0.6, precip=True,
        veg=["minecraft:glow_lichen", "blossom:moonlight_azaleas", "blossom:moonlight_pale_oaks",
             "blossom:moonlight_eyeblossoms", "blossom:moonlight_flowers", "blossom:moonlight_fireflies",
             "minecraft:patch_grass_forest", "minecraft:patch_waterlily"],
        effects={"grass_color": "#5e9c90", "foliage_color": "#4f8b98", "water_color": "#3a5fd0"},
        attributes={"minecraft:audio/background_music": music("music.overworld.lush_caves"),
                    "minecraft:visual/sky_color": "#5f73d9", "minecraft:visual/fog_color": "#a4acdf",
                    "minecraft:visual/water_fog_color": "#1d2f73",
                    "minecraft:visual/ambient_particles": [{"particle": {"type": "minecraft:glow"}, "probability": 0.0025},
                                                           {"particle": {"type": "minecraft:firefly"}, "probability": 0.002}],
                    "minecraft:audio/ambient_sounds": chimes(0.003)},
        spawners=spawners(NORMAL_MONSTERS + [("phantom", 0, 1, 1)][:0], [("rabbit", 4, 2, 3), ("fox", 3, 1, 2)])),

    "emerald_grove": dict(
        base="jungle", temperature=0.8, downfall=0.9, precip=True,
        veg=["minecraft:glow_lichen", "minecraft:bamboo_light", "minecraft:trees_jungle",
             "blossom:emerald_giant_trees", "minecraft:flower_warm", "minecraft:patch_grass_jungle",
             "minecraft:patch_firefly_bush_near_water", "minecraft:vines", "minecraft:patch_melon"],
        effects={"grass_color": "#3fbf62", "foliage_color": "#2fae52", "water_color": "#2fbfa0"},
        attributes={"minecraft:audio/background_music": music("music.overworld.jungle"),
                    "minecraft:visual/sky_color": "#77b6ff", "minecraft:visual/fog_color": "#c4e8d2",
                    "minecraft:visual/water_fog_color": "#1a7f6a",
                    "minecraft:visual/ambient_particles": [{"particle": {"type": "minecraft:happy_villager"}, "probability": 0.0012}],
                    "minecraft:gameplay/increased_fire_burnout": True},
        extra={6: ["blossom:emerald_ore_rich"]},
        spawners=spawners(NORMAL_MONSTERS, [("parrot", 40, 1, 2), ("panda", 1, 1, 2), ("ocelot", 2, 1, 3), ("chicken", 10, 4, 4)])),

    "frosted_blossom_valley": dict(
        base="grove", temperature=-0.3, downfall=0.5, precip=True,
        veg=["minecraft:glow_lichen", "blossom:frosted_cherries", "blossom:frosted_spruces",
             "blossom:frosted_ice_spikes", "minecraft:patch_berry_rare", "minecraft:patch_pumpkin"],
        effects={"grass_color": "#9cc8b0", "foliage_color": "#b4d4c6", "water_color": "#7ab6e6"},
        attributes={"minecraft:audio/background_music": music("music.overworld.grove"),
                    "minecraft:visual/sky_color": "#a7c4ff", "minecraft:visual/fog_color": "#e2eaff",
                    "minecraft:visual/water_fog_color": "#4a78b8",
                    "minecraft:visual/ambient_particles": [{"particle": {"type": "minecraft:snowflake"}, "probability": 0.008}]},
        spawners=spawners([("spider", 100, 4, 4), ("zombie", 95, 4, 4), ("skeleton", 20, 4, 4), ("stray", 80, 4, 4),
                           ("creeper", 100, 4, 4), ("slime", 100, 4, 4), ("enderman", 10, 1, 4), ("witch", 5, 1, 1)],
                          [("rabbit", 4, 2, 3), ("fox", 8, 2, 4), ("goat", 2, 1, 3), ("polar_bear", 1, 1, 2)])),

    "ancient_blossom_sanctuary": dict(
        base="cherry_grove", temperature=0.6, downfall=0.4, precip=False,
        veg=["minecraft:glow_lichen", "minecraft:patch_grass_plain", "minecraft:flower_cherry",
             "blossom:sanctuary_ancient_cherries", "blossom:sanctuary_great_oaks", "blossom:sanctuary_rare_flowers"],
        effects={"grass_color": "#c9d58c", "foliage_color": "#d9b86a", "water_color": "#9fd6ff"},
        attributes={"minecraft:audio/background_music": music("music.overworld.deep_dark"),
                    "minecraft:visual/sky_color": "#b7a5ff", "minecraft:visual/fog_color": "#f1d7b4",
                    "minecraft:visual/water_fog_color": "#4b7bd6",
                    "minecraft:visual/ambient_particles": [{"particle": {"type": "minecraft:end_rod"}, "probability": 0.0015},
                                                           {"particle": {"type": "minecraft:enchant"}, "probability": 0.006}],
                    "minecraft:audio/ambient_sounds": chimes(0.006)},
        extra={6: ["blossom:sanctuary_diamonds"]},
        spawners=spawners([("zombie", 80, 2, 4), ("skeleton", 100, 2, 4), ("wither_skeleton", 30, 1, 2),
                           ("husk", 40, 2, 3), ("stray", 40, 2, 3), ("witch", 10, 1, 1), ("spider", 40, 2, 3)],
                          [], ambient=False)),
}

# ------------------------------------------------------------------ feature order (Minecraft's FeatureSorter rule)
def flat(features):
    return [(step, f) for step, lst in enumerate(features) for f in lst]

def graph_of(biome_lists):
    edges = defaultdict(set)
    nodes = set()
    for lst in biome_lists:
        fl = flat(lst)
        nodes.update(fl)
        for a, b in zip(fl, fl[1:]):
            edges[a].add(b)
    return nodes, edges

def has_cycle(nodes, edges):
    WHITE, GREY, BLACK = 0, 1, 2
    color = {n: WHITE for n in nodes}
    sys.setrecursionlimit(100000)
    def dfs(n):
        color[n] = GREY
        for m in edges.get(n, ()):
            if color[m] == GREY:
                return (n, m)
            if color[m] == WHITE:
                r = dfs(m)
                if r:
                    return r
        color[n] = BLACK
        return None
    for n in nodes:
        if color[n] == WHITE:
            r = dfs(n)
            if r:
                return r
    return None

vanilla_lists = [vanilla[b]['features'] for b in overworld]
vnodes, vedges = graph_of(vanilla_lists)
assert has_cycle(vnodes, vedges) is None, "vanilla itself has a cycle?"

# topological order of vanilla (Kahn), ties broken by step then name -> stable global rank
indeg = defaultdict(int)
for a in vedges:
    for b in vedges[a]:
        indeg[b] += 1
import heapq
heap = [(n[0], n[1]) for n in vnodes if indeg[n] == 0]
heapq.heapify(heap)
rank = {}
while heap:
    n = heapq.heappop(heap)
    rank[n] = len(rank)
    for m in vedges.get(n, ()):
        indeg[m] -= 1
        if indeg[m] == 0:
            heapq.heappush(heap, m)
assert len(rank) == len(vnodes)

def order(steps):
    """Sort each step by the vanilla rank; blossom features go after all vanilla ones in their step."""
    out = []
    for step, lst in enumerate(steps):
        seen = []
        for f in lst:
            if f not in seen:
                seen.append(f)
        def key(f):
            if (step, f) in rank:
                return (0, rank[(step, f)])
            if f.startswith('blossom:'):
                return (1, sorted(placed).index(f.split(':')[1]))
            raise SystemExit(f'{f} is not a vanilla feature in step {step}')
        out.append(sorted(seen, key=key))
    return out

# ------------------------------------------------------------------ write the pack
if os.path.exists(OUT):
    shutil.rmtree(OUT)
def write(rel, obj):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(obj, fh, indent=2)
        fh.write('\n')

write('pack.mcmeta', {"pack": {"description": "Blossom SMP custom biomes (Minecraft 1.21.11)",
                               "min_format": [94, 1], "max_format": 94}})

my_lists = {}
for name, d in BIOMES.items():
    steps = base_steps(d['base'])
    steps[9] = list(d['veg'])
    for step, extra in d.get('extra', {}).items():
        steps[step] = steps[step] + extra
    for step, lst in enumerate(steps):
        for f in lst:
            if f.startswith('blossom:'):
                fid = f.split(':')[1]
                assert fid in placed, f'{name}: unknown {f}'
                assert STEP_OF[fid] == step, f'{name}: {f} in step {step}, expected {STEP_OF[fid]}'
            else:
                assert (step, f) in vnodes, f'{name}: {f} is not vanilla in step {step}'
    steps = order(steps)
    my_lists[name] = steps
    biome = {
        "attributes": d['attributes'],
        "carvers": vanilla[d['base']]['carvers'],
        "downfall": d['downfall'],
        "effects": d['effects'],
        "features": steps,
        "has_precipitation": d['precip'],
        "spawn_costs": {},
        "spawners": d['spawners'],
        "temperature": d['temperature'],
    }
    write(f'data/blossom/worldgen/biome/{name}.json', biome)

# the real check: vanilla + all custom biomes together must have no cycle
nodes, edges = graph_of(vanilla_lists + list(my_lists.values()))
cyc = has_cycle(nodes, edges)
if cyc:
    raise SystemExit(f'FEATURE ORDER CYCLE near {cyc}')

for k, v in placed.items():
    write(f'data/blossom/worldgen/placed_feature/{k}.json', v)
for k, v in configured.items():
    write(f'data/blossom/worldgen/configured_feature/{k}.json', v)

# every placed feature must point at a configured feature that exists
for k, v in placed.items():
    ns, cf = v['feature'].split(':')
    if ns == 'minecraft':
        assert os.path.exists(f'{W}configured_feature/{cf}.json'), f'{k}: no vanilla {cf}'
    else:
        assert cf in configured, f'{k}: no blossom {cf}'

# biome tags: let vanilla structures use the new biomes, and count them as overworld
normal = ["sakura_forest", "blossom_meadows", "moonlight_garden", "emerald_grove", "frosted_blossom_valley"]
def tag(rel, names):
    path = f'{MC}/tags/worldgen/biome/{rel}.json'
    assert os.path.exists(path), f'no vanilla tag {rel}'
    write(f'data/minecraft/tags/worldgen/biome/{rel}.json', {"replace": False, "values": ["blossom:" + n for n in names]})
tag('is_overworld', list(BIOMES))
tag('has_structure/mineshaft', normal)
tag('has_structure/ruined_portal_standard', normal)
tag('has_structure/stronghold', list(BIOMES))
tag('stronghold_biased_to', normal)
tag('has_structure/village_plains', ["sakura_forest", "blossom_meadows"])
tag('has_structure/village_snowy', ["frosted_blossom_valley"])
tag('has_structure/pillager_outpost', ["blossom_meadows"])
tag('has_structure/trail_ruins', ["sakura_forest", "emerald_grove"])
tag('has_structure/jungle_temple', ["emerald_grove"])
tag('has_structure/igloo', ["frosted_blossom_valley"])
tag('has_structure/trial_chambers', list(BIOMES))
tag('is_forest', ["sakura_forest", "emerald_grove", "moonlight_garden"])
tag('is_jungle', ["emerald_grove"])
tag('spawns_snow_foxes', ["frosted_blossom_valley"])
tag('spawns_white_rabbits', ["frosted_blossom_valley"])
tag('spawns_cold_variant_farm_animals', ["frosted_blossom_valley"])

print('datapack written:', OUT)
for n, s in my_lists.items():
    print(f'  {n:27} features per step: {[len(x) for x in s]}')
print(f'  {len(placed)} placed + {len(configured)} configured features; vanilla+custom feature order has no cycle')
