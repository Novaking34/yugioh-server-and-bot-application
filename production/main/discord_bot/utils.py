#!/usr/bin/env python3
"""
=============================================================================
Discord Bot Formatting & UI Utilities
=============================================================================
Provides card frame color palettes, parameter formatters, and rich Discord
embed generators matching authentic Yu-Gi-Oh! visual styles.
=============================================================================
"""

import discord
from typing import Optional, Dict, Any, List

# Standard Yu-Gi-Oh! Card Frame Hex Colors
FRAME_COLORS = {
    'normal': 0xD4B37F,       # Normal Monster Yellow
    'effect': 0xC97434,       # Effect Monster Orange
    'ritual': 0x6E9ED4,       # Ritual Blue
    'fusion': 0x9356A0,       # Fusion Violet
    'synchro': 0xEEEEEE,      # Synchro White
    'xyz': 0x111111,          # Xyz Black
    'link': 0x0055AA,         # Link Dark Blue
    'spell': 0x1D9E74,        # Spell Green
    'trap': 0xBC3576,         # Trap Magenta
    'divine': 0xF59E0B,       # Divine Gold / Egyptian God Amber
    'token': 0x9E9E9E         # Token Grey
}


def get_card_color(card_type: Optional[str], card_subtype: Optional[str], attribute: Optional[str] = None) -> int:
    """
    Selects the authentic Discord embed border color corresponding to
    the card's frame category and attribute (including Divine-Beast gold).
    """
    ctype = (card_type or '').strip().lower()
    csub = (card_subtype or '').strip().lower()
    attr = (attribute or '').strip().upper()

    # Divine-Beast / DIVINE cards get distinctive Divine Gold border
    if attr == 'DIVINE' or 'divine' in csub:
        return FRAME_COLORS['divine']

    if ctype == 'spell':
        return FRAME_COLORS['spell']
    if ctype == 'trap':
        return FRAME_COLORS['trap']

    # For monsters, check specific summon frames in priority order
    for mechanic in ['link', 'xyz', 'synchro', 'fusion', 'ritual', 'effect', 'normal']:
        if mechanic in csub:
            return FRAME_COLORS[mechanic]

    return FRAME_COLORS['effect']


def build_card_embed(card: Dict[str, Any]) -> discord.Embed:
    """
    Constructs a rich Discord Embed displaying the card's artwork,
    stats, Set Number, Rarity, Banlist Status, Pendulum scales, effect text,
    and narrative story lore.
    """
    card_type = card.get("card_type") or "Monster"
    card_subtype = card.get("card_subtype") or "Effect"
    attribute = card.get("attribute")
    color = get_card_color(card_type, card_subtype, attribute)

    set_num = card.get("set_number") or ""
    title_text = f"{card['name']} [{set_num}]" if set_num else card["name"]

    duelingbook_url = (
        card.get("duelingbook_url")
        or (f"https://www.duelingbook.com/card?id={card.get('duelingbook_id')}" if card.get("duelingbook_id") else None)
        or f"https://www.duelingbook.com/card?id={card.get('id', '')}"
    )

    rarity = card.get("rarity") or "Common"
    banlist = card.get("banlist_status") or "Unlimited"
    archetype = card.get("archetype")

    header_parts = [f"**[{card_type} / {card_subtype}]**", f"Rarity: **{rarity}**", f"Limit: **{banlist}**"]
    if archetype:
        header_parts.append(f"Archetype: **{archetype}**")

    embed = discord.Embed(
        title=title_text,
        url=duelingbook_url,
        description=" • ".join(header_parts),
        color=color
    )

    if card_type == "Monster":
        csub_lower = card_subtype.lower()
        attr_display = attribute or "N/A"
        race_display = card.get("monster_type") or "N/A"

        stats_lines = [f"**Attribute:** {attr_display} | **Type:** {race_display}"]

        level_val = card.get("level_or_rank_or_link") or 0
        if "link" in csub_lower:
            stats_lines.append(f"**Link Rating:** Link-{level_val} | **Arrows:** {card.get('link_arrows') or 'N/A'}")
        elif "xyz" in csub_lower:
            stats_lines.append(f"**Rank:** {level_val}")
        else:
            stats_lines.append(f"**Level:** {level_val}")

        if card.get("scale") is not None:
            stats_lines[-1] += f" | **Scale:** {card['scale']}"

        def_val = "LINK" if "link" in csub_lower else (card.get("def") if card.get("def") is not None else 0)
        stats_lines.append(f"**ATK:** {card.get('atk', 0)} / **DEF:** {def_val}")

        embed.add_field(name="⚔️ Monster Parameters", value="\n".join(stats_lines), inline=False)
    else:
        embed.add_field(name="📜 Card Type", value=f"**{card_subtype} {card_type}**", inline=True)

    if card.get("pendulum_effect"):
        embed.add_field(name="💎 Pendulum Effect", value=f"```fix\n{card['pendulum_effect']}\n```", inline=False)

    effect_text = card.get("effect_text") or "No effect text recorded."
    embed.add_field(name="📖 Card Effect", value=f"```md\n{effect_text}\n```", inline=False)

    # Narrative Lore and Story Metadata
    meta = []
    if card.get("faction_name"):
        meta.append(f"**Faction:** {card['faction_name']}")
    if card.get("character_name"):
        meta.append(f"**Owner:** {card['character_name']}")
    if card.get("story_significance"):
        meta.append(f"**Role:** {card['story_significance']}")

    lore_content = []
    if card.get("lore_text"):
        lore_content.append(f"*{card['lore_text']}*")
    if meta:
        lore_content.append(" • ".join(meta))

    if lore_content:
        embed.add_field(name="🌌 Story Lore", value="\n\n".join(lore_content), inline=False)

    if card.get("image_url"):
        embed.set_thumbnail(url=card["image_url"])

    creator = card.get("creator_name") or "ProfessorSeanEX"
    passcode = card.get("id", "Unknown")
    embed.set_footer(text=f"Passcode: {passcode} • Set: {set_num or 'TLOK'} • Designed by {creator} • Live in Simulator")
    return embed


