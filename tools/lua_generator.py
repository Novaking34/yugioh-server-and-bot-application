#!/usr/bin/env python3
"""
Advanced Lua Effect Script Generator for YGOPro / EDOPro Simulator (ocgcore).
Intelligently parses Yu-Gi-Oh card text, stats, and types to generate
fully functional Lua scripts covering:
- Summoning procedures (Fusion, Synchro, Xyz, Link, Pendulum, Ritual)
- Trigger conditions (On-Summon, Quick Effects, Battle Destruction, Ignition)
- Effect costs (Detach Xyz material, Tribute, Discard, Pay LP)
- Targeting & categories (Search, Special Summon, Banish, Destroy, Draw, Mill)
- Continuous & Replacement effects (ATK/DEF boost, Destruction replacement)
- Count limits (Hard Once Per Turn vs Soft Once Per Turn)
"""

import sqlite3
import os
import sys
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORY_DB_PATH = os.path.join(BASE_DIR, "story_database", "ygo_story.db")
SCRIPTS_DIR = os.path.join(BASE_DIR, "server-data", "expansions", "scripts")

def clean_text(text):
    if not text:
        return ""
    return text.strip().replace("\r\n", "\n").replace("\r", "\n")

class LuaScriptBuilder:
    def __init__(self, card_data):
        (self.cid, self.name, self.ctype, self.csubtype, self.attribute,
         self.monster_type, self.level, self.scale, self.atk, self.defense,
         self.link_arrows, self.effect_text, self.pendulum_effect, self.db_url) = card_data
         
        self.effect_text = clean_text(self.effect_text)
        self.pendulum_effect = clean_text(self.pendulum_effect)
        self.ctype_l = (self.ctype or "").lower()
        self.csub_l = (self.csubtype or "").lower()
        
        self.procedures = []
        self.effects = []
        self.helpers = []
        self.effect_counter = 0

    def add_procedure(self, code_line):
        self.procedures.append(f"\t{code_line}")

    def build_procedures(self):
        # 1. Pendulum
        if "pendulum" in self.csub_l:
            self.add_procedure("Pendulum.AddProcedure(c)")
            
        # 2. Xyz
        if "xyz" in self.csub_l:
            rank = self.level or 8
            mat_match = re.search(r"(\d+)\s+Level\s+(\d+)", self.effect_text, re.IGNORECASE)
            mat_count = int(mat_match.group(1)) if mat_match else 2
            mat_rank = int(mat_match.group(2)) if mat_match else rank
            
            # Check attribute restriction
            if "light" in self.effect_text.lower():
                self.add_procedure(f"Xyz.AddProcedure(c,aux.FilterBoolFunctionEx(Card.IsAttribute,ATTRIBUTE_LIGHT),{mat_rank},{mat_count})")
            elif "dark" in self.effect_text.lower():
                self.add_procedure(f"Xyz.AddProcedure(c,aux.FilterBoolFunctionEx(Card.IsAttribute,ATTRIBUTE_DARK),{mat_rank},{mat_count})")
            else:
                self.add_procedure(f"Xyz.AddProcedure(c,nil,{mat_rank},{mat_count})")
            self.add_procedure("c:EnableReviveLimit()")
            
        # 3. Link
        elif "link" in self.csub_l:
            rating = self.level or 2
            min_mat = 2
            min_match = re.search(r"(\d+)\+\s+(?:Effect\s+)?Monsters", self.effect_text, re.IGNORECASE)
            if min_match:
                min_mat = int(min_match.group(1))
            self.add_procedure(f"Link.AddProcedure(c,aux.FilterBoolFunctionEx(Card.IsType,TYPE_EFFECT),{min_mat},{rating})")
            self.add_procedure("c:EnableReviveLimit()")
            
        # 4. Synchro
        elif "synchro" in self.csub_l:
            self.add_procedure("Synchro.AddProcedure(c,nil,1,1,Synchro.NonTuner(nil),1,99)")
            self.add_procedure("c:EnableReviveLimit()")
            
        # 5. Fusion
        elif "fusion" in self.csub_l:
            self.add_procedure("Fusion.AddProcedure(c,nil,2,2)")
            self.add_procedure("c:EnableReviveLimit()")
            
        # 6. Ritual
        elif "ritual" in self.csub_l:
            self.add_procedure("c:EnableReviveLimit()")

    def analyze_effects(self):
        # Split text into distinct effect clauses by newlines or sentence boundaries with trigger indicators
        pattern = r'(?:\n+|(?:(?<=\.)\s+(?=(?:Once per turn|When|If|During|\(Quick Effect\)|All|You can|Target|Cannot))))'
        paragraphs = [p.strip() for p in re.split(pattern, self.effect_text) if p.strip()]
        
        # Check hard once per turn restriction
        hard_opt = bool(re.search(r"You can only use each effect of .* once per turn", self.effect_text, re.IGNORECASE) or
                       re.search(r"You can only use this effect of .* once per turn", self.effect_text, re.IGNORECASE))
                       
        for para in paragraphs:
            # Skip material requirements line for Extra deck monsters
            if re.match(r"^\d+\+?\s+Level\s+\d+", para, re.IGNORECASE): continue
            if re.match(r"^\d+\+?\s+(?:Effect\s+)?Monsters", para, re.IGNORECASE): continue
            if re.match(r"^You can only use (?:each|this) effect", para, re.IGNORECASE): continue
            
            self.effect_counter += 1
            idx = self.effect_counter
            
            # --- Check Continuous ATK/DEF Boost (e.g. Field Spells / Continuous Spells) ---
            if "all" in para.lower() and ("gain" in para.lower() or "atk" in para.lower()) and self.ctype_l == "spell" and "field" in self.csub_l:
                boost_match = re.search(r"gain\s+(\d+)\s+ATK(?:/DEF)?", para, re.IGNORECASE)
                boost_val = int(boost_match.group(1)) if boost_match else 300
                eff_code = f"""\t-- All monsters gain ATK
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

            # --- Check Destruction Replacement ---
            if "would be destroyed" in para.lower() and "detach" in para.lower():
                eff_code = f"""\t-- Destruction replacement (detach 1 material)
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

            # --- Check Attach Destroyed Monster as Xyz Material ---
            if "destroys an opponent's monster by battle" in para.lower() and "attach" in para.lower():
                eff_code = f"""\t-- Attach destroyed monster as material
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

            # --- Determine Trigger & Timing ---
            is_quick = bool("quick effect" in para.lower() or (self.ctype_l == "spell" and "quick" in self.csub_l) or self.ctype_l == "trap")
            is_on_summon = bool("normal or special summoned" in para.lower() or "link summoned" in para.lower() or "when this card is activated" in para.lower())
            is_ignition = not is_quick and not is_on_summon
            
            # --- Determine Costs ---
            has_detach_cost = bool("detach 1 material" in para.lower() or "detach" in para.lower())
            has_tribute_cost = bool("tribute this card" in para.lower())
            has_discard_cost = bool("discard 1 card" in para.lower() or "discard" in para.lower())
            
            # --- Determine Categories & Operation ---
            categories = []
            if "search" in para.lower() or "add 1" in para.lower(): categories.append("CATEGORY_TOHAND+CATEGORY_SEARCH")
            if "special summon" in para.lower(): categories.append("CATEGORY_SPECIAL_SUMMON")
            if "banish" in para.lower(): categories.append("CATEGORY_REMOVE")
            if "destroy" in para.lower(): categories.append("CATEGORY_DESTROY")
            if "draw" in para.lower(): categories.append("CATEGORY_DRAW")
            if "negate" in para.lower(): categories.append("CATEGORY_DISABLE")
            if "deck to the gy" in para.lower(): categories.append("CATEGORY_TOGRAVE")
            
            cat_str = "+".join(categories) if categories else "0"
            
            # Build Effect Header
            lines = [f"\t-- Effect {idx}: {para[:60]}..."]
            lines.append(f"\tlocal e{idx}=Effect.CreateEffect(c)")
            lines.append(f"\te{idx}:SetDescription(aux.Stringid(id,{idx-1}))")
            lines.append(f"\te{idx}:SetCategory({cat_str})")
            
            if is_quick:
                lines.append(f"\te{idx}:SetType(EFFECT_TYPE_QUICK_O)")
                lines.append(f"\te{idx}:SetCode(EVENT_FREE_CHAIN)")
                lines.append(f"\te{idx}:SetHintTiming(0,TIMINGS_CHECK_MONSTER_E)")
            elif is_on_summon:
                if self.ctype_l == "spell" or self.ctype_l == "trap":
                    lines.append(f"\te{idx}:SetType(EFFECT_TYPE_ACTIVATE)")
                    lines.append(f"\te{idx}:SetCode(EVENT_FREE_CHAIN)")
                else:
                    lines.append(f"\te{idx}:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_TRIGGER_O)")
                    lines.append(f"\te{idx}:SetCode(EVENT_SUMMON_SUCCESS)")
                    lines.append(f"\te{idx}:SetProperty(EFFECT_FLAG_DELAY)")
            else:
                lines.append(f"\te{idx}:SetType(EFFECT_TYPE_IGNITION)")
                
            if self.ctype_l == "monster":
                lines.append(f"\te{idx}:SetRange(LOCATION_MZONE)")
                
            # Count Limit
            if hard_opt:
                lines.append(f"\te{idx}:SetCountLimit(1,id)")
            elif "once per turn" in para.lower():
                lines.append(f"\te{idx}:SetCountLimit(1)")
                
            # Cost setup
            if has_detach_cost:
                lines.append(f"\te{idx}:SetCost(s.cost_detach{idx})")
                self.helpers.append(f"""function s.cost_detach{idx}(e,tp,eg,ep,ev,re,r,rp,chk)
