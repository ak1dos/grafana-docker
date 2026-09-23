# Dashboard e log — 2026-09-23

## Valutazione catalogo Grafana

- [Node Exporter Full 1860](https://grafana.com/grafana/dashboards/1860-node-exporter-full/): copertura ampia, ma assume job/variabili differenti e alcuni collector opzionali. Utili separazione CPU/RAM/dischi/rete e drill-down per host. Non importato integralmente per evitare pannelli non supportati dai collector presenti.
- [Docker Containers 14971](https://grafana.com/grafana/dashboards/14971-docker-containers/): cAdvisor compatibile come fonte; richiede adattamento alle etichette host/name del nostro Alloy. Dashboard locale usa core CPU, working set, limiti cgroup e uptime.
- [Valheim 14123](https://grafana.com/grafana/dashboards/14123-valheim/): legata a mbround18/valheim e metriche via Steam. Il server esistente usa lloesche/community-valheim-tools con crossplay; status.json restituisce TimeoutError. Importazione diretta non avrebbe fornito il conteggio giocatori.
- [A2S exporter](https://github.com/armsnyder/a2s-exporter): non risolve il problema se il server non risponde alla query A2S. Nessun exporter o mod aggiunto al gioco.
- [Alloy loki.process](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.process/): pipeline di pulizia dei log, validata con Alloy 1.19.2.

Le dashboard sono locali, generate da scripts/build-dashboards e adattate alle serie osservate; nessun template esterno importato alla cieca.

## Risultato distribuito

- homelab-hosts: CPU normalizzata, RAM totale/disponibile, swap, filesystem distinti (senza sommare dataset ZFS), disco, rete, pressure e uptime.
- homelab-containers: filtro host/container, CPU in core, RAM working set e limiti cgroup, top 10, uptime e stato raccolta.
- homelab-logs: filtri host/container/unità/testo, Docker separato da journal, volume e righe error/warning.
- homelab-valheim: conteggio connessioni, ultima rilevazione, storico, risorse e uptime; eventi gioco/salvataggi, errori e diagnostica completa.
- homelab-overview mantiene il vecchio UID ma diventa una pagina di navigazione.

## Giocatori Valheim: limite esplicito

Il processo emette `Connections N ZDOS:...` ogni circa dieci minuti. Il pannello mostra l’ultima osservazione entro 15 minuti e il suo timestamp; oltre quella finestra mostra N/D, mai uno zero inventato. Non è un contatore in tempo reale e non fornisce i nomi dei giocatori. Crossplay e processo di gioco non modificati; Valheim non riavviato.

## Correzioni raccolta

Alloy conserva tutte le righe: rimuove codici ANSI e prefissi ridondanti syslog/supervisord/data nelle righe Valheim. Il journal nuovo riceve job=journal; le query supportano anche il vecchio job loki.source.journal.system. Nessuna cancellazione di log storici.

Le etichette up effettive sono integrations/unix e integrations/cadvisor: corretti pannello cAdvisor e allarme ExporterScrapeFailed, prima basati su nomi assenti.

## Prove

- Validatori bootstrap, Compose, promtool, Loki, Alloy e nginx passati.
- scripts/check-dashboard-queries: 39 query eseguite sui datasource reali, zero errori e nessun pannello vuoto al controllo finale; assenza futura di warning/errori può naturalmente dare una serie vuota.
- API Grafana: cinque dashboard provisioned, rispettivamente 1/13/9/5/12 pannelli; entrambi i datasource OK.
- Ultima riga Valheim verificata senza prefisso supervisord dopo aggiornamento Alloy.
- Browser della sessione non disponibile (lista vuota): nessun collaudo visuale tramite screenshot eseguito. Layout a griglia e API/query verificati; disponibilità del dato non certifica automaticamente tutti i dettagli di rendering.
