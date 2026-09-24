# Homelab monitoring

## Distribuzione

- **Fuji:** Grafana, Prometheus, Loki, RustFS, gateway di ingestione e Alloy, nello stesso progetto `homelab-monitoring`.
- **Ryzen:** soltanto Alloy, progetto `homelab-telemetry`.
- Entrambi gli agenti inviano metriche e log al gateway autenticato `10.20.0.1:3100` attraverso WireGuard.
- Il collector Goose su Ryzen legge solo `/loki/api/v1/query_range` con una credenziale distinta dall'ingestione; nessuna porta Loki aggiuntiva è pubblicata.
- Loki usa `rustfs:9000` nella rete Docker; S3 e console sono pubblicati solo sul loopback di Fuji, rispettivamente 19000 e 9001.

La distribuzione precedente con backend su Ryzen è superata dalla scelta esplicita dell’utente del 2026-09-23. I documenti di validazione precedenti conservano la cronologia, non descrivono necessariamente lo stato corrente.

## Persistenza

| Host | Dati | Percorso |
|---|---|---|
| Fuji | Prometheus | `/srv/homelab-monitoring/prometheus` |
| Fuji | Loki WAL/indice/cache | `/srv/homelab-monitoring/loki` |
| Fuji | Grafana | `/srv/homelab-monitoring/grafana` |
| Entrambi | Alloy | `/srv/homelab-monitoring/alloy` |
| Fuji | RustFS oggetti/log | `/tank/observability/rustfs/{data,logs}` |

Bind mount espliciti; nessun volume Docker nominato in produzione. Dataset ZFS `tank/observability`, quota 128 GiB. Il container RustFS rifiuta l’avvio se il dataset atteso non è montato. Prometheus conserva 15 giorni/8 GB; Loki 30 giorni. I backup esistenti non includono automaticamente questi percorsi.

## Gestione quotidiana senza sudo

Su entrambi i server:

```sh
cd /opt/applications/homelab-monitoring
docker compose ps
docker compose up -d
docker compose logs --tail 100 -f
```

Il manifest installato su Ryzen contiene solo Alloy. Su Fuji puoi selezionare il servizio, per esempio `docker compose restart grafana` o `docker compose logs -f rustfs`. `stop` ferma i container, `start` li riavvia, `down` li rimuove preservando i bind mount. Non cancellare le directory dati durante manutenzione ordinaria.

Le credenziali runtime appartengono a `mika`, directory 0700 e file 0600; i manifest/configurazioni sono leggibili dai container. Non stampare `docker compose config` senza `-q`: contiene segreti. `runtime/goose.htpasswd` autentica la sola lettura Loki; `runtime/goose-reader` generato al bootstrap contiene la coppia da installare in `server-agent/secrets/loki_reader` su Ryzen. Non usare le credenziali Alloy per questa lettura.

## Accesso Grafana e RustFS

Grafana è raggiungibile dalla LAN su **http://192.168.1.54:13000**, utente `admin`, password in `runtime/grafana.env` su Fuji. Il bind è limitato all’IP LAN di Fuji.

La console RustFS resta sul loopback; dal Mac:

```sh
ssh -N -L 9001:127.0.0.1:9001 mika@192.168.1.54
```

Console: http://localhost:9001, credenziali in `runtime/rustfs.env`. Il bucket Loki usa un account separato limitato al bucket `loki`; il client mc è solo uno strumento di inizializzazione.

Il `docker-compose.yaml` principale contiene tutte le definizioni di Fuji, senza `extends`. `agents/compose.yaml` serve per l’installazione del solo Alloy su Ryzen. La cartella storage conserva gli script di bootstrap e la policy S3.

## Installazione iniziale

`python3 scripts/bootstrap` crea segreti nuovi e rifiuta sovrascritture. Fuji richiede tutti i file runtime, compreso `goose.htpasswd`, e il proprio file agente; Ryzen solo `runtime/agents/ryzen5lenovo.env`. Il primo setup host usa `sudo bash scripts/install-host` per filesystem e permessi. Successivamente si usa solo Compose. Non sono installati supervisori systemd del progetto.

