package com.blossomsmp.biomes;

import net.kyori.adventure.title.Title;
import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.World;
import org.bukkit.block.Biome;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.command.PluginCommand;
import org.bukkit.command.TabExecutor;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.event.world.WorldInitEvent;
import org.bukkit.generator.BiomeProvider;
import org.bukkit.plugin.java.JavaPlugin;

import java.time.Duration;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * BlossomBiomes: places the six Blossom SMP biomes (from the BlossomBiomes datapack) in the world,
 * builds sanctuary shrines, and makes the Ancient Blossom Sanctuary dangerous and rewarding.
 *
 * Turned on per world in bukkit.yml:
 *   worlds:
 *     world:
 *       biome-provider: BlossomBiomes
 */
public final class BlossomBiomes extends JavaPlugin implements Listener, TabExecutor {

    private final Map<String, BlossomBiomeProvider> providers = new HashMap<>();
    private final Map<UUID, CustomBiome> lastBiome = new HashMap<>();
    private Placement.Settings settings;
    private Shrines shrines;
    private Mobs mobs;
    private BiomesMenu menu;

    @Override
    public void onEnable() {
        saveDefaultConfig();
        settings = readSettings();
        shrines = new Shrines(this);
        shrines.load();
        mobs = new Mobs(this);
        menu = new BiomesMenu(this);
        Items.customModels = customIcons();
        getServer().getPluginManager().registerEvents(this, this);
        getServer().getPluginManager().registerEvents(menu, this);
        getServer().getPluginManager().registerEvents(shrines, this);
        getServer().getPluginManager().registerEvents(mobs, this);
        for (String name : List.of("biome", "biomes", "blossombiomes")) {
            PluginCommand command = getCommand(name);
            if (command != null) {
                command.setExecutor(this);
                command.setTabCompleter(this);
            }
        }
        getServer().getScheduler().runTaskTimer(this, shrines::saveIfDirty, 2400L, 2400L);
        getServer().getScheduler().runTaskTimer(this, this::announceBiomes, 40L, 20L);
        getServer().getScheduler().runTask(this, () -> {
            if (providers.isEmpty()) {
                getLogger().warning("No world uses BlossomBiomes yet. Add 'biome-provider: BlossomBiomes' for your "
                        + "world in bukkit.yml BEFORE the world is first created (see the guide).");
            }
        });
    }

    @Override
    public void onDisable() {
        if (shrines != null) {
            shrines.saveIfDirty();
        }
    }

    /** bukkit.yml -> worlds.<world>.biome-provider: BlossomBiomes */
    @Override
    public BiomeProvider getDefaultBiomeProvider(String worldName, String id) {
        if (settings == null) {
            saveDefaultConfig();
            settings = readSettings();
        }
        return providers.computeIfAbsent(worldName, name -> new BlossomBiomeProvider(this));
    }

    @EventHandler
    public void onWorldInit(WorldInitEvent event) {
        World world = event.getWorld();
        if (world.getBiomeProvider() instanceof BlossomBiomeProvider provider) {
            world.getPopulators().add(new DecorationPopulator(this, provider));
            world.getPopulators().add(new ShrinePopulator(this, provider));
            getLogger().info("Sanctuary shrines and biome decorations will be built in world '" + world.getName() + "'.");
        }
    }

    // ------------------------------------------------------------------ settings

    private Placement.Settings readSettings() {
        ConfigurationSection p = getConfig().getConfigurationSection("placement");
        Map<CustomBiome, Integer> weights = new EnumMap<>(CustomBiome.class);
        ConfigurationSection w = p.getConfigurationSection("weights");
        for (CustomBiome biome : CustomBiome.values()) {
            weights.put(biome, w == null ? 1 : w.getInt(biome.id, 0));
        }
        ConfigurationSection s = getConfig().getConfigurationSection("sanctuary");
        return new Placement.Settings(
                p.getDouble("start-distance", 5000), p.getDouble("full-distance", 10000),
                p.getDouble("coverage", 0.40), p.getDouble("patch-size", 900), p.getDouble("region-size", 650),
                weights,
                s.getDouble("min-distance", 10000), s.getInt("cell-size", 8000), s.getDouble("chance", 0.30),
                s.getInt("radius", 160),
                keys(p.getStringList("keep-vanilla")), keys(p.getStringList("cold-biomes")));
    }

    private static Set<String> keys(List<String> names) {
        Set<String> out = new HashSet<>();
        for (String name : names) {
            String n = name.toLowerCase(Locale.ROOT).trim();
            out.add(n.contains(":") ? n : "minecraft:" + n);
        }
        return out;
    }

    /**
     * Custom item models and menu icons are only used when the server sends a resource pack,
     * otherwise players would see purple-black "missing" items.
     * config.yml custom-icons: auto (default) / true / false
     */
    private boolean customIcons() {
        String mode = String.valueOf(getConfig().getString("custom-icons", "auto")).toLowerCase(Locale.ROOT);
        if (mode.equals("true") || mode.equals("false")) {
            return mode.equals("true");
        }
        String pack = getServer().getResourcePack();
        return pack != null && !pack.isBlank();
    }

    public BlossomBiomeProvider provider(String worldName) {
        return providers.get(worldName);
    }

    public Placement.Settings placementSettings() {
        return settings;
    }

    public Shrines shrines() {
        return shrines;
    }

    public Mobs mobs() {
        return mobs;
    }

    /** Which Blossom biome a spot is in (null = vanilla). Main thread only. */
    public CustomBiome biomeAt(Location location) {
        Biome biome = location.getWorld().getBiome(location);
        return CustomBiome.byKey(biome.getKey().toString());
    }