def build_rank_embed(player: Dict[str, Any], user: Optional[discord.User] = None) -> discord.Embed:
    """
    Constructs an authentic Duelist License / Ranking card embed.
    """
    from services.rating_service import RatingService
    elo = player.get("elo", 1200)
    tier_name, badge, color = RatingService.get_tier_info(elo)
    username = player.get("username") or (user.display_name if user else "Duelist")

    wins = player.get("wins", 0)
    losses = player.get("losses", 0)
    draws = player.get("draws", 0)
    total_games = wins + losses + draws
    win_rate = round((wins / total_games * 100), 1) if total_games > 0 else 0.0

    streak = player.get("win_streak", 0)
    best_streak = player.get("highest_streak", streak)
    highest_elo = player.get("highest_elo", elo)
    season = player.get("season_id", "Season 1")

    embed = discord.Embed(
        title=f"🪪 Official Duelist License — {username}",
        description=f"**Current Division:** {badge} **{tier_name}**\n*The Land of Kustomazi Custom Card League ({season})*",
        color=color
    )

    embed.add_field(name="⚔️ Competitive Rating", value=f"**{elo} ELO**\n*(Peak: {highest_elo} ELO)*", inline=True)
    embed.add_field(name="📊 Win Rate", value=f"**{win_rate}%**\n`{wins}W - {losses}L - {draws}D`", inline=True)
    embed.add_field(name="🔥 Current Streak", value=f"**{streak} Wins**\n*(Best: {best_streak})*", inline=True)

    if user and user.display_avatar:
        embed.set_thumbnail(url=user.display_avatar.url)

    embed.set_footer(text=f"Duelist ID: {player.get('user_id')} • FIDE K=32 • Set 1: The Land of Kustomazi")
    return embed


def build_leaderboard_embed(entries: list, season_id: str = "Season 1") -> discord.Embed:
    """
    Constructs a rich competitive leaderboard for the custom card league.
    """
    from services.rating_service import RatingService
    embed = discord.Embed(
        title=f"🏆 The Land of Kustomazi — Leaderboard ({season_id})",
        description="Top rated duelists battling with Set 1 custom cards.",
        color=0xF59E0B
    )

    if not entries:
        embed.description += "\n\n*No ranked duels recorded yet for this season. Be the first to duel!*"
        return embed

    lines = []
    medals = ["🥇", "🥈", "🥉"]
    for i, p in enumerate(entries, start=1):
        medal = medals[i-1] if i <= 3 else f"`#{i}`"
        _, badge, _ = RatingService.get_tier_info(p["elo"])
        uname = p.get("username", "Unknown")
        streak_str = f" 🔥{p['win_streak']}" if p.get("win_streak", 0) >= 3 else ""
        wins = p.get("wins", 0)
        losses = p.get("losses", 0)
        wr = p.get("win_rate")
        if wr is None:
            tot = wins + losses + p.get("draws", 0)
            wr = round((wins / tot * 100), 1) if tot > 0 else 0.0
        lines.append(
            f"{medal} {badge} **{uname}** — **{p['elo']} ELO** "
            f"({wins}W/{losses}L | {wr}%){streak_str}"
        )


    embed.add_field(name="Rankings", value="\n".join(lines), inline=False)
    embed.set_footer(text="Use /duel to challenge an opponent to a Ranked match and climb the ladder!")
    return embed


def build_card_stats_embed(stats: Dict[str, Any]) -> discord.Embed:
    """
    Generates a card usage and telemetry overview embed.
    """
    cname = stats.get("name", "Unknown Card")
    set_num = stats.get("set_number", "")
    title = f"📈 Card Telemetry: {cname} [{set_num}]" if set_num else f"📈 Card Telemetry: {cname}"

    ctype = stats.get("card_type", "Monster")
    csub = stats.get("card_subtype", "Effect")
    color = get_card_color(ctype, csub)

    embed = discord.Embed(
        title=title,
        description=f"**Type:** `{ctype} / {csub}` | **Rarity:** `{stats.get('rarity', 'Common')}`",
        color=color
    )

    times_decked = stats.get("times_decked", 0)
    times_drawn = stats.get("times_drawn", 0)
    times_played = stats.get("times_played", 0)
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    total_duels = wins + losses
    win_rate = stats.get("win_rate", 0.0)

    embed.add_field(name="📦 Active Decks", value=f"Included in **{times_decked}** deck(s)", inline=True)
    embed.add_field(name="🃏 Duel Appearances", value=f"Drawn **{times_drawn}**x\nPlayed **{times_played}**x", inline=True)
    embed.add_field(name="🏆 Match Win Rate", value=f"**{win_rate}%** ({wins}W / {losses}L)", inline=True)

    embed.set_footer(text="Telemetry tracked live across player decks and Discord duels.")
    return embed


