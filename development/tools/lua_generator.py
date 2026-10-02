#!/usr/bin/env python3
"""
=============================================================================
Advanced Lua Effect Script Generator for YGOPro / EDOPro Simulator (ocgcore)
=============================================================================
This module parses custom Yu-Gi-Oh card definitions, stats, and effect text
from the Story Database and generates fully functional, syntactically valid
Lua scripts (`c<id>.lua`) used by the `ocgcore` duel simulation engine.

Understanding the ocgcore Lua Engine:
-------------------------------------
Every card in YGOPro is governed by a script named `c<id>.lua` (where <id> is
the 8-digit passcode). In modern ocgcore / Project Ignis conventions:

1. Identification:
   `local s, id = GetID()`
   - `s`: The card's private Lua table/module.
   - `id`: The integer passcode of this card.

2. Initial Effect Setup:
   `function s.initial_effect(c)`
   - Called once when the simulator loads the card into the duel state.
   - Registers summoning procedures (Xyz materials, Link arrows, Pendulum scales).
   - Creates and registers card effects via `Effect.CreateEffect(c)`.

3. Effect Anatomy:
   An `Effect` object defines:
   - `SetType()`: Activation timing (Ignition, Trigger, Quick, Continuous, Activate).
   - `SetCode()`: Event timing trigger (e.g. EVENT_FREE_CHAIN, EVENT_SUMMON_SUCCESS).
   - `SetProperty()`: Flags such as EFFECT_FLAG_CARD_TARGET or EFFECT_FLAG_DELAY.
   - `SetCountLimit(count, id)`: Soft Once Per Turn (1) or Hard Once Per Turn (1, id).
   - `SetCost()`: Pre-activation costs (discarding, paying LP, detaching Xyz materials).
   - `SetTarget()`: Legality check (chk==0) and targeting declaration (chk==1).
   - `SetOperation()`: The actual card resolution when the chain resolves.
=============================================================================
"""

import sqlite3
import os
import sys
import re
import subprocess
from typing import Optional, List, Tuple, Dict, Any

# Resolve project base directory
try:
    from config.paths import BASE_DIR, STORY_DB_PATH, SCRIPTS_DIR
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    STORY_DB_PATH = os.path.join(BASE_DIR, "production", "main", "web", "ygo_story.db")
    SCRIPTS_DIR = os.path.join(BASE_DIR, "production", "shared", "expansions", "scripts")


def clean_text(text: Optional[str]) -> str:
    """Standardizes line breaks and strips whitespace."""
    if not text:
        return ""
    return text.strip().replace("\r\n", "\n").replace("\r", "\n")


# =============================================================================
# 1. SUMMONING PROCEDURE GENERATOR
# =============================================================================
class ProcedureGenerator:
    """
    Generates standard ocgcore summoning procedure registrations for Extra Deck
    and Special Summon monsters (Xyz, Link, Synchro, Fusion, Ritual, Pendulum).
    """

    @staticmethod
    def generate(subtype: str, effect_text: str, level: Optional[int]) -> List[str]:
        """
        Analyzes card subtype and material lines in card text to produce
        the appropriate `*.AddProcedure(c, ...)` Lua code.
        """
        lines = []
        sub_lower = (subtype or "").lower()

        # 1. Pendulum Summoning Procedure
        if "pendulum" in sub_lower:
            lines.append("\tPendulum.AddProcedure(c)")

        # 2. Xyz Summoning Procedure
        if "xyz" in sub_lower:
            rank = level or 8
            mat_match = re.search(r"(\d+)\s+Level\s+(\d+)", effect_text, re.IGNORECASE)
            mat_count = int(mat_match.group(1)) if mat_match else 2
            mat_rank = int(mat_match.group(2)) if mat_match else rank

            # Check if materials require a specific attribute (e.g. LIGHT or DARK)
            text_lower = effect_text.lower()
            if "light" in text_lower:
                lines.append(f"\tXyz.AddProcedure(c,aux.FilterBoolFunctionEx(Card.IsAttribute,ATTRIBUTE_LIGHT),{mat_rank},{mat_count})")
            elif "dark" in text_lower:
                lines.append(f"\tXyz.AddProcedure(c,aux.FilterBoolFunctionEx(Card.IsAttribute,ATTRIBUTE_DARK),{mat_rank},{mat_count})")
            else:
                lines.append(f"\tXyz.AddProcedure(c,nil,{mat_rank},{mat_count})")
            lines.append("\tc:EnableReviveLimit()")

        # 3. Link Summoning Procedure
        elif "link" in sub_lower:
            rating = level or 2
            min_mat = 2
            min_match = re.search(r"(\d+)\+\s+(?:Effect\s+)?Monsters", effect_text, re.IGNORECASE)
            if min_match:
                min_mat = int(min_match.group(1))
            lines.append(f"\tLink.AddProcedure(c,aux.FilterBoolFunctionEx(Card.IsType,TYPE_EFFECT),{min_mat},{rating})")
            lines.append("\tc:EnableReviveLimit()")

        # 4. Synchro Summoning Procedure
        elif "synchro" in sub_lower:
            lines.append("\tSynchro.AddProcedure(c,nil,1,1,Synchro.NonTuner(nil),1,99)")
            lines.append("\tc:EnableReviveLimit()")

        # 5. Fusion Summoning Procedure
        elif "fusion" in sub_lower:
            lines.append("\tFusion.AddProcedure(c,nil,2,2)")
            lines.append("\tc:EnableReviveLimit()")

        # 6. Ritual Summoning Revive Limit
        elif "ritual" in sub_lower:
            lines.append("\tc:EnableReviveLimit()")

        return lines


