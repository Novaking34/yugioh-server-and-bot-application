/* =============================================================================
   The Land of Kustomazi - Lore & Saga Chronicles JavaScript
   ============================================================================= */

async function loadLoreData() {
    const factionsContainer = document.getElementById('lore-factions-container');
    const charactersContainer = document.getElementById('lore-characters-container');
    const arcsContainer = document.getElementById('lore-arcs-container');

    try {
        const res = await fetch('/api/lore');
        if (!res.ok) throw new Error('Failed to load lore');
        const data = await res.json();

        // 1. Render Narrative Arcs / Sagas
        if (arcsContainer && data.arcs) {
            if (data.arcs.length === 0) {
                arcsContainer.innerHTML = '<div style="color: var(--text-muted); padding: 20px;">No narrative arcs registered yet.</div>';
            } else {
                arcsContainer.innerHTML = data.arcs.map(arc => `
                    <div style="background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); padding: 24px; margin-bottom: 20px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <span class="hero-tag" style="margin-bottom: 0;">Act ${arc.order_index || 1}</span>
                            <span style="font-size: 12px; color: var(--accent-gold); font-weight: 600;">Canon Chronicle</span>
                        </div>
                        <h3 style="font-size: 20px; margin-bottom: 8px;">${arc.title}</h3>
                        <p style="color: var(--text-secondary); font-size: 14px; line-height: 1.6;">${arc.synopsis || 'Saga synopsis recorded in the archives.'}</p>
                    </div>
                `).join('');
            }
        }

        // 2. Render Factions
        if (factionsContainer && data.factions) {
            factionsContainer.innerHTML = data.factions.map(fac => `
                <div style="background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); padding: 24px; display: flex; flex-direction: column; gap: 12px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="width: 36px; height: 36px; border-radius: 8px; background: rgba(99, 102, 241, 0.2); border: 1px solid rgba(99, 102, 241, 0.4); display: flex; align-items: center; justify-content: center; font-size: 18px;">🏛️</div>
                        <h3 style="font-size: 18px;">${fac.name}</h3>
                    </div>
                    <p style="color: var(--text-secondary); font-size: 14px;">${fac.lore_description || 'Cosmic order faction of Kustomazi.'}</p>
                    <div style="background: rgba(0, 0, 0, 0.25); border-radius: var(--radius-sm); padding: 10px; font-size: 12px; color: var(--accent-cyan); margin-top: auto;">
                        <strong>Playstyle:</strong> ${fac.playstyle_overview || 'High-level Divine control and ritual tribute.'}
                    </div>
                </div>
            `).join('');
        }

        // 3. Render Characters
        if (charactersContainer && data.characters) {
            charactersContainer.innerHTML = data.characters.map(char => `
                <div style="background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); padding: 24px;">
                    <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 14px;">
                        <div style="width: 48px; height: 48px; border-radius: 50%; background: linear-gradient(135deg, var(--accent-gold), var(--accent-indigo)); display: flex; align-items: center; justify-content: center; font-size: 24px; box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);">👑</div>
                        <div>
                            <h3 style="font-size: 18px;">${char.name}</h3>
                            <span style="font-size: 12px; color: var(--accent-gold); font-weight: 600;">${char.alias || 'Supreme Duelist'}</span>
                        </div>
                    </div>
                    <p style="color: var(--text-secondary); font-size: 13px; line-height: 1.6;">${char.bio || 'Creator and master strategist of the Kustomazi chronicle.'}</p>
                </div>
            `).join('');
        }
    } catch (err) {
        console.error('Error loading lore:', err);
    }
}

document.addEventListener('DOMContentLoaded', loadLoreData);