def build_story_stage_embed(stage: Dict[str, Any], progress: Dict[str, Any]) -> discord.Embed:
    """
    Builds an RPG story encounter embed displaying dialogue, boss profile, and rewards.
    """
    embed = discord.Embed(
        title=f"🌌 Story Chapter 1 — Stage {stage['stage_number']}: {stage['title']}",
        description=f"*{stage['intro_dialogue']}*",
        color=0x8B5CF6
    )

    opp_title = f" ({stage['opponent_title']})" if stage.get("opponent_title") else ""
    deck_name = stage.get("opponent_deck_name") or "Kasutamaiza - Creation Control"
    embed.add_field(
        name="⚔️ Encounter Challenger",
        value=f"**{stage['opponent_name']}**{opp_title}\nDeck: *{deck_name}*",
        inline=False
    )

    rewards = []
    if stage.get("reward_title"):
        rewards.append(f"🏅 Title: **{stage['reward_title']}**")
    if stage.get("reward_card_name"):
        set_num = f" [{stage.get('reward_card_set')}]" if stage.get('reward_card_set') else ""
        rewards.append(f"🃏 Custom Card: **{stage['reward_card_name']}**{set_num}")

    if rewards:
        embed.add_field(name="🎁 First-Time Clear Rewards", value="\n".join(rewards), inline=False)

    highest = progress.get("highest_stage_completed", 0)
    is_cleared = (highest >= stage["stage_number"])
    status = "✅ Completed (Replayable)" if is_cleared else "⏳ In Progress / Uncompleted"
    embed.add_field(name="📜 Mission Status", value=f"**{status}**", inline=False)

    if stage.get("opponent_avatar"):
        embed.set_thumbnail(url=stage["opponent_avatar"])

    embed.set_footer(text="Click 'Begin Story Duel' below to challenge this encounter!")
    return embed


# =============================================================================
# 7. DUEL BOARD MODEL & FIELD VISUALIZATION UTILITIES
# =============================================================================

class DuelBoard:
    """
    State model representing a duelist's side of the official Yu-Gi-Oh! duel field.
    Tracks Main Monster Zones (1-5), Spell & Trap Zones (1-5), Field Spell Zone,
    Graveyard, and Banished Zone.
    """

    def __init__(self, player_name: Optional[str] = None):
        self.player_name = player_name
        # 5 Main Monster Zones: each is None or dict with {id, name, atk, def, position: "ATK"|"DEF"|"SET"}
        self.mmz: List[Optional[Dict[str, Any]]] = [None] * 5
        # 5 Spell & Trap Zones: each is None or dict with {id, name, state: "FACEUP"|"SET"}
        self.stz: List[Optional[Dict[str, Any]]] = [None] * 5
        # Field Spell Zone: None or dict with {id, name}
        self.field_spell: Optional[Dict[str, Any]] = None
        # Graveyard and Banished piles
        self.gy: List[int] = []
        self.banished: List[int] = []

    def summon_monster(self, card_data: Dict[str, Any], position: str = "ATK", zone_idx: Optional[int] = None) -> Optional[int]:
        """Places a monster in an available MMZ (0 to 4). Returns zone index or None if full."""
        pos = position.upper()
        if pos not in ("ATK", "DEF", "SET"):
            pos = "ATK"

        monster_entry = {
            "id": card_data.get("id"),
            "name": card_data.get("name", "Monster"),
            "atk": card_data.get("atk") or 0,
            "def": card_data.get("def") or 0,
            "position": pos
        }

        if zone_idx is not None and 0 <= zone_idx < 5 and self.mmz[zone_idx] is None:
            self.mmz[zone_idx] = monster_entry
            return zone_idx

        for i in range(5):
            if self.mmz[i] is None:
                self.mmz[i] = monster_entry
                return i
        return None

    def play_spell_or_trap(self, card_data: Dict[str, Any], state: str = "FACEUP", zone_idx: Optional[int] = None) -> Optional[int]:
        """Places a Spell or Trap in an available S/T Zone (0 to 4). Returns zone index or None if full."""
        st_entry = {
            "id": card_data.get("id"),
            "name": card_data.get("name", "Spell/Trap"),
            "card_type": card_data.get("card_type", "Spell"),
            "subtype": card_data.get("card_subtype", "Normal"),
            "state": state.upper()
        }

        if zone_idx is not None and 0 <= zone_idx < 5 and self.stz[zone_idx] is None:
            self.stz[zone_idx] = st_entry
            return zone_idx

        for i in range(5):
            if self.stz[i] is None:
                self.stz[i] = st_entry
                return i
        return None

    def play_field_spell(self, card_data: Dict[str, Any]) -> str:
        """Sets or activates a Field Spell in the dedicated Field Spell Zone."""
        old_field = self.field_spell
        if old_field and old_field.get("id"):
            self.gy.append(old_field["id"])
        self.field_spell = {
            "id": card_data.get("id"),
            "name": card_data.get("name", "Field Spell")
        }
        return self.field_spell["name"]

    def banish_card(self, card_id: int) -> None:
        """Sends a card to the Banished Zone."""
        self.banished.append(card_id)

    def send_to_gy(self, card_id: int) -> None:
        """Sends a card to the Graveyard."""
        self.gy.append(card_id)

    @property
    def active_monsters(self) -> List[Dict[str, Any]]:
        """Returns all non-empty monsters on field."""
        return [m for m in self.mmz if m is not None]

    @property
    def highest_atk_monster(self) -> Optional[Dict[str, Any]]:
        """Returns monster with highest ATK in attack position."""
        atk_monsters = [m for m in self.mmz if m and m.get("position") == "ATK"]
        if not atk_monsters:
            return None
        return max(atk_monsters, key=lambda m: m.get("atk", 0))

    def format_mmz_display(self) -> str:
        """Returns clean 5-slot MMZ status string (e.g. `[⚔️ 4000] [🛡️ 2000] [—] [—] [—]`)."""
        slots = []
        for m in self.mmz:
            if m is None:
                slots.append("`[ — ]`")
            elif m["position"] == "SET":
                slots.append("`[🎴 SET]`")
            elif m["position"] == "DEF":
                slots.append(f"`[🛡️{m.get('def', 0)}]`")
            else:
                slots.append(f"`[⚔️{m.get('atk', 0)}]`")
        return " ".join(slots)

    def format_stz_display(self) -> str:
        """Returns clean 5-slot Spell & Trap Zone status string."""
        slots = []
        for s in self.stz:
            if s is None:
                slots.append("`[ — ]`")
            elif s["state"] == "SET":
                slots.append("`[🎴 SET]`")
            else:
                slots.append(f"`[✨ {s['name'][:6]}]`")
        return " ".join(slots)


