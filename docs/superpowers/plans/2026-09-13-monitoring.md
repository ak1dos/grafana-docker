# Monitoring Implementation Plan

**Goal:** osservabilità verificabile di Fuji e Ryzen con Loki su S3/DAS.
**Architecture:** backend Ryzen, storage Fuji, agenti indipendenti su entrambi.
**Tech Stack:** Compose, Grafana, Prometheus, Loki, Alloy, MinIO, nginx, systemd/ZFS.
**Spec:** ../specs/2026-09-13-monitoring.md

## Vincoli
Preservare dati e segreti esistenti. Nessun bind pubblico. Versioni esplicite. Nessun riuso credenziali storiche. Root solo per dataset/installazione host.

- [ ] Correggere stack backend, storage e agenti in compose separati; validare con i binari reali.
- [ ] Aggiungere bootstrap segreti e policy S3, provisioning datasource/dashboard, retention e regole di allarme.
- [ ] Aggiungere installer systemd con dipendenza mount e preflight, senza sudo implicito né pulizia dati.
- [ ] Eseguire smoke isolato e controllare S3, remote_write e Loki query.
- [ ] Preparare checkout server e comandi amministrativi esatti; deploy se i privilegi lo consentono.
- [ ] Aggiornare memoria con evidenze e limiti; rinominare/archiviare remoti soltanto quando giustificato dal collaudo.
