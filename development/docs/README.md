# 📚 Technical Documentation & Operations Index (`development/docs/`)

This directory contains in-depth architectural specifications, cloud infrastructure guides, and distribution documentation for the Yu-Gi-Oh! platform.

---

## 📁 Technical Manuals

| Document | Topic | Target Audience |
| :--- | :--- | :--- |
| [`HOSTING_24_7.md`](file:///home/professorseanex/yugioh-server/development/docs/HOSTING_24_7.md) | Comparison of 24/7 cloud hosting options (Oracle Cloud Always Free, Hetzner, DigitalOcean) | Server Administrators & Devs |
| [`ORACLE_CLOUDFLARE_SETUP.md`](file:///home/professorseanex/yugioh-server/development/docs/ORACLE_CLOUDFLARE_SETUP.md) | Complete setup guide for Oracle Cloud Free Tier VPS + Cloudflare Zero Trust Tunnels & DNS | Cloud Operations & Infrastructure |
| [`PACKAGING_AND_DISTRIBUTION.md`](file:///home/professorseanex/yugioh-server/development/docs/PACKAGING_AND_DISTRIBUTION.md) | Release packaging architecture, tarball/zip builders, and player distribution workflows | Release Engineers & Maintainers |

---

## 🌐 Subsystem Documentation Cross-References

* **Central Configuration:** [`config/README.md`](file:///home/professorseanex/yugioh-server/config/README.md)
* **DNS & Domain Architecture:** [`config/dns/README.md`](file:///home/professorseanex/yugioh-server/config/dns/README.md)
* **Player Client Package:** [`packages/client/README.md`](file:///home/professorseanex/yugioh-server/packages/client/README.md)
* **Host Server Package:** [`packages/server/README.md`](file:///home/professorseanex/yugioh-server/packages/server/README.md)
* **Server Scripts Manual:** [`packages/server/scripts/README.md`](file:///home/professorseanex/yugioh-server/packages/server/scripts/README.md)
* **Systemd Daemons Manual:** [`packages/server/systemd/README.md`](file:///home/professorseanex/yugioh-server/packages/server/systemd/README.md)
* **Card Compilers & Tools:** [`development/tools/README.md`](file:///home/professorseanex/yugioh-server/development/tools/README.md)
* **Story Database & Schemas:** [`development/database/README.md`](file:///home/professorseanex/yugioh-server/development/database/README.md)
* **Automated Test Suite:** [`development/tests/README.md`](file:///home/professorseanex/yugioh-server/development/tests/README.md)