    /** A list that writes each config mistake to the console. */
    public List<String> problems(String where) {
        return new ArrayList<>() {
            @Override
            public boolean add(String problem) {
                getLogger().warning("config.yml " + where + ": " + problem);
                return true;
            }
        };
    }

    // ------------------------------------------------------------------ messages

    public String raw(String key) {
        String text = getConfig().getString("messages." + key);
        return text == null ? "&cMissing message: " + key : text;
    }

    public void send(CommandSender to, String key, String... replacements) {
        String text = raw(key);
        if (!text.isEmpty()) {
            to.sendMessage(Text.c(raw("prefix") + Text.fill(text, replacements)));
        }
    }

    public String displayName(CustomBiome biome) {
        return getConfig().getString("names." + biome.id, biome.id);
    }

    /** A title the first time a player walks into a Blossom biome (and each time it changes). */
    private void announceBiomes() {
        if (!getConfig().getBoolean("enter-titles", true)) {
            return;
        }
        for (Player player : Bukkit.getOnlinePlayers()) {
            CustomBiome now = biomeAt(player.getLocation());
            CustomBiome before = lastBiome.put(player.getUniqueId(), now);
            if (now == null || now == before) {
                continue;
            }
            player.showTitle(Title.title(Text.c(displayName(now)),
                    Text.c(getConfig().getString("subtitles." + now.id, "")),
                    Title.Times.times(Duration.ofMillis(400), Duration.ofMillis(2500), Duration.ofMillis(800))));
        }
    }

    @EventHandler
    public void onQuit(PlayerQuitEvent event) {
        lastBiome.remove(event.getPlayer().getUniqueId());
    }

    // ------------------------------------------------------------------ commands

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (command.getName().equalsIgnoreCase("biomes")) {
            if (!(sender instanceof Player player)) {
                send(sender, "players-only");
                return true;
            }
            if (args.length > 0 && player.hasPermission("blossombiomes.teleport")) {
                CustomBiome biome = CustomBiome.byKey(args[0].toLowerCase(Locale.ROOT));
                if (biome == null) {
                    send(player, "unknown-biome", "{biome}", args[0]);
                } else {
                    menu.teleport(player, biome);
                }
                return true;
            }
            menu.open(player);
            return true;
        }
        if (command.getName().equalsIgnoreCase("biome")) {
            if (!(sender instanceof Player player)) {
                send(sender, "players-only");
                return true;
            }
            CustomBiome biome = biomeAt(player.getLocation());
            String name = biome != null ? displayName(biome)
                    : "&f" + Text.pretty(player.getWorld().getBiome(player.getLocation()).getKey().getKey());
            send(player, "biome-here", "{biome}", name);
            return true;
        }

        if (!sender.hasPermission("blossombiomes.admin")) {
            send(sender, "no-permission");
            return true;
        }
        String sub = args.length == 0 ? "help" : args[0].toLowerCase(Locale.ROOT);
        switch (sub) {
            case "reload" -> {
                reloadConfig();
                Items.customModels = customIcons();
                send(sender, "reloaded");
            }
            case "where" -> {
                if (!(sender instanceof Player player)) {
                    send(sender, "players-only");
                    return true;
                }
                Location at = player.getLocation();
                CustomBiome biome = biomeAt(at);
                send(player, "where", "{biome}", biome == null ? "&7vanilla" : displayName(biome),
                        "{distance}", Text.number((long) Math.hypot(at.getX(), at.getZ())));
            }
            case "sanctuary" -> {
                if (!(sender instanceof Player player)) {
                    send(sender, "players-only");
                    return true;
                }
                BlossomBiomeProvider provider = providers.get(player.getWorld().getName());
                if (provider == null) {
                    send(player, "not-blossom-world");
                    return true;
                }
                Placement.Sanctuary s = provider.placementFor(player.getWorld()).nearestSanctuary(
                        player.getLocation().getBlockX(), player.getLocation().getBlockZ(), 12);
                if (s == null) {
                    send(player, "no-sanctuary");
                } else {
                    send(player, "nearest-sanctuary", "{x}", String.valueOf(s.x()), "{z}", String.valueOf(s.z()),
                            "{distance}", Text.number((long) s.distance(player.getLocation().getBlockX(),
                                    player.getLocation().getBlockZ())));
                }
            }
            case "shrines" -> send(sender, "shrine-count", "{total}", String.valueOf(shrines.count()),
                    "{sealed}", String.valueOf(shrines.count(Shrines.State.SEALED)),
                    "{awake}", String.valueOf(shrines.count(Shrines.State.AWAKENED)),
                    "{claimed}", String.valueOf(shrines.count(Shrines.State.CLAIMED)));
            default -> {
                for (String line : getConfig().getStringList("messages.admin-help")) {
                    sender.sendMessage(Text.c(line));
                }
            }
        }
        return true;
    }

    @Override
    public List<String> onTabComplete(CommandSender sender, Command command, String label, String[] args) {
        List<String> out = new ArrayList<>();
        if (command.getName().equalsIgnoreCase("biomes") && args.length == 1 && sender.hasPermission("blossombiomes.teleport")) {
            for (CustomBiome biome : CustomBiome.values()) {
                if (biome.id.startsWith(args[0].toLowerCase(Locale.ROOT))) {
                    out.add(biome.id);
                }
            }
            return out;
        }
        if (command.getName().equalsIgnoreCase("blossombiomes") && args.length == 1
                && sender.hasPermission("blossombiomes.admin")) {
            for (String option : List.of("where", "sanctuary", "shrines", "reload")) {
                if (option.startsWith(args[0].toLowerCase(Locale.ROOT))) {
                    out.add(option);
                }
            }
        }
        return out;
    }
}