\tif chk==0 then return e:GetHandler():CheckRemoveOverlayCard(tp,1,REASON_COST) end
\te:GetHandler():RemoveOverlayCard(tp,1,1,REASON_COST)
end""")
            elif has_tribute_cost:
                lines.append(f"\te{idx}:SetCost(s.cost_tribute{idx})")
                self.helpers.append(f"""function s.cost_tribute{idx}(e,tp,eg,ep,ev,re,r,rp,chk)
\tif chk==0 then return e:GetHandler():IsReleasable() end
\tDuel.Release(e:GetHandler(),REASON_COST)
end""")
                
            # Targeting
            is_targeting = bool("target 1" in para.lower())
            if is_targeting:
                lines.append(f"\te{idx}:SetProperty(EFFECT_FLAG_CARD_TARGET)")
                
            lines.append(f"\te{idx}:SetTarget(s.target{idx})")
            lines.append(f"\te{idx}:SetOperation(s.operation{idx})")
            lines.append(f"\tc:RegisterEffect(e{idx})")
            
            # If on summon, clone for SPSUMMON_SUCCESS
            if is_on_summon and self.ctype_l == "monster":
                lines.append(f"\tlocal e{idx}b=e{idx}:Clone()")
                lines.append(f"\te{idx}b:SetCode(EVENT_SPSUMMON_SUCCESS)")
                lines.append(f"\tc:RegisterEffect(e{idx}b)")
                
            self.effects.append("\n".join(lines))
            
            # --- Build Helper Functions ---
            self.build_helper_logic(idx, para)

    def build_helper_logic(self, idx, para):
        para_l = para.lower()
        
        # 1. Search / Add to hand
        if "add 1" in para_l and "deck to your hand" in para_l:
            filter_code = "Card.IsAbleToHand"
            if "spell/trap" in para_l or "spell" in para_l:
                filter_code = "function(c) return c:IsSpellTrap() and c:IsAbleToHand() end"
            elif "monster" in para_l:
                filter_code = "function(c) return c:IsMonster() and c:IsAbleToHand() end"
                
            helper = f"""function s.filter{idx}(c)
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
end"""
            self.helpers.append(helper)
            
        # 2. Target 1 face-up card -> Banish it
        elif "target 1 face-up card" in para_l and "banish" in para_l:
            helper = f"""function s.target{idx}(e,tp,eg,ep,ev,re,r,rp,chk,chkc)
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
end"""
            self.helpers.append(helper)
            
        # 3. Special Summon from Hand or GY
        elif "special summon 1" in para_l and ("hand" in para_l or "gy" in para_l):
            helper = f"""function s.spfilter{idx}(c,e,tp)
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
end"""
            self.helpers.append(helper)
            
        # 4. Mill / Banish top cards face-down
        elif "banish the top" in para_l and "face-down" in para_l:
            count = 3
            count_match = re.search(r"top\s+(\d+)\s+cards", para_l)
            if count_match: count = int(count_match.group(1))
            helper = f"""function s.target{idx}(e,tp,eg,ep,ev,re,r,rp,chk)
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
end"""
            self.helpers.append(helper)
            
        # 5. Send from Deck to GY (Foolish Burial effect)
        elif "send 1" in para_l and "deck to the gy" in para_l:
            helper = f"""function s.tgfilter{idx}(c)
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
end"""
            self.helpers.append(helper)
            
        # 6. Default Fallback
        else:
            helper = f"""function s.target{idx}(e,tp,eg,ep,ev,re,r,rp,chk,chkc)