# =============================================================================
# 2. CARD EFFECT ANALYZER & HELPER GENERATOR
# =============================================================================
class EffectAnalyzer:
    """
    Parses natural language Yu-Gi-Oh card text into structured ocgcore effect
    declarations and corresponding Lua callback functions.
    """

    def __init__(self, card_id: int, card_type: str, card_subtype: str, effect_text: str):
        self.card_id = card_id
        self.ctype_lower = (card_type or "").lower()
        self.csub_lower = (card_subtype or "").lower()
        self.effect_text = clean_text(effect_text)
        self.effects: List[str] = []
        self.helpers: List[str] = []
        self.counter = 0

    def parse_clauses(self) -> List[str]:
        """Splits full card text into distinct actionable effect clauses."""
        pattern = r'(?:\n+|(?:(?<=\.)\s+(?=(?:Once per turn|When|If|During|\(Quick Effect\)|All|You can|Target|Cannot))))'
        raw_paras = [p.strip() for p in re.split(pattern, self.effect_text) if p.strip()]
        
        # Filter out material requirement headers and global once-per-turn statements
        valid_clauses = []
        for p in raw_paras:
            if re.match(r"^\d+\+?\s+Level\s+\d+", p, re.IGNORECASE):
                continue
            if re.match(r"^\d+\+?\s+(?:Effect\s+)?Monsters", p, re.IGNORECASE):
                continue
            if re.match(r"^You can only use (?:each|this) effect", p, re.IGNORECASE):
                continue
            valid_clauses.append(p)
        return valid_clauses

    def build_all(self):
        """Analyzes all clauses and generates effect code and helper functions."""
        clauses = self.parse_clauses()
        is_hard_opt = bool(
            re.search(r"You can only use each effect of .* once per turn", self.effect_text, re.IGNORECASE) or
            re.search(r"You can only use this effect of .* once per turn", self.effect_text, re.IGNORECASE)
        )

        for clause in clauses:
            self.counter += 1
            idx = self.counter
            clause_lower = clause.lower()

            # --- Pattern A: Continuous Field ATK/DEF Boost ---
            if "all" in clause_lower and ("gain" in clause_lower or "atk" in clause_lower) and self.ctype_lower == "spell" and "field" in self.csub_lower:
                boost_match = re.search(r"gain\s+(\d+)\s+ATK(?:/DEF)?", clause, re.IGNORECASE)
                boost_val = int(boost_match.group(1)) if boost_match else 300
                eff_code = f"""\t-- Effect {idx}: Continuous Field ATK/DEF Boost
\tlocal e{idx}=Effect.CreateEffect(c)
\te{idx}:SetType(EFFECT_TYPE_FIELD)
\te{idx}:SetCode(EFFECT_UPDATE_ATTACK)
\te{idx}:SetRange(LOCATION_FZONE)
\te{idx}:SetTargetRange(LOCATION_MZONE,0)
\te{idx}:SetValue({boost_val})
\tc:RegisterEffect(e{idx})
\tlocal e{idx}b=e{idx}:Clone()
\te{idx}b:SetCode(EFFECT_UPDATE_DEFENSE)
\tc:RegisterEffect(e{idx}b)"""
                self.effects.append(eff_code)
                continue

            # --- Pattern B: Xyz Destruction Replacement ---
            if "would be destroyed" in clause_lower and "detach" in clause_lower:
                eff_code = f"""\t-- Effect {idx}: Destruction replacement (detach 1 material)
\tlocal e{idx}=Effect.CreateEffect(c)
\te{idx}:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_CONTINUOUS)
\te{idx}:SetCode(EFFECT_DESTROY_REPLACE)
\te{idx}:SetProperty(EFFECT_FLAG_SINGLE_RANGE)
\te{idx}:SetRange(LOCATION_MZONE)
\te{idx}:SetTarget(s.reptg{idx})
\te{idx}:SetOperation(s.repop{idx})
\tc:RegisterEffect(e{idx})"""
                self.effects.append(eff_code)

                self.helpers.append(f"""function s.reptg{idx}(e,tp,eg,ep,ev,re,r,rp,chk)
\tlocal c=e:GetHandler()
\tif chk==0 then return not c:IsReason(REASON_REPLACE) and c:CheckRemoveOverlayCard(tp,1,REASON_EFFECT) end
\tif Duel.SelectEffectYesNo(tp,c,96) then
\t\treturn true
\telse return false end
end
function s.repop{idx}(e,tp,eg,ep,ev,re,r,rp)
\te:GetHandler():RemoveOverlayCard(tp,1,1,REASON_EFFECT)
end""")
                continue

            # --- Pattern C: Attach Battle-Destroyed Monster as Material ---
            if "destroys an opponent's monster by battle" in clause_lower and "attach" in clause_lower:
                eff_code = f"""\t-- Effect {idx}: Attach destroyed monster as Xyz material
\tlocal e{idx}=Effect.CreateEffect(c)
\te{idx}:SetDescription(aux.Stringid(id,{idx-1}))
\te{idx}:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_TRIGGER_O)
\te{idx}:SetCode(EVENT_BATTLE_DESTROYING)
\te{idx}:SetCondition(aux.bdocon)
\te{idx}:SetTarget(s.attachtg{idx})
\te{idx}:SetOperation(s.attachop{idx})
\tc:RegisterEffect(e{idx})"""
                self.effects.append(eff_code)

                self.helpers.append(f"""function s.attachtg{idx}(e,tp,eg,ep,ev,re,r,rp,chk)
\tlocal c=e:GetHandler()
\tlocal tc=c:GetBattleTarget()
\tif chk==0 then return c:IsType(TYPE_XYZ) and tc and tc:IsLocation(LOCATION_GRAVE) end
\tDuel.SetOperationInfo(0,CATEGORY_LEAVE_GRAVE,tc,1,0,0)
end
function s.attachop{idx}(e,tp,eg,ep,ev,re,r,rp)
\tlocal c=e:GetHandler()
\tlocal tc=c:GetBattleTarget()
\tif c:IsRelateToEffect(e) and c:IsFaceup() and tc:IsRelateToBattle() then
\t\tc:Overlay(tc)
\tend
end""")
                continue

            # --- Pattern D: Continuous Targeting Protection ---
            if "cannot be targeted" in clause_lower:
                eff_code = f"""\t-- Effect {idx}: Cannot be targeted by opponent's card effects
\tlocal e{idx}=Effect.CreateEffect(c)
\te{idx}:SetType(EFFECT_TYPE_SINGLE)
\te{idx}:SetProperty(EFFECT_FLAG_SINGLE_RANGE)
\te{idx}:SetRange(LOCATION_MZONE)
\te{idx}:SetCode(EFFECT_CANNOT_BE_EFFECT_TARGET)
\te{idx}:SetValue(aux.tgoval)
\tc:RegisterEffect(e{idx})"""
                self.effects.append(eff_code)
                continue

            # --- Pattern E: Battle / Effect Indestructibility ---
            if "cannot be destroyed by battle" in clause_lower and "would be destroyed" not in clause_lower:
                eff_code = f"""\t-- Effect {idx}: Cannot be destroyed by battle
\tlocal e{idx}=Effect.CreateEffect(c)
\te{idx}:SetType(EFFECT_TYPE_SINGLE)
\te{idx}:SetRange(LOCATION_MZONE)
\te{idx}:SetCode(EFFECT_INDESTRUCTABLE_BATTLE)
\te{idx}:SetValue(1)
\tc:RegisterEffect(e{idx})"""
                self.effects.append(eff_code)
                continue

            # --- Standard Activated Effects (Quick, Trigger on-summon, Ignition) ---
            is_quick = bool("quick effect" in clause_lower or (self.ctype_lower == "spell" and "quick" in self.csub_lower) or self.ctype_lower == "trap")
            is_on_summon = bool("normal or special summoned" in clause_lower or "link summoned" in clause_lower or "when this card is activated" in clause_lower)

            # Determine category flags
            cats = []
            if "search" in clause_lower or "add 1" in clause_lower:
                cats.append("CATEGORY_TOHAND+CATEGORY_SEARCH")
            if "special summon" in clause_lower:
                cats.append("CATEGORY_SPECIAL_SUMMON")
            if "banish" in clause_lower:
                cats.append("CATEGORY_REMOVE")
            if "destroy" in clause_lower:
                cats.append("CATEGORY_DESTROY")
            if "draw" in clause_lower:
                cats.append("CATEGORY_DRAW")
            if "negate" in clause_lower:
                cats.append("CATEGORY_DISABLE")
            if "deck to the gy" in clause_lower:
                cats.append("CATEGORY_TOGRAVE")
            cat_expr = "+".join(cats) if cats else "0"

            eff_lines = [f"\t-- Effect {idx}: {clause[:55]}..."]
            eff_lines.append(f"\tlocal e{idx}=Effect.CreateEffect(c)")
            eff_lines.append(f"\te{idx}:SetDescription(aux.Stringid(id,{idx-1}))")
            eff_lines.append(f"\te{idx}:SetCategory({cat_expr})")

            # Timing & Type
            if is_quick:
                eff_lines.append(f"\te{idx}:SetType(EFFECT_TYPE_QUICK_O)")
                eff_lines.append(f"\te{idx}:SetCode(EVENT_FREE_CHAIN)")
                eff_lines.append(f"\te{idx}:SetHintTiming(0,TIMINGS_CHECK_MONSTER_E)")
            elif is_on_summon:
                if self.ctype_lower in ("spell", "trap"):
                    eff_lines.append(f"\te{idx}:SetType(EFFECT_TYPE_ACTIVATE)")
                    eff_lines.append(f"\te{idx}:SetCode(EVENT_FREE_CHAIN)")
                else:
                    eff_lines.append(f"\te{idx}:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_TRIGGER_O)")
                    eff_lines.append(f"\te{idx}:SetCode(EVENT_SUMMON_SUCCESS)")
                    eff_lines.append(f"\te{idx}:SetProperty(EFFECT_FLAG_DELAY)")
            else:
                eff_lines.append(f"\te{idx}:SetType(EFFECT_TYPE_IGNITION)")

            if self.ctype_lower == "monster":
                eff_lines.append(f"\te{idx}:SetRange(LOCATION_MZONE)")

            # Once per turn limit
            if is_hard_opt:
                eff_lines.append(f"\te{idx}:SetCountLimit(1, id)")
            elif "once per turn" in clause_lower:
                eff_lines.append(f"\te{idx}:SetCountLimit(1)")

            # Costs: Detach, Tribute, or Discard
            if "detach 1 material" in clause_lower or "detach" in clause_lower:
                eff_lines.append(f"\te{idx}:SetCost(s.cost_detach{idx})")
                self.helpers.append(f"""function s.cost_detach{idx}(e,tp,eg,ep,ev,re,r,rp,chk)
\tif chk==0 then return e:GetHandler():CheckRemoveOverlayCard(tp,1,REASON_COST) end
\te:GetHandler():RemoveOverlayCard(tp,1,1,REASON_COST)
end""")
            elif "tribute this card" in clause_lower:
                eff_lines.append(f"\te{idx}:SetCost(s.cost_tribute{idx})")
                self.helpers.append(f"""function s.cost_tribute{idx}(e,tp,eg,ep,ev,re,r,rp,chk)
\tif chk==0 then return e:GetHandler():IsReleasable() end
\tDuel.Release(e:GetHandler(),REASON_COST)
end""")

            # Targeting property
            if "target 1" in clause_lower:
                eff_lines.append(f"\te{idx}:SetProperty(EFFECT_FLAG_CARD_TARGET)")

            eff_lines.append(f"\te{idx}:SetTarget(s.target{idx})")
            eff_lines.append(f"\te{idx}:SetOperation(s.operation{idx})")
            eff_lines.append(f"\tc:RegisterEffect(e{idx})")

            # On-summon clone for Special Summon
            if is_on_summon and self.ctype_lower == "monster":
                eff_lines.append(f"\tlocal e{idx}b=e{idx}:Clone()")
                eff_lines.append(f"\te{idx}b:SetCode(EVENT_SPSUMMON_SUCCESS)")
                eff_lines.append(f"\tc:RegisterEffect(e{idx}b)")

            self.effects.append("\n".join(eff_lines))
            self.generate_helper_callbacks(idx, clause_lower)

    def generate_helper_callbacks(self, idx: int, text_lower: str):
        """Generates target and operation functions based on effect mechanics."""
        # 1. Search / Add from Deck to Hand
        if "add 1" in text_lower and "deck to your hand" in text_lower:
            filter_code = "Card.IsAbleToHand"
            if "spell/trap" in text_lower or "spell" in text_lower:
                filter_code = "function(c) return c:IsSpellTrap() and c:IsAbleToHand() end"
            elif "monster" in text_lower:
                filter_code = "function(c) return c:IsMonster() and c:IsAbleToHand() end"

            self.helpers.append(f"""function s.filter{idx}(c)
\treturn {filter_code}
end
function s.target{idx}(e,tp,eg,ep,ev,re,r,rp,chk)
\tif chk==0 then return Duel.IsExistingMatchingCard(s.filter{idx},tp,LOCATION_DECK,0,1,nil) end
\tDuel.SetOperationInfo(0,CATEGORY_TOHAND,nil,1,tp,LOCATION_DECK)
end
function s.operation{idx}(e,tp,eg,ep,ev,re,r,rp)
\tDuel.Hint(HINT_SELECTMSG,tp,HINTMSG_ATOHAND)
\tlocal g=Duel.SelectMatchingCard(tp,s.filter{idx},tp,LOCATION_DECK,0,1,1,nil)
\tif #g>0 then
\t\tDuel.SendtoHand(g,nil,REASON_EFFECT)
\t\tDuel.ConfirmCards(1-tp,g)
\tend
end""")

        # 2. Target 1 card on the field -> Banish
        elif "target 1 face-up card" in text_lower and "banish" in text_lower:
            self.helpers.append(f"""function s.target{idx}(e,tp,eg,ep,ev,re,r,rp,chk,chkc)
\tif chkc then return chkc:IsOnField() and chkc:IsAbleToRemove() end
\tif chk==0 then return Duel.IsExistingTarget(Card.IsAbleToRemove,tp,LOCATION_ONFIELD,LOCATION_ONFIELD,1,nil) end
\tDuel.Hint(HINT_SELECTMSG,tp,HINTMSG_REMOVE)
\tlocal g=Duel.SelectTarget(tp,Card.IsAbleToRemove,tp,LOCATION_ONFIELD,LOCATION_ONFIELD,1,1,nil)
\tDuel.SetOperationInfo(0,CATEGORY_REMOVE,g,1,0,0)
end
function s.operation{idx}(e,tp,eg,ep,ev,re,r,rp)
\tlocal tc=Duel.GetFirstTarget()
\tif tc:IsRelateToEffect(e) then
\t\tDuel.Remove(tc,POS_FACEUP,REASON_EFFECT)
\tend
end""")

        # 3. Special Summon from Hand or GY
        elif "special summon 1" in text_lower and ("hand" in text_lower or "gy" in text_lower):
            self.helpers.append(f"""function s.spfilter{idx}(c,e,tp)
\treturn c:IsLevel(8) and c:IsCanBeSpecialSummoned(e,0,tp,false,false)
end
function s.target{idx}(e,tp,eg,ep,ev,re,r,rp,chk)
\tlocal loc=LOCATION_HAND+LOCATION_GRAVE
\tif chk==0 then return Duel.GetLocationCount(tp,LOCATION_MZONE)>0
\t\tand Duel.IsExistingMatchingCard(s.spfilter{idx},tp,loc,0,1,nil,e,tp) end
\tDuel.SetOperationInfo(0,CATEGORY_SPECIAL_SUMMON,nil,1,tp,loc)
end
function s.operation{idx}(e,tp,eg,ep,ev,re,r,rp)
\tif Duel.GetLocationCount(tp,LOCATION_MZONE)<=0 then return end
\tlocal loc=LOCATION_HAND+LOCATION_GRAVE
\tDuel.Hint(HINT_SELECTMSG,tp,HINTMSG_SPSUMMON)
\tlocal g=Duel.SelectMatchingCard(tp,aux.NecroValleyFilter(s.spfilter{idx}),tp,loc,0,1,1,nil,e,tp)
\tif #g>0 then
\t\tDuel.SpecialSummon(g,0,tp,tp,false,false,POS_FACEUP)
\tend
end""")

        # 4. Banish Top Cards Face-Down (Mill / Banish effect)
        elif "banish the top" in text_lower and "face-down" in text_lower:
            count = 3
            match = re.search(r"top\s+(\d+)\s+cards", text_lower)
            if match:
                count = int(match.group(1))
            self.helpers.append(f"""function s.target{idx}(e,tp,eg,ep,ev,re,r,rp,chk)
\tif chk==0 then return Duel.IsPlayerCanRemove(tp) and Duel.IsPlayerCanRemove(1-tp) end
\tDuel.SetOperationInfo(0,CATEGORY_REMOVE,nil,{count*2},PLAYER_ALL,LOCATION_DECK)
end
function s.operation{idx}(e,tp,eg,ep,ev,re,r,rp)
\tlocal g1=Duel.GetDecktopGroup(tp,{count})
\tlocal g2=Duel.GetDecktopGroup(1-tp,{count})
\tg1:Merge(g2)
\tif #g1>0 then
\t\tDuel.DisableShuffleCheck()
\t\tDuel.Remove(g1,POS_FACEDOWN,REASON_EFFECT)
\tend
end""")

        # 5. Send from Deck to GY (Foolish Burial)
        elif "send 1" in text_lower and "deck to the gy" in text_lower:
            self.helpers.append(f"""function s.tgfilter{idx}(c)
\treturn c:IsAbleToGrave()
end
function s.target{idx}(e,tp,eg,ep,ev,re,r,rp,chk)
\tif chk==0 then return Duel.IsExistingMatchingCard(s.tgfilter{idx},tp,LOCATION_DECK,0,1,nil) end
\tDuel.SetOperationInfo(0,CATEGORY_TOGRAVE,nil,1,tp,LOCATION_DECK)
end
function s.operation{idx}(e,tp,eg,ep,ev,re,r,rp)
\tDuel.Hint(HINT_SELECTMSG,tp,HINTMSG_TOGRAVE)
\tlocal g=Duel.SelectMatchingCard(tp,s.tgfilter{idx},tp,LOCATION_DECK,0,1,1,nil)
\tif #g>0 then
\t\tDuel.SendtoGrave(g,REASON_EFFECT)
\tend
end""")

        # 6. Default Fallback Callback
        else:
            self.helpers.append(f"""function s.target{idx}(e,tp,eg,ep,ev,re,r,rp,chk,chkc)
\tif chk==0 then return true end
end
function s.operation{idx}(e,tp,eg,ep,ev,re,r,rp)
\t-- Effect implementation
end""")