def render_duel_field_ascii(
    player_board: DuelBoard,
    opp_board: DuelBoard,
    p_name: str,
    opp_name: str,
    p_lp: int,
    opp_lp: int,
    p_hand: int,
    opp_hand: int,
    p_deck: int,
    opp_deck: int
) -> str:
    """Renders a clean ASCII duel mat representing the shared Yu-Gi-Oh! board."""
    p_field_str = player_board.field_spell["name"] if player_board.field_spell else "None"
    opp_field_str = opp_board.field_spell["name"] if opp_board.field_spell else "None"

    lines = [
        f"🤖 **{opp_name}** — **{opp_lp} LP** | Hand: `{opp_hand}` | Deck: `{opp_deck}` | GY: `{len(opp_board.gy)}` | Banished: `{len(opp_board.banished)}`",
        f"   Field Spell: *{opp_field_str}*",
        f"   STZ: {opp_board.format_stz_display()}",
        f"   MMZ: {opp_board.format_mmz_display()}",
        f"   ═════════════════ `[EMZ 1: —]`   `[EMZ 2: —]` ═════════════════",
        f"   MMZ: {player_board.format_mmz_display()}",
        f"   STZ: {player_board.format_stz_display()}",
        f"   Field Spell: *{p_field_str}*",
        f"👤 **{p_name}** — **{p_lp} LP** | Hand: `{p_hand}` | Deck: `{p_deck}` | GY: `{len(player_board.gy)}` | Banished: `{len(player_board.banished)}`"
    ]
    return "\n".join(lines)


def build_board_guide_embed() -> discord.Embed:
    """Constructs a rich educational embed explaining the Yu-Gi-Oh! Master Rule board."""
    embed = discord.Embed(
        title="🏛️ Yu-Gi-Oh! Duel Field & Board Zone Guide",
        description=(
            "The duel field (playmat) is a shared symmetrical arena under standard **Master Rules**.\n"
            "Understanding zone placement is vital for monster positions, Field Spells, Link arrows, and Void banishing!"
        ),
        color=0x3B82F6
    )

    board_ascii = (
        "```text\n"
        "                     OPPONENT'S FIELD\n"
        " [Field]                                  [GY]\n"
        " [Extra]  [S/T 5] [S/T 4] [S/T 3] [S/T 2] [S/T 1]  [Deck]\n"
        "          [MMZ 5] [MMZ 4] [MMZ 3] [MMZ 2] [MMZ 1]  [Banished]\n"
        "──────────────────── [EMZ 1]   [EMZ 2] ────────────────────\n"
        "          [MMZ 1] [MMZ 2] [MMZ 3] [MMZ 4] [MMZ 5]  [Banished]\n"
        " [Extra]  [S/T 1] [S/T 2] [S/T 3] [S/T 4] [S/T 5]  [Deck]\n"
        " [Field]                                  [GY]\n"
        "                      YOUR FIELD\n"
        "```"
    )
    embed.add_field(name="🗺️ Master Rule Field Architecture", value=board_ascii, inline=False)

    embed.add_field(
        name="⚔️ Main Monster Zones (MMZ 1-5)",
        value="5 slots for Normal, Tribute, and Special Summoned monsters. Monsters can be in **Face-Up Attack** (vertical, uses ATK), **Face-Up Defense** (horizontal, uses DEF), or **Face-Down Set** (horizontal, hides stats).",
        inline=False
    )
    embed.add_field(
        name="🌌 Extra Monster Zones (EMZ 1-2)",
        value="2 shared zones in the middle. Extra Deck Link monsters and face-up Pendulum monsters from Extra Deck must be summoned here. Fusion, Synchro, and Xyz monsters can be summoned here or directly to any MMZ.",
        inline=False
    )
    embed.add_field(
        name="✨ Spell & Trap Zones (S/T 1-5) & Pendulum Zones",
        value="5 slots for Normal, Continuous, Quick-Play, Equip, or Counter Spells/Traps. **Columns 1 and 5** double as Pendulum Zones when setting Pendulum scales.",
        inline=False
    )
    embed.add_field(
        name="🌱 Field Spell Zone",
        value="Dedicated zone (top-left) holding your active Field Spell (e.g. *The Land of Kustomazi* environmental spells). Both players can maintain active Field Spells simultaneously.",
        inline=True
    )
    embed.add_field(
        name="💀 Graveyard (GY) & 🌀 Banished",
        value="**GY:** Public face-up pile for destroyed/tributed cards.\n**Banished:** Separate zone for cards banished face-up or face-down by Void effects.",
        inline=True
    )
    embed.set_footer(text="Master Rule (2020 Revision) • The Land of Kustomazi Platform")
    return embed


# =============================================================================
# 8. CARD TYPES, SUBTYPES & 26 MONSTER RACES METADATA
# =============================================================================

SPELL_CARD_TYPES = {
    "Normal Spell": {
        "icon": "None",
        "speed": "Spell Speed 1",
        "description": "Activated during your Main Phase on an open game state. Sent to the Graveyard immediately upon resolving."
    },
    "Continuous Spell": {
        "icon": "∞ (Infinity)",
        "speed": "Spell Speed 1",
        "description": "Remains face-up on the field in a Spell & Trap Zone after activation, providing ongoing or triggered effects."
    },
    "Equip Spell": {
        "icon": "+ (Crossed Swords)",
        "speed": "Spell Speed 1",
        "description": "Attaches to 1 face-up monster on field, modifying stats or granting effects. Destroyed if the monster leaves the field."
    },
    "Quick-Play Spell": {
        "icon": "⚡ (Lightning Bolt)",
        "speed": "Spell Speed 2",
        "description": "Can be activated from hand during any phase of your turn, or Set face-down to activate during the opponent's turn like a Trap."
    },
    "Field Spell": {
        "icon": "⨁ (Compass Rose)",
        "speed": "Spell Speed 1",
        "description": "Placed in the dedicated Field Spell Zone (does not take up a S/T Zone). Provides global or archetype-wide environment effects."
    },
    "Ritual Spell": {
        "icon": "🔥 (Flame)",
        "speed": "Spell Speed 1",
        "description": "Tributes monsters from hand or field to Special Summon a designated Ritual Monster from hand."
    }
}

