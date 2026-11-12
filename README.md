# ✿ BlossomBiomes

Six custom biomes for Blossom SMP (Paper 1.21.11, Java 21). Players don't need any mods: the biomes come from a **datapack**, and this **plugin** decides where they go.

| Biome | What it's like |
|---|---|
| ✿ **Sakura Forest** | Thick cherry blossom forest, pink petal carpets, petals drifting through the air |
| ❀ **Blossom Meadows** | Rolling hills of colourful flowers, lone cherry trees, horses |
| ☾ **Moonlight Garden** | Teal grass, azalea and pale oak trees, eyeblossoms that open at night, fireflies, glowing sparkles, soft chimes |
| ❦ **Emerald Grove** | Giant jungle trees, dense plants, parrots and pandas, **lots of emerald ore** |
| ❄ **Frosted Blossom Valley** | Cherry trees in the snow, frozen lakes, ice spikes, falling snowflakes |
| ✦ **Ancient Blossom Sanctuary** | **Super rare.** Golden haze, lavender sky, rare flowers, extra diamonds, a ruined shrine with treasure, and very dangerous mobs |

## Where they appear

- **0 – 5,000 blocks** from spawn: normal Minecraft only.
- **5,000 – 10,000 blocks**: Blossom areas start small and rare, and get more common.
- **Past 10,000 blocks**: about **40%** of the land is Blossom biomes, in big areas around 1,000 blocks wide.
- Cold land (snowy plains, taiga, slopes) becomes **Frosted Blossom Valley**.
- Oceans, rivers, beaches, mountain peaks and cave biomes always stay normal.
- **Ancient Blossom Sanctuary**: only past 10,000 blocks, about 320 blocks across. A 100,000 world border holds about **40–60** of them, and the closest one is usually **11,000–15,000 blocks** from spawn.

The **shape of the land never changes**: only the biome does (colours, trees, flowers, mobs, music). So Blossom biomes sit naturally on hills, plains and mountains.

Villages, mineshafts, ruined portals, trail ruins and strongholds can still appear in the Blossom biomes, and ores are the same as normal.

## The Ancient Blossom Sanctuary

- **Every monster that spawns there is an "Ancient" elite**: 2.5× health, 1.6× damage, faster, armoured, and they don't burn in the sun. They drop extra loot (emeralds, diamonds, golden apples, netherite scrap) and 15 Petals.
- In the middle there's a **ruined shrine** with a sealed chest on a quartz altar.
- **Opening the chest wakes 5 guardians** (lightning and a roar): Sanctuary Knights (netherite wither skeletons), Petal Archers (Power V bows), Blossom Revenants and the Ancient Warden. They have 80–160 health, don't burn, and give 150 Petals each.
- **The chest stays shut until every guardian is dead.** Then it fills with treasure, once, for whoever opens it, and the whole server is told.
- **Treasure** always includes an enchanted golden apple, 2 netherite ingots and an **Eternal Petal** collectible, plus 5 random picks from: Eternal Blossom Blade, Sakura Katana, Petal Bow, Emerald Blossom Pickaxe, Guardian's Shield, full Sanctuary netherite armour (Protection IV, Mending), Moonlight Crystal, elytra, totems, more god apples, netherite, diamond blocks, a trident. The claimer also gets **2,500 Petals**.
- Each shrine can only be claimed **once**. The chest can't be broken or blown up before that.

Everything about the mobs and the loot can be changed in `config.yml`.

---

## Setting it up (with your world reset)

You need two files:
- **`BlossomBiomes-datapack.zip`**: the biomes. Don't unzip it.
- **`BlossomBiomes.jar`**: the plugin. Build it on GitHub like your other plugins (see below).

⚠️ **Order matters.** The datapack and bukkit.yml must be ready **before** the new world is created. If the world is made first, the land near spawn will be normal and you'd have to reset again.