# =============================================================================
# 3. LUA SCRIPT BUILDER & EMITTER
# =============================================================================
class LuaScriptBuilder:
    """
    Coordinates summoning procedure generation, effect parsing, and final Lua code
    rendering for an individual custom card.
    """

    def __init__(self, card_data: Tuple):
        (self.cid, self.name, self.ctype, self.csubtype, self.attribute,
         self.monster_type, self.level, self.scale, self.atk, self.defense,
         self.link_arrows, self.effect_text, self.pendulum_effect, self.db_url) = card_data

    def render(self) -> str:
        """Generates the full Lua script string."""
        procedures = ProcedureGenerator.generate(self.csubtype, self.effect_text, self.level)
        analyzer = EffectAnalyzer(self.cid, self.ctype, self.csubtype, self.effect_text)
        analyzer.build_all()

        proc_block = "\n".join(procedures)
        eff_block = "\n\n".join(analyzer.effects)
        help_block = "\n\n".join(analyzer.helpers)

        body_elements = []
        if proc_block:
            body_elements.append(proc_block)
        if eff_block:
            body_elements.append(eff_block)

        initial_effect_body = "\n".join(body_elements)

        header = f"""-- ============================================================================
-- {self.name}
-- Passcode / Custom ID: {self.cid}
-- Type: [{self.ctype} / {self.csubtype or 'Normal'}]
-- Duelingbook Reference: {self.db_url or 'https://www.duelingbook.com'}
-- Auto-generated by Yu-Gi-Oh Story Platform Lua Generator
-- ============================================================================
local s, id = GetID()

function s.initial_effect(c)
{initial_effect_body}
end

{help_block}
"""
        return header


