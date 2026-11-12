package com.blossomsmp.biomes;

import io.papermc.paper.registry.RegistryAccess;
import io.papermc.paper.registry.RegistryKey;
import org.bukkit.NamespacedKey;
import org.bukkit.Registry;
import org.bukkit.block.Biome;
import org.bukkit.generator.BiomeProvider;
import org.bukkit.generator.WorldInfo;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Gives every spot its vanilla biome, except where {@link Placement} says a Blossom biome goes.
 * Terrain shape never changes: only the biome (colours, plants, mobs, music) does.
 * Called from many world-generation threads at once, so nothing here changes after the world loads.
 */
public final class BlossomBiomeProvider extends BiomeProvider {

    private final BlossomBiomes plugin;
    private final Map<String, Placement> placements = new ConcurrentHashMap<>();
    private final Map<String, BiomeProvider> vanillaProviders = new ConcurrentHashMap<>();
    private volatile Map<CustomBiome, Biome> biomes;

    public BlossomBiomeProvider(BlossomBiomes plugin) {
        this.plugin = plugin;
    }

    /** Finds blossom:sakura_forest and the others. Null if the datapack isn't installed. */
    private Map<CustomBiome, Biome> resolve() {
        Registry<Biome> registry = RegistryAccess.registryAccess().getRegistry(RegistryKey.BIOME);
        Map<CustomBiome, Biome> found = new EnumMap<>(CustomBiome.class);
        for (CustomBiome custom : CustomBiome.values()) {
            Biome biome = registry.get(NamespacedKey.fromString(custom.key()));
            if (biome == null) {
                plugin.getLogger().severe("The biome " + custom.key() + " doesn't exist, so the Blossom biomes are OFF. "
                        + "Is the BlossomBiomes datapack in world/datapacks? See the guide.");
                return null;
            }
            found.put(custom, biome);
        }
        return found;
    }

    private Placement placement(WorldInfo world) {
        return placements.computeIfAbsent(world.getName(), name -> new Placement(world.getSeed(), plugin.placementSettings()));
    }

    public Placement placementFor(WorldInfo world) {
        return placement(world);
    }

    /** Minecraft's own biome picker for this world (made once, then reused). */
    private BiomeProvider vanilla(WorldInfo world) {
        return vanillaProviders.computeIfAbsent(world.getName(), name -> world.vanillaBiomeProvider());
    }

    public boolean active() {
        return biomes != null;
    }

    @Override
    public Biome getBiome(WorldInfo world, int x, int y, int z) {
        Biome vanilla = vanilla(world).getBiome(world, x, y, z);
        Map<CustomBiome, Biome> custom = biomes;
        if (custom == null) {
            return vanilla;
        }
        CustomBiome pick = placement(world).pick(x, z, vanilla.getKey().toString());
        return pick == null ? vanilla : custom.get(pick);
    }

    @Override
    public List<Biome> getBiomes(WorldInfo world) {
        List<Biome> list = new ArrayList<>(vanilla(world).getBiomes(world));
        Map<CustomBiome, Biome> custom = resolve();
        if (custom != null) {
            for (Biome biome : custom.values()) {
                if (!list.contains(biome)) {
                    list.add(biome);
                }
            }
            biomes = custom;
            plugin.getLogger().info("Blossom biomes are ON in world '" + world.getName() + "'.");
        }
        return list;
    }
}
