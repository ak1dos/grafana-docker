# Evidenze 2026-09-13

## Censimento in sola lettura
Fuji via SSH mika@192.168.1.54; Ryzen via ProxyJump Fuji verso mika@192.168.68.107. Nessun container Grafana/Prometheus/Loki/MinIO nel censimento docker ps -a; nessun volume nominato di questi servizi. Volumi anonimi preservati e contenuto non ispezionato. Fuji: tank/storage e tank/backups, ~1.2GiB RAM disponibile. Ryzen ~4.8GiB RAM disponibile, ~64GiB SSD libero. Nessun nuovo servizio installato. sudo -n su Fuji richiede password.

## Codice e prove locali
Clonati grafana-docker (base 6dd4ad5) e minio-docker in checkout isolati. Credenziali rimosse dai nuovi file, nessun valore riportato nelle evidenze. La storia Git contiene configurazioni storiche: cancellare dal working tree non bonifica i vecchi commit. Non riutilizzare vecchie credenziali; non pubblicare runtime.

Passati: bootstrap privato con rifiuto sovrascrittura; bash -n; Compose config -q backend/storage/agenti; promtool su configurazione e quattro regole; Loki verify-config; Alloy validate; nginx -t; git diff --check.

Smoke Docker Desktop su rete e volumi esclusivi homelab-monitoring-smoke: Garage2.3.0, Loki3.7.7, Prometheus3.14.0, Grafana13.2.1, Alloy1.19.2. Passati readiness, rifiuto ingestione anonima (401), ingestione log autenticata (204), query del marker, flush chunk in Garage, invio metriche Alloy remote_write e query, salute dei due datasource Grafana, dashboard provisionata. Garage mostra oggetti nel bucket. Test minimo, non benchmark; cAdvisor host Linux non collaudato su Docker Desktop.

Revisione separata: aggiunto retry all'avvio backend se WireGuard tarda; corretto comando di aggiornamento agenti in README.

## Limiti prima del deploy
La prova più severa con un secondo Loki privo di WAL/index locale è in corso; non dichiarare ancora il recupero solo-S3 riuscito. Retention a 30 giorni configurata e validata, non osservata per 30 giorni. Nessuna prova di reboot host, fail-mount DAS, pressione RAM/volume log reale, exporter live o notifiche esterne. Installazione root e archiviazione dei vecchi repository ancora pendenti.