1. **Stop** the server. If you want to keep the old world, download a backup first.
2. In the File Manager, **delete** the folders `world`, `world_nether` and `world_the_end`. If `level-name` in `server.properties` isn't `world`, use that name instead.
3. **Make a new folder** called `world`, and inside it a folder called `datapacks`.
4. Upload **`BlossomBiomes-datapack.zip`** into `world/datapacks/`, still zipped.
5. Open **`bukkit.yml`** and add this at the very bottom. Use spaces, not tabs, and keep the indents exactly:
   ```yaml
   worlds:
     world:
       biome-provider: BlossomBiomes
   ```
   If `bukkit.yml` already has a `worlds:` section, add the `world:` part under it instead of making a second one.
6. Upload **`BlossomBiomes.jar`** into `plugins`.
7. **Start** the server. In the console you should see:
   - `Blossom biomes are ON in world 'world'.`
   - `Sanctuary shrines will be built in world 'world'.`

   If you see `The biome blossom:... doesn't exist`, the datapack is in the wrong place. **Stop, fix it, and reset again** before anyone builds.
8. **Set the world border** (in the console):
   ```
   worldborder center 0 0
   worldborder set 100000
   ```
   That's 50,000 blocks in every direction from spawn.
9. **Pre-generate with Chunky.** Generating all 100,000 blocks would take days and a huge amount of disk space, so pre-generate the busy middle and let the rest generate as people explore:
   ```
   chunky radius 12000
   chunky start
   ```
   That covers spawn, the 5k–10k ring where Blossom biomes start, and the first sanctuaries.

## Testing it

As an op:
- `/locate biome blossom:sakura_forest`, which works for any of the six names
- `/blossombiomes sanctuary` gives the coordinates of the nearest sanctuary, and `/tp` there
- `/biome` (everyone) shows which biome you're in. Walking into a Blossom biome also shows its name as a title.

## Commands

| Command | Who | What it does |
|---|---|---|
| `/biome` | Everyone | Shows which biome you're in |
| `/blossombiomes where` | Staff | Your biome and distance from spawn |
| `/blossombiomes sanctuary` | Staff | Coordinates of the nearest sanctuary |
| `/blossombiomes shrines` | Staff | How many shrines exist, and how many are sealed, awake or claimed |
| `/blossombiomes reload` | Staff | Reload mobs, loot and messages |

Staff can remove a broken shrine by **sneaking and breaking** its chest.

## Rules you must not break

- **Never remove the datapack** from `world/datapacks` after the world exists. Minecraft would lose track of the Blossom biomes in every chunk already made.
- **Don't change `placement:` or `sanctuary:` in config.yml** after the world is created. New land would no longer line up with old land. Mobs, loot, names and messages are safe to change any time.
- The Nether and the End are not affected.

## Good to know (the honest limits)

- **It hasn't run on a real server yet.** The biome files were built from Minecraft 1.21.11's own data, using its real feature lists, particle names, sounds and blocks. They were checked against the rule that crashes servers when a biome's feature order is wrong ("Feature order cycle found"), and every item, enchantment, mob and block name was checked against the official 1.21.11 lists. The placement maths was tested over millions of spots. The plugin code was compile-checked against stand-ins for the Paper classes. The first start is the real test: send me the console.
- **Changing the look of a biome** (colours, trees, mobs) means editing the datapack, and only affects **new** chunks.
- **Elite mobs only spawn in the dark** like normal monsters, so the sanctuary is safest at noon, and most dangerous at night and in caves.
- **Guardians are kept loaded with the chunk.** If everyone leaves, they wait there. The chest stays sealed until they're killed.

## For developers

- `datapack/` is the datapack, built by `tools/build_datapack.py` from Minecraft's own 1.21.11 data (misode/mcmeta, tag `1.21.11-data`). The script orders every biome's features by the same rule Minecraft's FeatureSorter uses and refuses to write the pack if vanilla plus custom biomes would form a cycle.
- `Placement` is plain maths with no Bukkit code, deterministic from the world seed and thread safe.
- `BlossomBiomeProvider` asks Minecraft's own biome picker (`WorldInfo#vanillaBiomeProvider`) first, then swaps in a Blossom biome where `Placement` says so. Terrain is unchanged.
- `ShrinePopulator` builds the shrine inside the sanctuary's centre chunk only.