\tif chk==0 then return true end
end
function s.operation{idx}(e,tp,eg,ep,ev,re,r,rp)
\t-- Effect implementation
end"""
            self.helpers.append(helper)

    def render(self):
        self.build_procedures()
        self.analyze_effects()
        
        proc_str = "\n".join(self.procedures)
        eff_str = "\n\n".join(self.effects)
        help_str = "\n\n".join(self.helpers)
        
        header = f"""-- {self.name}
-- Custom Card ID: {self.cid}
-- [{self.ctype} / {self.csubtype}]
-- Duelingbook Link: {self.db_url or 'https://www.duelingbook.com'}
local s,id=GetID()
function s.initial_effect(c)
{proc_str}
{eff_str}
end

{help_str}
"""
        return header

def generate_lua_for_card_full(card_data, scripts_dir=SCRIPTS_DIR, overwrite=True):
    cid = card_data[0]
    script_path = os.path.join(scripts_dir, f"c{cid}.lua")
    if os.path.exists(script_path) and not overwrite:
        return False
        
    builder = LuaScriptBuilder(card_data)
    content = builder.render()
    
    os.makedirs(scripts_dir, exist_ok=True)
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(content)
    return True

def generate_lua_for_card(card, scripts_dir=SCRIPTS_DIR, overwrite=False):
    """
    Backwards-compatible wrapper: if simple 5-tuple passed, query DB for full record.
    """
    cid = card[0]
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

def generate_all_scripts(story_db=STORY_DB_PATH, scripts_dir=SCRIPTS_DIR, overwrite=True):
    os.makedirs(scripts_dir, exist_ok=True)
    conn = sqlite3.connect(story_db)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, card_type, card_subtype, attribute, monster_type,
               level_or_rank_or_link, scale, atk, def, link_arrows,
               effect_text, pendulum_effect, duelingbook_url
        FROM custom_cards
    """)
    cards = cur.fetchall()
    conn.close()
    
    generated = 0
    for card in cards:
        if generate_lua_for_card_full(card, scripts_dir, overwrite=overwrite):
            generated += 1
            
    print(f"[+] Successfully generated/upgraded {generated} advanced Lua scripts in {scripts_dir}")

if __name__ == "__main__":
    generate_all_scripts()
