# Collaudo RustFS — 2026-09-23

## Ambito

Docker Desktop locale, progetto isolato `homelab-rustfs-smoke`, credenziali nuove e dati sintetici. Nessuna installazione sui server certificata da questi test.

## Esiti osservati

- Bootstrap: permessi privati, rifiuto sovrascritture, credenziali admin/Loki/RPC distinte; test unitari passati.
- Compose backend/storage/agent, promtool, Loki verify-config, Alloy validate e nginx -t: passati.
- RustFS 1.0.0: immagine scaricata, processo UID 10001; creazione bucket/account/policy con client mc riuscita.
- PUT/GET/HEAD/DELETE account Loki: passati; lettura oggetto in altro bucket negata.
- Gateway: ingestione non autenticata 401; autenticata Loki 204, ricerca marker e flush riusciti.
- Alloy sintetico → gateway → Prometheus remote_write: metrica presente.
- Grafana: salute dei due datasource OK e dashboard homelab-overview caricata.
- Lettore Loki nuovo senza WAL/index/cache originali: recuperata da RustFS la riga di log attesa usando target read,query-scheduler e query-store-only.
- Revisione indipendente installer/storage/bootstrap: nessun rilievo bloccante.

## Problemi di test risolti e limiti

Il disco Docker Desktop occupato oltre 90% attivava la protezione WAL Loki e causava HTTP 500. Nel solo smoke è stato usato tmpfs per `/loki`; la protezione e la persistenza di produzione restano invariate. Il polling del lettore gestisce anche connessioni chiuse durante l'avvio.

Non ancora verificati: RAM/swap sotto carico su Fuji, journal e cAdvisor dei due host, collegamento VPN reale tra i componenti, retention a 30 giorni, reboot/mount DAS assente, backup dei nuovi dati e notifiche alert. Il dataset pianificato ha quota 128 GiB; RustFS limita il processo a 768 MiB ma questi limiti richiedono osservazione live.

## Attivazione

Checkout durevole salvato in `/Volumes/SSD/progetti/github/homelab-monitoring`; staging verificato su entrambi gli host in `/home/mika/homelab-monitoring-stage-20260923`, con segreti per ruolo e permessi directory 0700/file 0600. Eseguire `sudo bash /home/mika/homelab-monitoring-stage-20260923/scripts/install-host`, prima Fuji, poi Ryzen. `sudo -n` su Fuji richiede password: il test locale non supera questo requisito. Nessuna rinomina/archiviazione GitHub effettuata.
