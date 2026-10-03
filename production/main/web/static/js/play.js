/* =============================================================================
   The Land of Kustomazi - Play & Live Duel Server JavaScript
   ============================================================================= */

function copyHostConfig() {
    const hostStr = "147.224.147.30";
    copyToClipboard(hostStr, "Simulator Server Host copied!");
}

function copyPortConfig() {
    const portStr = "7911";
    copyToClipboard(portStr, "Simulator Port 7911 copied!");
}

function copyFullEDOProConfig() {
    const configBlock = `[The Land of Kustomazi]
address = 147.224.147.30
port = 7911
version = 0x1337`;
    copyToClipboard(configBlock, "EDOPro connection block copied!");
}