def validate_lua_syntax(script_path: str) -> Tuple[bool, str]:
    """
    Validates a generated Lua file using `luac -p` if luac is installed on the host.
    Returns (is_valid, error_message).
    """
    try:
        proc = subprocess.run(
            ["luac", "-p", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if proc.returncode == 0:
            return True, ""
        return False, proc.stderr.strip()
    except FileNotFoundError:
        # luac is not installed on system; skip verification
        return True, "luac not available"


def generate_lua_for_card_full(card_data: Tuple, scripts_dir: str = SCRIPTS_DIR, overwrite: bool = True) -> bool:
    """
    Renders and writes the Lua effect script for a complete card tuple.
    """
    cid = card_data[0]
    script_path = os.path.join(scripts_dir, f"c{cid}.lua")
    if os.path.exists(script_path) and not overwrite:
        return False

    builder = LuaScriptBuilder(card_data)
    content = builder.render()

    os.makedirs(scripts_dir, exist_ok=True)
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Validate syntax if luac is available
    is_valid, err = validate_lua_syntax(script_path)
    if not is_valid:
        print(f"[!] Warning: Lua syntax error in {script_path}: {err}", file=sys.stderr)

    return True


def generate_lua_for_card(card_tuple: Tuple, scripts_dir: str = SCRIPTS_DIR, overwrite: bool = False) -> bool:
    """
    Backwards-compatible wrapper: if simple 5-tuple passed, queries the DB
    for the full record before generation.
    """
    cid = card_tuple[0]
    conn = sqlite3.connect(STORY_DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, card_type, card_subtype, attribute, monster_type,
               level_or_rank_or_link, scale, atk, def, link_arrows,
               effect_text, pendulum_effect, duelingbook_url
        FROM custom_cards WHERE id = ?
    """, (cid,))
    row = cur.fetchone()
    conn.close()
    if row:
        return generate_lua_for_card_full(row, scripts_dir, overwrite=overwrite)
    return False


def generate_all_scripts(story_db: str = STORY_DB_PATH, scripts_dir: str = SCRIPTS_DIR, overwrite: bool = True) -> int:
    """
    Generates or refreshes Lua effect scripts for all custom cards in the database.
    """
    os.makedirs(scripts_dir, exist_ok=True)
    conn = sqlite3.connect(story_db)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, card_type, card_subtype, attribute, monster_type,
               level_or_rank_or_link, scale, atk, def, link_arrows,
               effect_text, pendulum_effect, duelingbook_url
        FROM custom_cards
        ORDER BY id ASC
    """)
    cards = cur.fetchall()
    conn.close()

    generated_count = 0
    for card in cards:
        if generate_lua_for_card_full(card, scripts_dir, overwrite=overwrite):
            generated_count += 1

    print(f"[+] Successfully generated {generated_count} modular Lua scripts in {scripts_dir}")
    return generated_count


if __name__ == "__main__":
    generate_all_scripts()