Su Fuji inizializzazione bucket/account (ripetibile):

```sh
docker compose up -d --wait --wait-timeout 180 rustfs
docker compose --profile bootstrap run --rm init
docker compose up -d
```

`scripts/prepare-clean-container` è uno strumento **distruttivo** per una reinstallazione esplicitamente richiesta: azzera soltanto i percorsi progetto montati in `/install`, `/state` e, su Fuji, `/objectroot/rustfs`. Non fa parte dell’avvio ordinario e non va eseguito sull’host direttamente.

## Verifiche e limiti

`bash scripts/validate`: bootstrap, sintassi shell, Compose, promtool, Loki, Alloy, nginx. `scripts/prepare-smoke` crea un ambiente locale separato con segreti e volumi di test; `check-smoke` e `check-s3-recovery` verificano integrazione e lettura S3.

Verificare entrambe le etichette host in Prometheus, log Docker/journald in Loki, salute datasource Grafana e memoria/swap/OOM su Fuji. Alloy è privilegiato per le metriche host/container e l’accesso ai log. Gli alert sono definiti in Prometheus; notifiche push/email non configurate. Collaudo reboot/DAS assente e retention prolungata richiedono prove dedicate.

## Dashboard

- [Server](http://192.168.1.54:13000/d/homelab-hosts): risorse, capacità e pressione, con selezione host.
- [Container](http://192.168.1.54:13000/d/homelab-containers): CPU in core, RAM working set, limiti e uptime.
- [Log](http://192.168.1.54:13000/d/homelab-logs): Docker e journal separati, filtri e ricerca.
- [Valheim](http://192.168.1.54:13000/d/homelab-valheim): ultima rilevazione giocatori, risorse ed eventi/log.

Il conteggio Valheim deriva dai log nativi crossplay ogni circa 10 minuti, con timestamp visibile e scadenza dopo 15 minuti: non è un conteggio in tempo reale. Non espone nomi dei giocatori. Le righe diagnostiche vengono conservate; la raccolta rimuove colori e prefissi ridondanti.

Rigenerazione: `python3 scripts/build-dashboards`. Verifica query live: `python3 scripts/check-dashboard-queries` (usa le credenziali private locali senza stamparle). [Valutazione marketplace e prove](docs/dashboard-assessment-2026-09-23.md).

## Email degli alert

Prometheus invia le regole esistenti ad Alertmanager nella stessa pila Fuji.
Alertmanager usa `smtp-relay:587` sulla rete Docker esterna `homelab-mail`;
il relay deve essere già installato da homelab-core. Non sono necessarie nuove
credenziali Brevo e non viene pubblicata una porta Alertmanager sull'host.
Il tratto Docker interno usa SMTP senza TLS; il relay mantiene TLS verificato
verso Brevo.

Prima dell'installazione copiare `config/alertmanager/alertmanager.yml.example`
in `runtime/alertmanager.yml`, impostare `to` e applicare `chmod 600`.
La cartella runtime è esclusa da Git; gli indirizzi reali restano lì.
Alertmanager gira come UID/GID 1000 per leggere il file privato e scrive stato,
silenziamenti e deduplicazione in `/srv/homelab-monitoring/alertmanager`.

Email per allarmi e risoluzioni; raggruppamento per alert e host, attesa iniziale
30 secondi, aggiornamenti del gruppo ogni 5 minuti, promemoria ogni 4 ore.
I tempi `for` delle quattro regole restano invariati. Per controllare:

```sh
docker compose ps alertmanager
docker compose logs --since 30m alertmanager
docker compose exec alertmanager amtool --alertmanager.url=http://localhost:9093 alert query
```

Dopo aver modificato i destinatari, validare con `amtool check-config` e ricreare
il solo servizio (`docker compose up -d --force-recreate alertmanager`) per
rileggere anche un file runtime sostituito atomicamente.
Se Fuji è spento, il suo monitoraggio e il relay non possono inviare email:
la rilevazione di quel guasto richiede un controllo esterno.
