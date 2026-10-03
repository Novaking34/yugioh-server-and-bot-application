/* =============================================================================
   The Land of Kustomazi - Card Catalog & Database Explorer JavaScript
   ============================================================================= */

let allCards = [];
let activeCategory = 'all';

async function loadCardCatalog() {
    const grid = document.getElementById('catalog-cards-grid');
    if (!grid) return;

    grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-muted);">Loading custom card database...</div>';

    try {
        const res = await fetch('/api/cards');
        if (!res.ok) throw new Error('Failed to fetch cards');
        allCards = await res.json();
        renderFilteredCards();
    } catch (err) {
        console.error('Error loading cards:', err);
        grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--accent-rose);">Error loading card database: ${err.message}</div>`;
    }
}

function renderFilteredCards() {
    const grid = document.getElementById('catalog-cards-grid');
    const searchInput = document.getElementById('catalog-search-input');
    const query = searchInput ? searchInput.value.toLowerCase().trim() : '';

    if (!grid) return;

    const filtered = allCards.filter(card => {
        // Category check
        if (activeCategory !== 'all' && (card.card_type || '').toLowerCase() !== activeCategory.toLowerCase()) {
            return false;
        }
        // Search query check
        if (query) {
            const nameMatch = (card.name || '').toLowerCase().includes(query);
            const effectMatch = (card.effect_text || '').toLowerCase().includes(query);
            const idMatch = String(card.id || '').includes(query);
            const raceMatch = (card.monster_type || '').toLowerCase().includes(query);
            return nameMatch || effectMatch || idMatch || raceMatch;
        }
        return true;
    });

    const countLabel = document.getElementById('catalog-card-count');
    if (countLabel) {
        countLabel.textContent = `${filtered.length} Cards Found`;
    }

    if (filtered.length === 0) {
        grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 60px; color: var(--text-muted); font-size: 16px;">No cards match your filter criteria.</div>';
        return;
    }

    grid.innerHTML = filtered.map(card => {
        const typeClass = (card.card_type || '').toLowerCase() === 'monster' ? 'badge-monster' :
                          (card.card_type || '').toLowerCase() === 'spell' ? 'badge-spell' : 'badge-trap';

        const imgSrc = `/pics/${card.id}.jpg`;
        const fallbackSrc = card.image_url || 'https://images.duelingbook.com/custom-pics/2200000/2282769.jpg';

        const isMonster = (card.card_type || '').toLowerCase() === 'monster';
        const atkVal = card.atk === -2 ? '?' : (card.atk !== null ? card.atk : '-');
        const defVal = card.def === -2 ? '?' : (card.def !== null ? card.def : '-');
        const statsHtml = isMonster ? `
            <div class="card-stats">
                <span>ATK / <strong class="stat-atk">${atkVal}</strong></span>
                <span>DEF / <strong class="stat-def">${defVal}</strong></span>
            </div>
        ` : `
            <div class="card-stats" style="color: var(--text-muted);">
                <span>${card.card_subtype || 'Standard'}</span>
                <span>${card.set_number || 'TLOK'}</span>
            </div>
        `;

        return `
            <div class="card-tile" id="card-${card.id}" onclick="openCardModal(${card.id})">
                <div class="card-img-wrapper">
                    <img class="card-img" src="${imgSrc}" onerror="this.onerror=null; this.src='${fallbackSrc}';" alt="${card.name}" loading="lazy">
                    <span class="card-badge-type ${typeClass}">${card.card_subtype || card.card_type}</span>
                    <span class="card-badge-id">${card.id}</span>
                </div>
                <div class="card-content">
                    <div class="card-title" title="${card.name}">${card.name}</div>
                    <div class="card-meta">
                        <span>${card.attribute || ''}</span>
                        ${card.level_or_rank_or_link ? `<span>★${card.level_or_rank_or_link}</span>` : ''}
                        <span>${card.monster_type || card.card_type}</span>
                    </div>
                    ${statsHtml}
                </div>
            </div>
        `;
    }).join('');
}