TRAP_CARD_TYPES = {
    "Normal Trap": {
        "icon": "None",
        "speed": "Spell Speed 2",
        "description": "One-time reactive effect. Activated in response to an action or game state, resolves, and is sent to Graveyard."
    },
    "Continuous Trap": {
        "icon": "∞ (Infinity)",
        "speed": "Spell Speed 2",
        "description": "Remains face-up in the Spell & Trap Zone after activation, continuously altering game rules, floodgating, or triggering per turn."
    },
    "Counter Trap": {
        "icon": "⤶ (Counter Arrow)",
        "speed": "Spell Speed 3",
        "description": "The fastest cards in the game. Used specifically to negate summons, activations, or attacks. Only another Counter Trap can respond."
    }
}

MONSTER_CARD_FRAMES = {
    "Normal Monster": "Yellow Frame • Has no card effects; features flavor text describing its lore and combat style.",
    "Effect Monster": "Orange Frame • The cornerstone of Yu-Gi-Oh!; possesses Ignition, Trigger, Continuous, or Quick effects.",
    "Ritual Monster": "Light Blue Frame • Main Deck monster; summoned via a Ritual Spell with required material Tributes.",
    "Pendulum Monster": "Half Monster / Half Spell Frame • Can be summoned as a monster or placed in Column 1/5 to set Pendulum Scales.",
    "Fusion Monster": "Violet Frame (Extra Deck) • Summoned by fusing materials together (e.g. Polymerization or contact fusion).",
    "Synchro Monster": "White Frame (Extra Deck) • Summoned by sending 1 Tuner + 1+ non-Tuners whose Levels exactly equal the Synchro's Level.",
    "Xyz Monster": "Black Frame (Extra Deck) • Possesses Ranks instead of Levels. Summoned by overlaying same-Level monsters as Xyz Materials.",
    "Link Monster": "Dark Blue Frame (Extra Deck) • Has Link Arrows and Link Rating instead of DEF. Cannot exist in Defense Position.",
    "Token Monster": "Grey Frame • Generated on field by card effects; ceases to exist if it leaves the field."
}

ALL_26_MONSTER_RACES = [
    ("Dragon", "Legendary scaled beasts, cosmic wyrms, and cataclysmic powerhouses."),
    ("Spellcaster", "Mystics, sorcerers, alchemists, and wielders of arcane spellcraft."),
    ("Warrior", "Combat soldiers, knights, samurai, and masters of armed martial combat."),
    ("Beast-Warrior", "Humanoid beings fusing the strength of beasts with martial discipline."),
    ("Beast", "Wild animals, primal fauna, predators, and woodland spirits."),
    ("Winged Beast", "Avian predators, harpies, falcons, and airborne creatures."),
    ("Fiend", "Demons, shadow dwellers, archfiends, and dark netherworld entities."),
    ("Fairy", "Angels, celestial beings, holy heralds, and divine emissaries."),
    ("Zombie", "Undead ghouls, vampires, spectral spirits, and Graveyard recursors."),
    ("Machine", "Mechs, automatons, clockwork gear, robotic superweapons, and vehicles."),
    ("Aqua", "Water elementals, marine amphibians, oozes, and liquid entities."),
    ("Pyro", "Creatures of pure flame, magma, volcanics, and incinerating fire."),
    ("Rock", "Earthen golems, geological formations, fossils, and crystal entities."),
    ("Plant", "Botanical flora, carnivorous vines, sentient blossoms, and forest roots."),
    ("Insect", "Bugs, arachnids, mantises, and hive swarms."),
    ("Thunder", "Beings of raw lightning, voltage, storms, and electrostatic energy."),
    ("Dinosaur", "Prehistoric behemoths, apex carnivores, and primal giants."),
    ("Fish", "Aquatic swimmers, sharks, and abyssal swimmers."),
    ("Sea Serpent", "Leviathans, sea serpents, krakens, and colossal trench terrors."),
    ("Reptile", "Snakes, lizards, chameleons, and venomous cold-blooded beasts."),
    ("Psychic", "Beings of mental power, telekinesis, brainwaves, and cyber-kinetics."),
    ("Cyberse", "Digital lifeforms, network avatars, and AI constructs."),
    ("Wyrm", "Spiritual dragons, ethereal serpents, and celestial energy beings."),
    ("Illusion", "Phantasms and mirages that neither destroy nor can be destroyed in battle."),
    ("Divine-Beast", "Supreme primordial god-entities (The Egyptian Gods & The Great Kasutamaiza)."),
    ("Creator-God", "The transcendent divine architect (Holactie the Creator of Light).")
]


