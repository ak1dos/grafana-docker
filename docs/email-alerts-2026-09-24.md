# Notifiche email — 24 settembre 2026

## Configurazione distribuita

Le quattro regole Prometheus esistenti inviano ad Alertmanager 0.34.1,
fissato al digest e aggiunto al Compose Fuji. SMTP `smtp-relay:587` sulla rete
Docker privata `homelab-mail`, senza nuove credenziali. Mittente
`alerts@ak1dos.com`; destinatario autorizzato nel file privato
`runtime/alertmanager.yml`, escluso da Git. Stato persistente nel bind
`/srv/homelab-monitoring/alertmanager`, UID/GID 1000:1000. Nessuna porta host
pubblicata. Configurazione SMTP interna senza TLS coerente con il relay;
TLS verificato verso Brevo resta responsabilità di Postfix.

Raggruppamento per alertname/host, attesa 30s, intervallo gruppo 5m,
ripetizione 4h; notifiche di risoluzione abilitate. Corretta anche l'etichetta
host degli scrape interni Prometheus/Loki, che indicava ancora Ryzen.

## Prove

Compose config, test bootstrap e sintassi shell superati. Configurazione email
validata da amtool; Prometheus e le quattro regole validate da promtool.
Alertmanager healthy; API Prometheus riporta l'endpoint Alertmanager attivo.
Una regola sintetica temporanea NotificationEmailTest ha attraversato
Prometheus → Alertmanager → SMTP. Contatore notifiche email incrementato,
zero errori email e coda Postfix vuota. Regola sintetica rimossa e Prometheus
ricaricato; restano le quattro regole originali. L'evento di test scade e può
produrre la successiva email di risoluzione secondo il normale raggruppamento.

Il destinatario ha confermato la ricezione dell'email di prova in Gmail il
24 settembre 2026: consegna end-to-end verificata. I log di dettaglio Postfix non sono disponibili: rsyslog è
in stato FATAL dal 17 settembre, con pidfile riferito a un altro processo.
Il relay non è stato riavviato né modificato durante questa attività.

Il primo comando di distribuzione con mount ampi è stato respinto dal controllo
automatico. La distribuzione riuscita usa solo singoli file di configurazione
e la nuova directory dati Alertmanager; nessun mount scrivibile degli altri
store applicativi. Nessuna modifica al server Valheim.

## Fonti

- https://prometheus.io/docs/alerting/latest/configuration/
- https://github.com/prometheus/alertmanager/releases/tag/v0.34.1
- Verifiche SSH, amtool/promtool e API live del 24 settembre 2026.
