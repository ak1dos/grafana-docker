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

### Budget memoria su Fuji

Grafana e Alloy hanno un limite di 1 GiB ciascuno. I precedenti limiti di
384 MiB hanno causato un OOM di Grafana e forte pressione memoria/swap in
Alloy il 2026-09-25, con raccolte metriche intermittenti e dashboard lente.
Prometheus e Loki mantengono 1 GiB ciascuno, RustFS 768 MiB, Alertmanager
128 MiB e gateway 64 MiB: il totale dei limiti è 4,9375 GiB su circa 7,6 GiB
di RAM host. Sono massimi, non prenotazioni; gli altri servizi e il sistema
operativo condividono la RAM restante. Monitorare pressione memoria, swap,
OOM e durata delle raccolte dopo ogni variazione del carico.
Il collector Ryzen mantiene il proprio limite di 384 MiB: durante
l’incidente le sue raccolte risultavano regolari e rapide.

### Comandi

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

Console: http://localhost:9001, credenziali in `runtime/rustfs.env`. Il bucket Loki usa un account separato limitato al bucket `loki`; il client ufficiale RustFS `rc` viene eseguito solo per l’inizializzazione.

Il `docker-compose.yaml` principale contiene tutte le definizioni di Fuji, senza `extends`. `agents/compose.yaml` serve per l’installazione del solo Alloy su Ryzen. La cartella storage conserva gli script di bootstrap e la policy S3.

## Installazione iniziale

Prima del bootstrap copiare `.env.example` in `.env`. Le variabili `*_IMAGE`
contengono il riferimento completo delle immagini (repository, tag ed eventuale
digest); Compose le richiede esplicitamente. `.env` resta locale e ignorato da
Git, `.env.example` registra le versioni stabili verificate. I segreti dei servizi
rimangono nei file separati sotto `runtime/`.

Per aggiornare un'installazione esistente, riportare le variabili `*_IMAGE`
da `.env.example` nel suo `.env`, preservando `MONITORING_BIND_IP` e gli altri
valori locali. `sh scripts/prepare-env . .env` aggiunge le variabili mancanti
senza sovrascrivere quelle già impostate, anche durante l'installazione.
Un `git pull` da solo non cambia le immagini selezionate.
Eseguire `bash scripts/validate`, poi `docker compose pull` e
`docker compose up -d`. Il manifest del collector si valida dalla radice con
`docker compose --env-file .env -f agents/compose.yaml config -q`.
Validazione e prove S3 usano le immagini risolte da Compose; lo smoke copia il
`.env` locale nella propria directory isolata.

Versioni stabili verificate il 2026-09-25: [Prometheus 3.15.0](https://github.com/prometheus/prometheus/releases/tag/v3.15.0),
[Grafana 13.2.2](https://github.com/grafana/grafana/releases/tag/v13.2.2),
[Loki 3.7.8](https://github.com/grafana/loki/releases/tag/v3.7.8),
[Alloy 1.20.0](https://github.com/grafana/alloy/releases/tag/v1.20.0),
[Nginx stable 1.30.5](https://nginx.org/en/download.html),
[Alertmanager 0.34.1](https://github.com/prometheus/alertmanager/releases/tag/v0.34.1),
[RustFS 1.0.0](https://github.com/rustfs/rustfs/releases/tag/1.0.0) e
[RustFS rc 0.1.36](https://github.com/rustfs/cli/releases/tag/v0.1.36).

`python3 scripts/bootstrap` crea segreti nuovi e rifiuta sovrascritture. Fuji richiede tutti i file runtime, compreso `goose.htpasswd`, e il proprio file agente; Ryzen solo `runtime/agents/ryzen5lenovo.env`. Il primo setup host usa `sudo bash scripts/install-host` per filesystem e permessi. Successivamente si usa solo Compose. Non sono installati supervisori systemd del progetto.

Su Fuji inizializzazione bucket/account (ripetibile):

```sh
docker compose up -d --wait --wait-timeout 180 rustfs
docker compose --profile bootstrap run --rm init
docker compose up -d
```

Il bootstrap usa `RC_IMAGE` (`rustfs/rc`, versione e digest espliciti): crea il
bucket Loki, l’utente dedicato e la policy limitata al bucket. Non richiede MinIO.
Gli alias sono passati tramite `RC_HOST_*`; la home temporanea del client è in
RAM e il container viene rimosso al termine. Per migrare un vecchio `.env`,
eseguire `sh scripts/prepare-env . .env` e rimuovere la voce obsoleta `MC_IMAGE`.
Non è necessario rieseguire il bootstrap per un'installazione già inizializzata.

`python3 scripts/check-rustfs-bootstrap` collauda due bootstrap consecutivi e
le operazioni S3 con accesso negato a un altro bucket, su un RustFS temporaneo
senza porte pubblicate, dati di produzione o credenziali esistenti. Richiede
Docker e rimuove container e rete di test anche in caso di errore.

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