CARD_ATTRIBUTES = {
    "LIGHT": {
        "kanji": "光",
        "symbol": "☀️",
        "bitmask": 0x10,
        "color": 0xF1C40F,
        "description": "Radiance, celestial messengers, purity, and illumination. Central to the Kasutamaiza creation pantheon."
    },
    "DARK": {
        "kanji": "闇",
        "symbol": "🌑",
        "bitmask": 0x20,
        "color": 0x8E44AD,
        "description": "Shadow arts, netherworld entities, occult sorcerers, fiends, necromancy, and void manipulation."
    },
    "EARTH": {
        "kanji": "地",
        "symbol": "⛰️",
        "bitmask": 0x01,
        "color": 0xB9770E,
        "description": "Terrestrial bedrock, steadfast warriors, mineral golems, and primal physical force."
    },
    "WATER": {
        "kanji": "水",
        "symbol": "🌊",
        "bitmask": 0x02,
        "color": 0x2980B9,
        "description": "Tidal currents, glacial ice, aquatic fauna, oceanic abysses, and fluid combat adaptability."
    },
    "FIRE": {
        "kanji": "炎",
        "symbol": "🔥",
        "bitmask": 0x04,
        "color": 0xE74C3C,
        "description": "Combustion, molten magma, volcanic beasts, explosive burnout, and fiery passion."
    },
    "WIND": {
        "kanji": "風",
        "symbol": "🌪️",
        "bitmask": 0x08,
        "color": 0x27AE60,
        "description": "Atmospheric gales, avian predators, cyclone storms, and rapid tempo acceleration."
    },
    "DIVINE": {
        "kanji": "神",
        "symbol": "✨",
        "bitmask": 0x40,
        "color": 0xD4AC0D,
        "description": "Transcendent primordial god-entities (The Egyptian Gods, Holactie, and The Great Kasutamaiza)."
    }
}

LEVELS_AND_RANKS_DATA = {
    "levels": {
        "title": "⭐ Monster Levels (1 – 12)",
        "stars_icon": "⭐ (Yellow/Orange Stars)",
        "reading_order": "Top-Right, reading right-to-left",
        "applies_to": "Main Deck monsters (Normal, Effect, Ritual, Pendulum) and Extra Deck (Fusion, Synchro)",
        "tribute_rules": [
            "• **Level 1 to 4 (Low-Level):** Normal Summoned or Set directly with **0 Tributes**.",
            "• **Level 5 to 6 (Mid-Level):** Requires **1 Tribute** (sending 1 monster from your field to the GY).",
            "• **Level 7 to 9 (High-Level):** Requires **2 Tributes** (sending 2 monsters from your field to the GY).",
            "• **Level 10 to 12 (God-Tier):** Standard **2 Tributes**, unless card text requires 3 Tributes (e.g. *The Great Kasutamaiza*, Egyptian Gods)."
        ],
        "summon_math": [
            "• **Synchro Summoning:** Tuner Level + 1+ Non-Tuner Levels must exactly equal the Synchro Monster's Level.",
            "• **Ritual Summoning:** Tributes must have total Levels equal to or exceeding the Ritual Monster's Level."
        ]
    },
    "ranks": {
        "title": "⯪ Monster Ranks (1 – 13)",
        "stars_icon": "⯪ (Yellow Stars in Black Orbs)",
        "reading_order": "Top-Left, reading left-to-right",
        "applies_to": "Exclusively Xyz Monsters (Black Frame)",
        "golden_rule": "⚠️ **RANKS ARE NOT LEVELS!** An Xyz monster has NO Level (Level 0 / undefined).",
        "consequences": [
            "• Cannot be used as material for Synchro, Ritual, or Tribute Summons that demand a Level.",
            "• Completely unaffected by Level-modifying effects (e.g. *Gravity Bind*, *Level Limit - Area B*)."
        ],
        "xyz_mechanics": [
            "• **Xyz Summoning:** Overlay 2 or more monsters with the *exact same Level* matching the Xyz Monster's Rank.",
            "• **Xyz Materials:** Stacked underneath the card; they do not occupy monster zones and do not count as cards on field.",
            "• **Detaching:** Sent to the GY as costs to activate devastating Xyz effects."
        ]
    },
    "link_ratings": {
        "title": "🔗 Link Ratings & Link Arrows",
        "icon": "HEXAGON & ARROWS (Dark Blue Frame)",
        "stats": "No Level, No Rank, and **NO DEF** (cannot exist in Defense Position)",
        "link_rating": "The number in the bottom right (Link-1 to Link-6+) dictates the exact material count required.",
        "link_arrows": "Red directional arrows pointing to adjacent zones, unlocking Extra Monster Zones and Co-Linking."
    },
    "pendulum_scales": {
        "title": "⚖️ Pendulum Scales (0 – 13)",
        "icon": "💎 Blue (Left) & Red (Right) Scales",
        "placement": "Placed in the leftmost (Column 1) and rightmost (Column 5) Spell & Trap Zones.",
        "pendulum_summon": "Once per turn during Main Phase, Special Summon any number of monsters from hand (and face-up from Extra Deck to EMZ/Link zones) whose Levels fall strictly **between** the two scales (exclusive: e.g. Scales 1 and 8 summon Levels 2 through 7)."
    }
}


def get_tribute_requirement(level: Optional[int]) -> int:
    """
    Returns the minimum number of field tributes required for a standard Normal/Tribute Summon.
    - Level 1-4: 0 tributes
    - Level 5-6: 1 tribute
    - Level 7+: 2 tributes
    - None / <=0: 0 tributes
    """
    if not level or level <= 4:
        return 0
    if level in (5, 6):
        return 1
    return 2


