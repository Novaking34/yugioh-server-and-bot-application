-- Fracture of the Starlit Sky
-- Custom Card ID: 50000005
-- [Spell / Quick-Play]
-- Duelingbook Link: https://www.duelingbook.com/card?id=50000005
local s,id=GetID()
function s.initial_effect(c)

	-- Effect 1: Target 1 face-up monster on the field; change its battle pos...
	local e1=Effect.CreateEffect(c)
	e1:SetDescription(aux.Stringid(id,0))
	e1:SetCategory(CATEGORY_SPECIAL_SUMMON+CATEGORY_DISABLE)
	e1:SetType(EFFECT_TYPE_QUICK_O)
	e1:SetCode(EVENT_FREE_CHAIN)
	e1:SetHintTiming(0,TIMINGS_CHECK_MONSTER_E)
	e1:SetProperty(EFFECT_FLAG_CARD_TARGET)
	e1:SetTarget(s.target1)
	e1:SetOperation(s.operation1)
	c:RegisterEffect(e1)

	-- Effect 2: If you control a "Starforged" or "Void Sovereign" monster, t...
	local e2=Effect.CreateEffect(c)
	e2:SetDescription(aux.Stringid(id,1))
	e2:SetCategory(CATEGORY_DISABLE)
	e2:SetType(EFFECT_TYPE_QUICK_O)
	e2:SetCode(EVENT_FREE_CHAIN)
	e2:SetHintTiming(0,TIMINGS_CHECK_MONSTER_E)
	e2:SetTarget(s.target2)
	e2:SetOperation(s.operation2)
	c:RegisterEffect(e2)
end

function s.target1(e,tp,eg,ep,ev,re,r,rp,chk,chkc)
	if chk==0 then return true end
end
function s.operation1(e,tp,eg,ep,ev,re,r,rp)
	-- Effect implementation
end

function s.target2(e,tp,eg,ep,ev,re,r,rp,chk,chkc)
	if chk==0 then return true end
end
function s.operation2(e,tp,eg,ep,ev,re,r,rp)
	-- Effect implementation
end