function openCardModal(cardId) {
    const card = allCards.find(c => c.id === cardId);
    if (!card) return;

    const modal = document.getElementById('card-modal-overlay');
    const container = document.getElementById('card-modal-body');
    if (!modal || !container) return;

    const imgSrc = `/pics/${card.id}.jpg`;
    const fallbackSrc = card.image_url || '';
    const dbUrl = card.duelingbook_url || (card.duelingbook_id ? `https://www.duelingbook.com/card?id=${card.duelingbook_id}` : null);

    const isMonster = (card.card_type || '').toLowerCase() === 'monster';
    const atkVal = card.atk === -2 ? '?' : (card.atk !== null ? card.atk : '-');
    const defVal = card.def === -2 ? '?' : (card.def !== null ? card.def : '-');

    container.innerHTML = `
        <div class="modal-art-box">
            <img src="${imgSrc}" onerror="this.onerror=null; this.src='${fallbackSrc}';" alt="${card.name}">
            <div style="display: flex; gap: 8px; margin-top: 14px; flex-wrap: wrap;">
                <button class="btn btn-secondary" style="flex: 1; font-size: 12px;" onclick="copyToClipboard('${card.id}', 'Passcode ${card.id} copied!')">
                    📋 Copy Passcode
                </button>
                ${dbUrl ? `<a href="${dbUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-accent" style="flex: 1; font-size: 12px; text-decoration: none;">🌐 DuelingBook</a>` : ''}
            </div>
        </div>
        <div>
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; margin-bottom: 8px;">
                <h2 style="font-size: 24px; line-height: 1.2;">${card.name}</h2>
            </div>
            <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 16px; flex-wrap: wrap;">
                <span class="chip active" style="font-size: 11px; padding: 3px 10px;">${card.card_type}</span>
                <span class="chip" style="font-size: 11px; padding: 3px 10px;">${card.card_subtype || 'Standard'}</span>
                ${card.attribute ? `<span class="chip" style="font-size: 11px; padding: 3px 10px;">${card.attribute}</span>` : ''}
                ${card.level_or_rank_or_link ? `<span class="chip" style="font-size: 11px; padding: 3px 10px;">Level ${card.level_or_rank_or_link}</span>` : ''}
                <span class="mono" style="font-size: 12px; color: var(--accent-cyan);">ID: ${card.id}</span>
            </div>

            ${isMonster ? `
                <div style="background: rgba(0, 0, 0, 0.3); border-radius: var(--radius-sm); padding: 10px 14px; display: flex; gap: 24px; margin-bottom: 16px; font-family: 'JetBrains Mono', monospace;">
                    <div>[${card.monster_type || 'Monster'} / ${card.card_subtype || 'Effect'}]</div>
                    <div>ATK / <strong class="stat-atk">${atkVal}</strong></div>
                    <div>DEF / <strong class="stat-def">${defVal}</strong></div>
                </div>
            ` : ''}

            <div style="margin-bottom: 20px;">
                <h4 style="font-size: 13px; color: var(--text-muted); text-transform: uppercase; margin-bottom: 6px;">Card Text</h4>
                <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 14px; font-size: 13px; line-height: 1.6; white-space: pre-wrap;">${card.effect_text || 'No effect text registered.'}</div>
            </div>

            ${card.lore_text ? `
                <div style="margin-bottom: 16px;">
                    <h4 style="font-size: 13px; color: var(--accent-gold); text-transform: uppercase; margin-bottom: 4px;">Story Lore Context</h4>
                    <p style="font-size: 13px; color: var(--text-secondary); font-style: italic;">${card.lore_text}</p>
                </div>
            ` : ''}

            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; font-size: 12px; color: var(--text-muted); border-top: 1px solid var(--border-subtle); padding-top: 14px;">
                <div>Faction: <strong style="color: var(--text-primary);">${card.faction_name || 'The Creators of Kustomazi'}</strong></div>
                <div>Set: <strong style="color: var(--text-primary);">${card.set_number || 'TLOK-001'}</strong></div>
                <div>Status: <strong style="color: var(--accent-emerald);">${card.banlist_status || 'Unlimited'}</strong></div>
                <div>Script: <strong class="mono" style="color: var(--accent-cyan);">${card.script_file || `c${card.id}.lua`}</strong></div>
            </div>
        </div>
    `;

    modal.classList.add('active');
}

function closeCardModal() {
    const modal = document.getElementById('card-modal-overlay');
    if (modal) modal.classList.remove('active');
}

// Category filter button handler
function setCategoryFilter(category, btnElement) {
    activeCategory = category;
    document.querySelectorAll('.filter-chips .chip').forEach(el => el.classList.remove('active'));
    if (btnElement) btnElement.classList.add('active');
    renderFilteredCards();
}

document.addEventListener('DOMContentLoaded', () => {
    loadCardCatalog();

    const searchInput = document.getElementById('catalog-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            renderFilteredCards();
        });
    }

    const modalOverlay = document.getElementById('card-modal-overlay');
    if (modalOverlay) {
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) closeCardModal();
        });
    }
});
