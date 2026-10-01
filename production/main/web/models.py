#!/usr/bin/env python3
"""
=============================================================================
Pydantic Schemas for Yu-Gi-Oh! Story & Custom Card REST API
=============================================================================
Validates HTTP request payloads when registering new custom cards,
querying lore sagas, or exporting deck profiles. Uses Pydantic v2 conventions.
=============================================================================
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any


class CardInput(BaseModel):
    """
    Payload for creating or updating a custom card via the REST API.
    Matches standard fields from Duelingbook exports.
    """
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., description="Display name of the card")
    card_type: str = Field(..., description="Monster, Spell, or Trap")
    card_subtype: Optional[str] = Field("Normal", description="Subtype (Effect, Xyz, Link, Quick-Play, etc.)")
    attribute: Optional[str] = Field(None, description="LIGHT, DARK, WATER, FIRE, EARTH, WIND, DIVINE")
    monster_type: Optional[str] = Field(None, description="Warrior, Dragon, Spellcaster, Cyberse, etc.")
    level_or_rank_or_link: Optional[int] = Field(None, description="Level, Rank, or Link Rating")
    scale: Optional[int] = Field(None, description="Pendulum scale (0-13)")
    atk: Optional[int] = Field(None, description="Attack stat")
    def_: Optional[int] = Field(None, alias="def", description="Defense stat (null for Link monsters)")
    link_arrows: Optional[str] = Field(None, description="Comma-separated arrows (e.g. 'BL,BR,T')")
    effect_text: str = Field(..., description="Card effect or normal monster flavor text")
    pendulum_effect: Optional[str] = Field(None, description="Pendulum effect text")
    
    # Duelingbook Metadata
    duelingbook_id: Optional[str] = Field(None, description="Duelingbook card ID")
    duelingbook_url: Optional[str] = Field(None, description="URL on duelingbook.com")
    image_url: Optional[str] = Field(None, description="Artwork image URL")
    creator_name: Optional[str] = Field("Custom Designer", description="Card author name")
    
    # Story Lore Metadata
    lore_text: Optional[str] = Field(None, description="In-universe narrative lore")
    faction_id: Optional[int] = Field(None, description="Associated faction ID")
    story_significance: Optional[str] = Field("Custom Card", description="Role (Ace, Boss, Starter, Relic)")


class CardResponse(BaseModel):
    """Standardized representation of a custom card returned by the API."""
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    card_type: str
    card_subtype: Optional[str] = None
    attribute: Optional[str] = None
    monster_type: Optional[str] = None
    level_or_rank_or_link: Optional[int] = None
    scale: Optional[int] = None
    atk: Optional[int] = None
    def_: Optional[int] = Field(None, alias="def")
    link_arrows: Optional[str] = None
    effect_text: str
    pendulum_effect: Optional[str] = None
    duelingbook_url: Optional[str] = None
    image_url: Optional[str] = None
    creator_name: Optional[str] = None
    lore_text: Optional[str] = None
    faction_name: Optional[str] = None
    character_name: Optional[str] = None
    story_significance: Optional[str] = None


class StatusResponse(BaseModel):
    """Generic status response for mutations."""
    status: str
    id: Optional[int] = None
    message: str
