package com.blossomsmp.biomes;

import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.World;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.event.inventory.InventoryDragEvent;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.InventoryHolder;
import org.bukkit.inventory.ItemStack;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * /biomes : the six Blossom biomes with what they're like and where to find them.
 * Staff (blossombiomes.teleport) can click one to go to the nearest of that biome.
 */
public final class BiomesMenu implements Listener {

    private static final int[] SLOTS = {10, 11, 12, 14, 15, 16};
    private static final int INFO = 13;
    private static final int CLOSE = 22;
    private static final Map<CustomBiome, Material> FALLBACK = Map.of(
            CustomBiome.SAKURA_FOREST, Material.CHERRY_SAPLING,
            CustomBiome.BLOSSOM_MEADOWS, Material.ALLIUM,
            CustomBiome.MOONLIGHT_GARDEN, Material.AMETHYST_SHARD,
            CustomBiome.EMERALD_GROVE, Material.EMERALD,
            CustomBiome.FROSTED_BLOSSOM_VALLEY, Material.SNOWBALL,
            CustomBiome.ANCIENT_BLOSSOM_SANCTUARY, Material.NETHER_STAR);

    /** Marks our inventory. */
    private static final class Holder implements InventoryHolder {
        private Inventory inventory;

        @Override
        public Inventory getInventory() {
            return inventory;
        }
    }

    private final BlossomBiomes plugin;

    public BiomesMenu(BlossomBiomes plugin) {
        this.plugin = plugin;
    }

    public void open(Player player) {
        Holder holder = new Holder();
        Inventory inv = Bukkit.createInventory(holder, 27, Text.c(plugin.raw("menu-title")));
        holder.inventory = inv;
        ItemStack border = Items.icon(Material.PINK_STAINED_GLASS_PANE, " ", List.of(), false);
        ItemStack filler = Items.icon(Material.GRAY_STAINED_GLASS_PANE, " ", List.of(), false);
        for (int i = 0; i < 27; i++) {
            inv.setItem(i, i < 9 || i >= 18 ? border : filler);
        }
        boolean canTeleport = player.hasPermission("blossombiomes.teleport");
        CustomBiome[] biomes = CustomBiome.values();
        for (int i = 0; i < biomes.length; i++) {
            CustomBiome biome = biomes[i];
            List<String> lore = new ArrayList<>(plugin.getConfig().getStringList("biome-info." + biome.id));
            lore.add("");
            lore.add(canTeleport ? plugin.raw("menu-click-teleport") : plugin.raw("menu-explore"));
            ItemStack icon = Items.icon(FALLBACK.get(biome), plugin.displayName(biome), lore,
                    biome == CustomBiome.ANCIENT_BLOSSOM_SANCTUARY);
            inv.setItem(SLOTS[i], Items.model(icon, "blossom:icon_biome_" + biome.id));
        }
        inv.setItem(INFO, Items.icon(Material.MAP, plugin.raw("menu-info-name"), plugin.getConfig()
                .getStringList("messages.menu-info"), false));
        inv.setItem(CLOSE, Items.model(Items.icon(Material.BARRIER, plugin.raw("menu-close"), List.of(), false),
                "blossom:icon_close"));
        player.openInventory(inv);
    }

    @EventHandler(priority = EventPriority.HIGH)
    public void onClick(InventoryClickEvent event) {
        if (!(event.getInventory().getHolder() instanceof Holder) || !(event.getWhoClicked() instanceof Player player)) {
            return;
        }
        event.setCancelled(true);
        int slot = event.getRawSlot();
        if (slot == CLOSE) {
            Bukkit.getScheduler().runTask(plugin, () -> player.closeInventory());
            return;
        }
        for (int i = 0; i < SLOTS.length; i++) {
            if (SLOTS[i] == slot) {
                if (!player.hasPermission("blossombiomes.teleport")) {
                    plugin.send(player, "menu-no-teleport");
                    return;
                }
                CustomBiome biome = CustomBiome.values()[i];
                Bukkit.getScheduler().runTask(plugin, () -> player.closeInventory());
                teleport(player, biome);
                return;
            }
        }
    }

    @EventHandler(priority = EventPriority.HIGH)
    public void onDrag(InventoryDragEvent event) {
        if (event.getInventory().getHolder() instanceof Holder) {
            event.setCancelled(true);
        }
    }

    /** Finds the nearest spot of a biome in the background, then teleports there safely. */
    public void teleport(Player player, CustomBiome biome) {
        World world = player.getWorld();
        BlossomBiomeProvider provider = plugin.provider(world.getName());
        if (provider == null || !provider.active()) {
            plugin.send(player, "not-blossom-world");
            return;
        }
        plugin.send(player, "searching", "{biome}", plugin.displayName(biome));
        int fromX = player.getLocation().getBlockX();
        int fromZ = player.getLocation().getBlockZ();
        int maxRadius = plugin.getConfig().getInt("teleport-search-radius", 30000);
        Bukkit.getScheduler().runTaskAsynchronously(plugin, () -> {
            int[] found = biome == CustomBiome.ANCIENT_BLOSSOM_SANCTUARY
                    ? sanctuary(provider, world, fromX, fromZ)
                    : search(provider, world, biome, fromX, fromZ, maxRadius);
            Bukkit.getScheduler().runTask(plugin, () -> {
                if (!player.isOnline()) {
                    return;
                }
                if (found == null) {
                    plugin.send(player, "not-found", "{biome}", plugin.displayName(biome),
                            "{radius}", Text.number(maxRadius));
                    return;
                }
                world.getChunkAtAsync(found[0] >> 4, found[1] >> 4).thenAccept(chunk ->
                        Bukkit.getScheduler().runTask(plugin, () -> {
                            int y = world.getHighestBlockYAt(found[0], found[1]) + 1;
                            player.teleportAsync(new Location(world, found[0] + 0.5, y, found[1] + 0.5,
                                    player.getLocation().getYaw(), 0f));
                            plugin.send(player, "teleported", "{biome}", plugin.displayName(biome),
                                    "{x}", String.valueOf(found[0]), "{z}", String.valueOf(found[1]));
                        }));
            });
        });
    }

    private static int[] sanctuary(BlossomBiomeProvider provider, World world, int x, int z) {
        Placement.Sanctuary s = provider.placementFor(world).nearestSanctuary(x, z, 12);
        return s == null ? null : new int[]{s.x(), s.z() + 12}; // just outside the shrine
    }

    /** Ring by ring outwards, every 64 blocks, until the biome shows up on land. */
    private static int[] search(BlossomBiomeProvider provider, World world, CustomBiome biome, int x, int z, int max) {
        int step = 64;
        for (int r = 0; r <= max; r += step) {
            for (int dx = -r; dx <= r; dx += step) {
                for (int dz = -r; dz <= r; dz += step) {
                    if (Math.max(Math.abs(dx), Math.abs(dz)) != r) {
                        continue;
                    }
                    if (provider.surfaceBiome(world, x + dx, z + dz) == biome) {
                        // step a little further in, so you don't land right on the edge
                        int sx = x + dx + Integer.signum(dx) * 48;
                        int sz = z + dz + Integer.signum(dz) * 48;
                        return provider.surfaceBiome(world, sx, sz) == biome ? new int[]{sx, sz}
                                : new int[]{x + dx, z + dz};
                    }
                }
            }
        }
        return null;
    }
}