def calculate_battle_damage(
    attacker: Dict[str, Any],
    defender: Optional[Dict[str, Any]],
    is_direct: bool = False
) -> Dict[str, Any]:
    """
    Simulates complete official Yu-Gi-Oh! battle damage calculation and destruction rules.
    """
    atk_val = attacker.get("atk", 0)
    atk_name = attacker.get("name", "Attacking Monster")

    if is_direct or defender is None:
        return {
            "is_direct": True,
            "damage": atk_val,
            "damaged_side": "defender",
            "attacker_destroyed": False,
            "defender_destroyed": False,
            "summary": f"⚔️ **{atk_name}** attacks directly for **{atk_val}** battle damage!"
        }

    def_name = defender.get("name", "Defending Monster")
    def_pos = defender.get("position", "ATK").upper()
    def_atk = defender.get("atk", 0)
    def_def = defender.get("def", 0)

    # 1. Defender is in Attack Position: Compare ATK vs ATK
    if def_pos == "ATK":
        if atk_val > def_atk:
            diff = atk_val - def_atk
            return {
                "is_direct": False,
                "damage": diff,
                "damaged_side": "defender",
                "attacker_destroyed": False,
                "defender_destroyed": True,
                "summary": f"💥 **{atk_name}** ({atk_val} ATK) destroys **{def_name}** ({def_atk} ATK)! Opponent takes **{diff}** battle damage."
            }
        elif atk_val < def_atk:
            diff = def_atk - atk_val
            return {
                "is_direct": False,
                "damage": diff,
                "damaged_side": "attacker",
                "attacker_destroyed": True,
                "defender_destroyed": False,
                "summary": f"🛡️ **{atk_name}** ({atk_val} ATK) crashes into **{def_name}** ({def_atk} ATK) and is destroyed! You take **{diff}** battle damage."
            }
        else:
            return {
                "is_direct": False,
                "damage": 0,
                "damaged_side": "neither",
                "attacker_destroyed": True,
                "defender_destroyed": True,
                "summary": f"💥 Both **{atk_name}** and **{def_name}** have equal ATK ({atk_val})! Both monsters are destroyed; 0 damage taken."
            }

    # 2. Defender is in Defense Position (Face-up or Face-down Set): Compare ATK vs DEF
    else:
        was_set = (def_pos == "SET")
        flip_txt = " (flipped face-up)" if was_set else ""
        if atk_val > def_def:
            return {
                "is_direct": False,
                "damage": 0,
                "damaged_side": "neither",
                "attacker_destroyed": False,
                "defender_destroyed": True,
                "summary": f"🛡️ **{atk_name}** ({atk_val} ATK) destroys defending **{def_name}**{flip_txt} ({def_def} DEF)! No battle damage inflicted."
            }
        elif atk_val < def_def:
            diff = def_def - atk_val
            return {
                "is_direct": False,
                "damage": diff,
                "damaged_side": "attacker",
                "attacker_destroyed": False,
                "defender_destroyed": False,
                "summary": f"🧱 **{atk_name}** ({atk_val} ATK) fails to pierce **{def_name}**{flip_txt} ({def_def} DEF)! Neither monster is destroyed; attacker takes **{diff}** battle damage."
            }
        else:
            return {
                "is_direct": False,
                "damage": 0,
                "damaged_side": "neither",
                "attacker_destroyed": False,
                "defender_destroyed": False,
                "summary": f"🛡️ **{atk_name}** ({atk_val} ATK) matches **{def_name}**{flip_txt} ({def_def} DEF). Neither monster is destroyed; 0 damage taken."
            }


