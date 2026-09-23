# Osservabilità tra sedi

Richiesta: correggere Grafana/Prometheus/Loki, collegare Garage al DAS e raccogliere metriche/log di entrambi i server.

## Decisione
Repository dedicato homelab-monitoring, successore per rinomina di grafana-docker; Grafana e Prometheus hanno lo stesso ciclo operativo e restano insieme. Core resta proprietario delle applicazioni, edge dell'accesso web, network della VPN. Garage dedicato a Loki è incluso qui; minio-docker potrà essere archiviato dopo collaudo e verifica che nessun altro consumer ne dipenda.

Ryzen ospita Grafana, Prometheus e Loki monolitico. Fuji ospita Garage con S3 solo WireGuard e admin/RPC loopback. Dataset previsto tank/observability, quota 128 GiB, fuori dall'export NFS tank/storage e dal repository backup. Prometheus, Loki WAL/compactor e Grafana restano su SSD locale Ryzen. Nessun NFS per i database. Garage v2.3.0 selezionato rispetto a RustFS rc.6; contratto S3 collaudabile e sostituibile.

Alloy indipendente su entrambi i nodi: exporter Unix/cAdvisor integrati, log Docker e journald, remote_write verso Prometheus e push Loki tramite gateway autenticato sulla VPN. Metriche e log hanno host stabile. Nessuna porta exporter pubblica. Accesso Docker di Alloy è privilegiato di fatto; nessun accesso del browser al socket.

Grafana/Prometheus/Loki non pubblici; Grafana loopback con tunnel SSH. Gateway solo WireGuard con credenziali per agente e percorsi di ingestione consentiti. Garage usa chiave S3 dedicata al bucket Loki, mai token admin in Loki. Nessun segreto versionato. Nessuna cancellazione automatica di volumi o storia Git.

Retention log 30 giorni con compactor persistente; metriche 15 giorni / 8 GiB. Quota ZFS non è riserva. Mancanza DAS blocca Garage; indisponibilità Fuji interrompe accesso S3 e hub VPN, non promette HA. Buffer metriche/log persistente ma finito.

## Evidenze 2026-09-13
Fuji RAM disponibile ~1,2 GiB, Ryzen ~4,8 GiB; nessuno stack monitoraggio/Garage presente nel censimento docker ps -a. Nessun volume nominato Grafana/Garage; volumi anonimi preservati, contenuto non censito. Fuji tank/storage e tank/backups esistono. sudo richiede password. Endpoint SSH Ryzen verificato via ProxyJump Fuji verso 192.168.68.107.

## Collaudo
Validazioni native promtool, Loki verify-config, Alloy validate, nginx -t, Compose. Smoke temporaneo isolato: ingestione/query metriche e log, Loki con bucket S3, dashboard e datasource Grafana. Deployment live separato: dataset, firewall, servizi, verifica host labels, metriche container, journald e oggetti S3. Archiviazione remoti solo dopo collaudo live.
