# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.utils.domain.duel_board
Description:
    Live Yu-Gi-Oh! Duel Board State Model & Field ASCII Renderer.
    Tracks MMZ (1-5), STZ (1-5), Field Spell, GY, and Banished zones.
    Renders clean symmetrical ASCII playmat representation for Discord duels,
    and constructs the educational Master Rule field guide embed (/board).
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Any, Dict, List, Optional
import discord

# =============================================================================
# BLOCK 3: BODY BLOCK (Board Model & Field Renderers)
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
        # Graveyard, Banished, and Extra Deck piles
        self.gy: List[int] = []
        self.banished: List[int] = []
        self.extra_deck: List[int] = []

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

    # Alias for compatibility with duel engine
    place_monster = summon_monster

    def has_available_mmz(self) -> bool:
        """Returns True if at least one MMZ slot is unoccupied."""
        return any(slot is None for slot in self.mmz)

    def has_available_stz(self) -> bool:
        """Returns True if at least one STZ slot is unoccupied."""
        return any(slot is None for slot in self.stz)

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

    def change_position(self, zone_idx: int, new_position: str) -> bool:
        """Changes the battle position of a monster in the specified MMZ slot (0 to 4)."""
        if not (0 <= zone_idx < 5) or self.mmz[zone_idx] is None:
            return False
        pos = new_position.upper()
        if pos not in ("ATK", "DEF", "SET"):
            return False
        self.mmz[zone_idx]["position"] = pos
        return True

    def remove_monster(self, zone_idx: int) -> Optional[Dict[str, Any]]:
        """Removes and returns monster at specified MMZ slot (0 to 4)."""
        if 0 <= zone_idx < 5:
            m = self.mmz[zone_idx]
            self.mmz[zone_idx] = None
            return m
        return None

    def remove_spell_trap(self, zone_idx: int) -> Optional[Dict[str, Any]]:
        """Removes and returns spell/trap at specified STZ slot (0 to 4)."""
        if 0 <= zone_idx < 5:
            st = self.stz[zone_idx]
            self.stz[zone_idx] = None
            return st
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
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    "DuelBoard",
    "render_duel_field_ascii",
    "build_board_guide_embed",
]
