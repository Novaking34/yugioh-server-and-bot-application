#!/usr/bin/env python3
"""
Lua Effect Script Generator for YGOPro / EDOPro Simulator ocgcore engine.
Generates starter Lua script files (c<id>.lua) for custom cards.
"""

import sqlite3
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORY_DB_PATH = os.path.join(BASE_DIR, "story_database", "ygo_story.db")
SCRIPTS_DIR = os.path.join(BASE_DIR, "server-data", "expansions", "scripts")

LUA_TEMPLATE = """-- {name}
-- Custom Card ID: {id}
-- Duelingbook Link: {db_url}
local s,id=GetID()
function s.initial_effect(c)
{extra_procedures}
	-- Effect Scaffold
	local e1=Effect.CreateEffect(c)
	e1:SetDescription(aux.Stringid(id,0))
{effect_type}
{effect_code}
{range}
	e1:SetCountLimit(1,id)
	e1:SetTarget(s.target)
	e1:SetOperation(s.operation)
	c:RegisterEffect(e1)
end

function s.target(e,tp,eg,ep,ev,re,r,rp,chk,chkc)
	if chk==0 then return true end
end

function s.operation(e,tp,eg,ep,ev,re,r,rp)
	-- Effect logic implementation
end
"""

def generate_lua_for_card(card, scripts_dir=SCRIPTS_DIR):
    cid, name, ctype, csubtype, db_url = card
    script_path = os.path.join(scripts_dir, f"c{cid}.lua")
    
    # Don't overwrite existing customized scripts
    if os.path.exists(script_path):
        return False
        
    csub_l = (csubtype or '').lower()
    ctype_l = (ctype or '').lower()
    
    extra_procedures = ""
    effect_type = "\te1:SetType(EFFECT_TYPE_IGNITION)"
    effect_code = ""
    range_str = "\te1:SetRange(LOCATION_MZONE)"
    
    if 'xyz' in csub_l:
        extra_procedures = "\tXyz.AddProcedure(c,nil,8,2)\n\tc:EnableReviveLimit()"
    elif 'link' in csub_l:
        extra_procedures = "\tLink.AddProcedure(c,aux.FilterBoolFunctionEx(Card.IsType,TYPE_EFFECT),3,4)\n\tc:EnableReviveLimit()"
    elif 'synchro' in csub_l:
        extra_procedures = "\tSynchro.AddProcedure(c,nil,1,1,Synchro.NonTuner(nil),1,99)\n\tc:EnableReviveLimit()"
    elif 'fusion' in csub_l:
        extra_procedures = "\tFusion.AddProcedure(c,nil,2,2)\n\tc:EnableReviveLimit()"
        
    if ctype_l == 'spell' or ctype_l == 'trap':
        effect_type = "\te1:SetType(EFFECT_TYPE_ACTIVATE)"
        effect_code = "\te1:SetCode(EVENT_FREE_CHAIN)"
        range_str = ""
        
    content = LUA_TEMPLATE.format(
        id=cid,
        name=name,
        db_url=db_url or "https://www.duelingbook.com",
        extra_procedures=extra_procedures,
        effect_type=effect_type,
        effect_code=effect_code,
        range=range_str
    )
    
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(content)
    return True

def generate_all_scripts(story_db=STORY_DB_PATH, scripts_dir=SCRIPTS_DIR):
    os.makedirs(scripts_dir, exist_ok=True)
    conn = sqlite3.connect(story_db)
    cur = conn.cursor()
    cur.execute("SELECT id, name, card_type, card_subtype, duelingbook_url FROM custom_cards")
    cards = cur.fetchall()
    
    generated = 0
    for card in cards:
        if generate_lua_for_card(card, scripts_dir):
            generated += 1
            
    conn.close()
    print(f"[+] Generated {generated} starter Lua scripts in {scripts_dir}")

if __name__ == "__main__":
    generate_all_scripts()