def build_card_types_guide_embed(category: Optional[str] = None) -> discord.Embed:
    """
    Constructs a rich educational Discord Embed explaining Yu-Gi-Oh! card types,
    spell speeds, monster summoning frames, the 26 official monster races,
    elemental attributes, and Level vs Rank rules.
    """
    cat = (category or "overview").strip().lower()

    if cat == "spells":
        embed = discord.Embed(
            title="📗 Yu-Gi-Oh! Card Classification — Spell Cards",
            description="Spells provide instant, continuous, or environmental advantages. Identified by their top-right icon:",
            color=FRAME_COLORS["spell"]
        )
        for name, data in SPELL_CARD_TYPES.items():
            icon_str = f" `{data['icon']}`" if data['icon'] != "None" else ""
            embed.add_field(
                name=f"{name}{icon_str} [{data['speed']}]",
                value=data["description"],
                inline=False
            )
        embed.set_footer(text="Spell Speed 1: Normal, Continuous, Equip, Field, Ritual • Spell Speed 2: Quick-Play")
        return embed

    elif cat == "traps":
        embed = discord.Embed(
            title="📕 Yu-Gi-Oh! Card Classification — Trap Cards",
            description="Traps must be Set face-down for at least 1 turn before activation. Used to disrupt the opponent:",
            color=FRAME_COLORS["trap"]
        )
        for name, data in TRAP_CARD_TYPES.items():
            icon_str = f" `{data['icon']}`" if data['icon'] != "None" else ""
            embed.add_field(
                name=f"{name}{icon_str} [{data['speed']}]",
                value=data["description"],
                inline=False
            )
        embed.set_footer(text="Spell Speed 2: Normal, Continuous • Spell Speed 3: Counter Traps (Only Counter Traps can respond!)")
        return embed

    elif cat == "monsters":
        embed = discord.Embed(
            title="📙 Yu-Gi-Oh! Card Classification — Monster Categories & Frames",
            description="Monsters battle for field control and reduce the opponent's Life Points. Categorized by frame & summon mechanic:",
            color=FRAME_COLORS["effect"]
        )
        for frame, desc in MONSTER_CARD_FRAMES.items():
            embed.add_field(name=frame, value=desc, inline=False)
        embed.add_field(
            name="Sub-Classifications",
            value="• **Tuner:** Synchro material\n• **Flip:** Triggers on flip face-up\n• **Union:** Equips to other monsters\n• **Spirit:** Returns to hand at End Phase\n• **Gemini:** Re-summon to unlock effect",
            inline=False
        )
        embed.set_footer(text="Main Deck: Normal, Effect, Ritual, Pendulum • Extra Deck: Fusion, Synchro, Xyz, Link")
        return embed

    elif cat == "races":
        embed = discord.Embed(
            title="🐉 Yu-Gi-Oh! The 26 Official Monster Types (Races)",
            description="Printed on every monster card `[Type / Subtype]`. Distinguishes tribal synergy, not to be confused with Attributes (elements):",
            color=FRAME_COLORS["divine"]
        )
        col1 = []
        col2 = []
        for i, (race, desc) in enumerate(ALL_26_MONSTER_RACES):
            line = f"• **{race}**: *{desc}*"
            if i < 13:
                col1.append(line)
            else:
                col2.append(line)

        embed.add_field(name="Part 1 (Types 1-13)", value="\n".join(col1), inline=False)
        embed.add_field(name="Part 2 (Types 14-26)", value="\n".join(col2), inline=False)
        embed.set_footer(text="All 26 Official Yu-Gi-Oh! Monster Types • The Land of Kustomazi Platform")
        return embed

    elif cat == "attributes":
        embed = discord.Embed(
            title="✨ Yu-Gi-Oh! The 7 Elemental Card Attributes",
            description=(
                "Located in the upper-right corner of Monster cards. Dictates elemental alignment, "
                "attribute locking (e.g. *Gozen Match*), and fusion/archetype synergy:"
            ),
            color=0xF1C40F
        )
        for attr_name, data in CARD_ATTRIBUTES.items():
            embed.add_field(
                name=f"{data['symbol']} {attr_name} ({data['kanji']}) [Bitmask: {hex(data['bitmask'])}]",
                value=data["description"],
                inline=False
            )
        embed.set_footer(text="The 7 Canonical Attributes: LIGHT, DARK, EARTH, WATER, FIRE, WIND, DIVINE")
        return embed

    elif cat in ("levels_ranks", "levels", "ranks"):
        embed = discord.Embed(
            title="⭐ Yu-Gi-Oh! Monster Anatomy: Levels, Ranks & Scales",
            description="Every monster features distinct numeric scaling determining how it enters the field and participates in Extra Deck summons:",
            color=0xF39C12
        )
        lv_data = LEVELS_AND_RANKS_DATA["levels"]
        embed.add_field(
            name=f"{lv_data['title']} — {lv_data['stars_icon']}",
            value="\n".join(lv_data["tribute_rules"]) + "\n" + "\n".join(lv_data["summon_math"]),
            inline=False
        )

        rk_data = LEVELS_AND_RANKS_DATA["ranks"]
        embed.add_field(
            name=f"{rk_data['title']} — {rk_data['stars_icon']}",
            value=f"{rk_data['golden_rule']}\n" + "\n".join(rk_data["consequences"]) + "\n" + "\n".join(rk_data["xyz_mechanics"]),
            inline=False
        )

        lnk_data = LEVELS_AND_RANKS_DATA["link_ratings"]
        embed.add_field(
            name=lnk_data["title"],
            value=f"• **Stats:** {lnk_data['stats']}\n• **Rating:** {lnk_data['link_rating']}\n• **Arrows:** {lnk_data['link_arrows']}",
            inline=False
        )

        pen_data = LEVELS_AND_RANKS_DATA["pendulum_scales"]
        embed.add_field(
            name=pen_data["title"],
            value=f"• **Zones:** {pen_data['placement']}\n• **Summon Range:** {pen_data['pendulum_summon']}",
            inline=False
        )
        embed.set_footer(text="Master Rule 2020: Levels (Stars) • Ranks (Black Orbs) • Links (No DEF) • Scales (Summon Range)")
        return embed

    else:
        # Complete Overview
        embed = discord.Embed(
            title="🃏 Master Guide: Yu-Gi-Oh! Card Anatomy & Classifications",
            description="Yu-Gi-Oh! cards are governed by rigid structural classifications, elemental affinities, and numeric scaling.",
            color=0x3B82F6
        )
        embed.add_field(
            name="1. 📗 Spell Cards (6 Types)",
            value="• **Normal Spell** [Speed 1]\n• **Continuous Spell** `∞` [Speed 1]\n• **Equip Spell** `+` [Speed 1]\n• **Quick-Play Spell** `⚡` [Speed 2]\n• **Field Spell** `⨁` [Speed 1]\n• **Ritual Spell** `🔥` [Speed 1]",
            inline=True
        )
        embed.add_field(
            name="2. 📕 Trap Cards (3 Types)",
            value="• **Normal Trap** [Speed 2]\n• **Continuous Trap** `∞` [Speed 2]\n• **Counter Trap** `⤶` [Speed 3 — Unresponsive except by Counter Traps!]",
            inline=True
        )
        embed.add_field(
            name="3. 📙 Monster Frames & Mechanics",
            value="• **Main Deck:** Normal, Effect, Ritual, Pendulum\n• **Extra Deck:** Fusion, Synchro, Xyz, Link\n• **Special:** Tuner, Flip, Union, Spirit, Gemini, Token",
            inline=True
        )
        embed.add_field(
            name="4. ✨ The 7 Attributes",
            value="☀️ **LIGHT** • 🌑 **DARK** • ⛰️ **EARTH** • 🌊 **WATER** • 🔥 **FIRE** • 🌪️ **WIND** • ✨ **DIVINE**",
            inline=True
        )
        embed.add_field(
            name="5. ⭐ Levels VS Ranks",
            value="• **Levels (1-12):** Stars ⭐. Determines 0/1/2 Tributes and Synchro/Ritual math.\n• **Ranks (1-13):** Black Stars ⯪. **RANKS ARE NOT LEVELS!** Overlaid Xyz materials.",
            inline=True
        )
        races_preview = ", ".join([r[0] for r in ALL_26_MONSTER_RACES[:10]]) + f", ... (+{len(ALL_26_MONSTER_RACES)-10} more)"
        embed.add_field(
            name="6. 🐉 The 26 Monster Types (Races)",
            value=f"Tribal classifications distinguishing species: *{races_preview}*",
            inline=False
        )
        embed.set_footer(text="Use /card_types [category] or the dropdown menu below to inspect each section in detail!")
        return embed

