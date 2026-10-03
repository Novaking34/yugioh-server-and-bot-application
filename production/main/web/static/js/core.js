/* =============================================================================
   The Land of Kustomazi - Core JavaScript Module
   ============================================================================= */

// Toast notification helper
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3200);
}

// Clipboard copy helper
function copyToClipboard(text, label = 'Copied to clipboard!') {
    navigator.clipboard.writeText(text).then(() => {
        showToast(label, 'success');
    }).catch(err => {
        console.error('Failed to copy: ', err);
        showToast('Failed to copy to clipboard', 'error');
    });
}

// Telemetry Poller
async function updateServerTelemetry() {
    try {
        const res = await fetch('/api/status');
        if (!res.ok) throw new Error('Status degraded');
        const data = await res.json();

        const webPill = document.getElementById('status-web-pill');
        if (webPill) {
            webPill.className = 'status-pill online';
            webPill.innerHTML = '<span class="pulse-dot"></span> Web API: Online';
        }

        const dbStat = document.getElementById('stat-db-cards');
        if (dbStat && data.database) {
            dbStat.textContent = `${data.database.cards || 0} Registered`;
        }
    } catch (e) {
        const webPill = document.getElementById('status-web-pill');
        if (webPill) {
            webPill.className = 'status-pill warning';
            webPill.innerHTML = '⚠️ Web API: Offline/Local';
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    updateServerTelemetry();
    setInterval(updateServerTelemetry, 15000);
});
