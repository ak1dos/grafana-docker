# Homelab monitoring

## Distribuzione

- **Fuji:** Grafana, Prometheus, Loki, RustFS, gateway di ingestione e Alloy, nello stesso progetto `homelab-monitoring`.
- **Ryzen:** soltanto Alloy, progetto `homelab-telemetry`.
- Entrambi gli agenti inviano metriche e log al gateway autenticato `10.20.0.1:3100` attraverso WireGuard.
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

Le credenziali runtime appartengono a `mika`, directory 0700 e file 0600; i manifest/configurazioni sono leggibili dai container. Non stampare `docker compose config` senza `-q`: contiene segreti.

## Accesso Grafana e RustFS

Dal Mac:

```sh
ssh -N -L 3000:127.0.0.1:13000 -L 9001:127.0.0.1:9001 mika@192.168.1.54
```

Grafana: http://localhost:3000, utente `admin`, password in `runtime/grafana.env` su Fuji. Console RustFS: http://localhost:9001, credenziali in `runtime/rustfs.env`. Il bucket Loki usa un account separato limitato al bucket `loki`; il client mc è solo uno strumento di inizializzazione, non un server MinIO.

## Installazione iniziale

`python3 scripts/bootstrap` crea segreti nuovi e rifiuta sovrascritture. Fuji richiede tutti i file runtime e il proprio file agente; Ryzen solo `runtime/agents/ryzen5lenovo.env`. Il primo setup host usa `sudo bash scripts/install-host` per filesystem e permessi. Successivamente si usa solo Compose. Non sono installati supervisori systemd del progetto.

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
