/* =============================================================================
   The Land of Kustomazi - Deck Vault JavaScript
   ============================================================================= */

async function loadDecks() {
    const container = document.getElementById('decks-list-container');
    const downloadsContainer = document.getElementById('shared-ydk-downloads');

    try {
        // 1. Fetch Story Decks
        const res = await fetch('/api/decks');
        const decks = res.ok ? await res.json() : [];

        if (container) {
            if (decks.length === 0) {
                container.innerHTML = '<div style="color: var(--text-muted); padding: 30px; text-align: center;">No story character decks registered yet.</div>';
            } else {
                container.innerHTML = decks.map(d => `
                    <div style="background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); padding: 24px; display: flex; flex-direction: column; gap: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                                <h3 style="font-size: 19px; margin-bottom: 4px;">${d.name}</h3>
                                <span style="font-size: 12px; color: var(--accent-cyan); font-weight: 600;">Duelist: ${d.character_name || 'ProfessorSeanEX'}</span>
                            </div>
                            <span class="hero-tag" style="margin-bottom: 0;">Deck</span>
                        </div>
                        <p style="color: var(--text-secondary); font-size: 13px; line-height: 1.5;">${d.description || 'Pre-constructed custom archetype strategy.'}</p>
                        <div style="display: flex; gap: 8px; margin-top: auto; padding-top: 10px;">
                            ${d.ydk_filename ? `
                                <a href="/api/shared/decks/${d.ydk_filename}" class="btn btn-primary" style="flex: 1; font-size: 13px; text-decoration: none; justify-content: center;">
                                    📥 Download .YDK
                                </a>
                            ` : ''}
                        </div>
                    </div>
                `).join('');
            }
        }

        // 2. Fetch Downloadable .YDK Files
        if (downloadsContainer) {
            const dlRes = await fetch('/api/shared/decks');
            const files = dlRes.ok ? await dlRes.json() : [];

            if (files.length === 0) {
                downloadsContainer.innerHTML = '<div style="color: var(--text-muted); font-size: 13px;">No raw .YDK files in shared folder.</div>';
            } else {
                downloadsContainer.innerHTML = files.map(f => `
                    <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(0, 0, 0, 0.25); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 12px 18px; margin-bottom: 10px;">
                        <div>
                            <strong style="color: var(--text-primary); font-size: 14px;">${f.filename}</strong>
                            <span style="font-size: 12px; color: var(--text-muted); margin-left: 12px;">(${(f.size_bytes / 1024).toFixed(1)} KB)</span>
                        </div>
                        <a href="${f.download_url}" class="btn btn-secondary" style="font-size: 12px; padding: 6px 14px;">Download</a>
                    </div>
                `).join('');
            }
        }
    } catch (err) {
        console.error('Error loading decks:', err);
    }
}

document.addEventListener('DOMContentLoaded', loadDecks);
