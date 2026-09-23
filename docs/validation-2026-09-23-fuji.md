# Reinstallazione pulita su Fuji — 2026-09-23

Richiesta esplicita utente: backend su Fuji, solo Alloy su Ryzen; autorizzata cancellazione dei dati del solo monitoraggio senza migrazione.

## Operazioni eseguite

- Fermati e rimossi i container dei soli progetti `homelab-monitoring`, `homelab-telemetry`, `homelab-object-storage`.
- Azzerati dati `/srv/homelab-monitoring` su entrambi e `/tank/observability/rustfs` su Fuji; dataset ZFS e quota preservati. Altri servizi non modificati.
- Preparazione effettuata da container temporaneo senza rete, senza privilegi aggiuntivi, con bind mount scrivibili limitati alle directory progetto. Nessun accesso al filesystem host completo dal container di preparazione.
- Fuji: un Compose con Grafana, Prometheus, Loki, RustFS, gateway e Alloy. Ryzen: un Compose con solo Alloy e solo `runtime/agent.env`.
- Gateway su `10.20.0.1:3100`; S3 interno `rustfs:9000`; porte S3/console solo loopback 19000/9001. Grafana loopback 13000 perché 3000 occupata da un servizio preesistente.
- Gestione Compose verificata come `mika`, senza sudo. Nessuna nuova supervisione systemd.

## Prove live

- RustFS healthy; bucket e account limitato Loki inizializzati.
- Grafana database OK; datasource Prometheus e Loki entrambi OK.
- Prometheus `node_uname_info`: presenti fujiserver e ryzen5lenovo.
- Loki query aggregata: log Docker e journald da entrambi gli host (il job journal effettivo è `loki.source.journal.system`).
- Flush Loki riuscito; account Loki ha elencato 276 oggetti nel bucket RustFS.
- Ryzen: `docker compose config --services` restituisce solo `alloy`; sotto `/srv/homelab-monitoring` resta solo `alloy`; runtime contiene solo agent.env.
- Tutti i sei container Fuji senza OOM né riavvii al controllo dopo alcuni minuti. RAM disponibile Fuji circa 1,8 GiB, swap usata circa 2,1 GiB; Alloy 367 MiB su limite 384 MiB: osservare nel tempo. Questi dati non certificano tenuta sotto carico prolungato.

## Verifiche locali e limiti

Bootstrap e validatori Compose/promtool/Loki/Alloy/nginx passati. Guardia DAS già provata su ZFS reale e directory non ZFS. Reboot, retention di 30 giorni, backup nuovi percorsi e notifiche alert non collaudati/configurati da questa sessione. Repository remoto non rinominato né archiviato.

## Semplificazione e accesso LAN

Su richiesta utente, il Compose principale ora contiene tutti i servizi Fuji senza extends; eliminato storage/compose.yaml ridondante. Confronto JSON della configurazione risolta prima/dopo: unica variazione funzionale bind Grafana da 127.0.0.1 a 192.168.1.54, porta 13000. Ricreato soltanto Grafana. Dal Mac verificati HTTP 200 sia /api/health (database ok) sia /login su http://192.168.1.54:13000. Smoke Compose aggiornato e validato.
