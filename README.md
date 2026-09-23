# Homelab monitoring — RustFS

Backend Grafana/Prometheus/Loki su Ryzen; RustFS sul DAS Fuji; Alloy indipendente su entrambi. Repository dedicato proposto `homelab-monitoring`, successore di `grafana-docker`. La scelta RustFS è confermata dall’utente il 2026-09-23. Il materiale storico Garage resta nelle evidenze del 13 settembre, non descrive il deployment corrente.

## Componenti e accesso

- RustFS 1.0.0 fissato per digest; S3 `10.20.0.1:19000`, console soltanto `127.0.0.1:9001` su Fuji.
- Dataset `tank/observability`, quota iniziale 128 GiB; sottocartelle `rustfs/data` e `rustfs/logs`, UID 10001. Non condiviso NFS, distinto da backup/documenti/media. Il mirror hardware è visto come un unico dispositivo: nessuna finta distribuzione su quattro cartelle e nessuna HA tra sedi.
- Grafana loopback 3000 su Ryzen; Prometheus e Loki senza porte host. Gateway ingestione su VPN 3100, autenticato per host.
- Prometheus 15 giorni/8 GB, Loki 30 giorni; WAL/cache/compactor su SSD Ryzen, oggetti S3 sul DAS Fuji. Il limite TSDB non include tutto il WAL: mantenere margine SSD.
- Alloy: Unix/cAdvisor integrati, metriche host/container e log Docker/journald. Container amministrativo privilegiato, UI solo loopback 12345; il socket Docker equivale a root anche se montato read-only.
- Allarmi configurati e visibili in Prometheus; notifiche email/push e heartbeat esterno non configurati.

## Directory host

Tutti i servizi girano in Docker. I dati persistenti sono bind mount espliciti, secondo la convenzione dei server:

| Host | Dati | Directory host |
|---|---|---|
| Ryzen | Prometheus | `/srv/homelab-monitoring/prometheus` |
| Ryzen | Loki WAL, indice e cache | `/srv/homelab-monitoring/loki` |
| Ryzen | Grafana | `/srv/homelab-monitoring/grafana` |
| Entrambi | Alloy WAL e posizioni | `/srv/homelab-monitoring/alloy` |
| Fuji | RustFS oggetti e log | `/tank/observability/rustfs/{data,logs}` |

Manifest, configurazioni e segreti vengono installati in `/opt/applications/homelab-monitoring`. L’installer crea le directory dati con UID/GID delle immagini; `create_host_path: false` impedisce la creazione implicita di directory con proprietario errato. Se rileva volumi nominati del precedente layout si ferma, per richiedere una migrazione esplicita dei dati. Questi bind mount non aggiungono automaticamente copertura al backup.

## Preparare segreti

```sh
python3 scripts/bootstrap
```

Genera `runtime/` con permessi 0700 e file 0600, rifiuta sovrascritture. Admin RustFS, segreto RPC e account Loki sono separati. Non stampare `docker compose config` senza `-q`, né committare runtime. Il client `mc` serve solo a configurare RustFS; non viene installato un server MinIO.

Trasferimento privato:

- Fuji: `runtime/rustfs.env`, `runtime/loki.env`, `runtime/agents/fujiserver.env`.
- Ryzen: `runtime/loki.env`, `runtime/grafana.env`, `runtime/ingest.htpasswd`, `runtime/agents/ryzen5lenovo.env`.

Conservare una copia indipendente dei segreti. Il backup core esistente non include automaticamente questi nuovi volumi/configurazioni.

## Installazione

Dal checkout preparato, prima su Fuji e poi su Ryzen:

```sh
sudo bash scripts/install-host
```

Riconosce soltanto i due hostname, verifica dataset/mount, prepara sottodirectory UID 10001, copia configurazione e assegna le credenziali private a `mika` in `/opt/applications/homelab-monitoring`, disabilita le precedenti unità systemd del progetto e inizializza bucket/account RustFS. Se UFW è attivo autorizza S3 solo dal peer Ryzen su wg0. Non cancella volumi o dati preesistenti; non modifica la quota di un dataset già presente.

La gestione ordinaria usa Docker Compose e restart `unless-stopped`. Il container RustFS verifica il mount ZFS prima di avviare il processo. Se il DAS manca rifiuta l’avvio; non scrive su una directory SSD sostitutiva. L’indirizzo VPN deve essere disponibile. Il bootstrap è ripetibile e non ruota credenziali esistenti.

Per un’installazione già presente, applicare una volta i nuovi permessi con `sudo bash scripts/setup-compose-access`. Il comando non riavvia servizi e non cambia proprietari dei dati sotto `/srv` o sul DAS.

## Gestione Docker

Dalla directory `/opt/applications/homelab-monitoring`:

```sh
# Fuji: storage
docker compose -f storage/compose.yaml up -d
docker compose -f storage/compose.yaml ps
docker compose -f storage/compose.yaml logs --tail 100 -f rustfs
docker compose -f storage/compose.yaml restart rustfs
# Inizializzazione bucket, una volta o dopo ripristino
docker compose -f storage/compose.yaml --profile bootstrap run --rm init
# Ryzen: backend
docker compose up -d
docker compose ps
# Entrambi: agent
docker compose -f agents/compose.yaml up -d
docker compose -f agents/compose.yaml logs --tail 100 alloy
```

`stop` ferma, `start` riavvia, `down` rimuove i container lasciando i bind mount sull’host. Non cancellare le directory dati. Le credenziali sono leggibili solo da `mika` e root (directory 0700, file 0600). Il comando Docker Compose non richiede sudo; l’installer root serve solo a preparare filesystem, permessi e firewall. Non occorrono comandi systemctl nella gestione ordinaria.

## Accesso UI

```sh
# Console RustFS
ssh -N -L 9001:127.0.0.1:9001 mika@192.168.1.54
# Grafana
ssh -N -J mika@192.168.1.54 -L 3000:127.0.0.1:3000 mika@192.168.68.107
```

Console su http://localhost:9001, credenziali in rustfs.env. Grafana http://localhost:3000, utente admin e password in grafana.env. Nessun accesso pubblico aggiunto.

## Verifiche

```sh
cp runtime/agents/ryzen5lenovo.env runtime/agent.env
bash scripts/validate
```

Test nativi: Compose, promtool, Loki verify-config, Alloy validate, nginx -t; bootstrap verifica permessi, separazione credenziali e rifiuto sovrascritture.

Smoke isolato:

```sh
python3 scripts/prepare-smoke
cd /private/tmp/homelab-rustfs-smoke
docker compose up -d rustfs
docker compose --profile bootstrap run --rm init
docker compose up -d
```

Porte localhost: 13300 Grafana, 13310 Loki, 13311 gateway, 13909 Prometheus, 13900 S3. Solo nel test `/loki` è tmpfs per evitare interferenze della soglia disco di Docker Desktop; in produzione rimane persistente su SSD.

Dal percorso dello smoke:

```sh
docker run -d --name homelab-rustfs-smoke-alloy --network homelab-rustfs-smoke_default --env-file runtime/agents/fujiserver.env -v "$PWD/smoke.alloy:/etc/alloy/config.alloy:ro" grafana/alloy:v1.19.2 run /etc/alloy/config.alloy
docker run --rm --network homelab-rustfs-smoke_default --env-file runtime/rustfs.env --env-file runtime/loki.env -v "$PWD/storage/test-s3.sh:/test.sh:ro" --entrypoint /bin/sh quay.io/minio/mc:RELEASE.2025-08-13T08-35-41Z /test.sh
```

Poi dal repository: `python3 scripts/check-smoke` e `python3 scripts/check-s3-recovery`. [Evidenze del collaudo](docs/validation-2026-09-23.md). Rimuovere solo i container/volumi con prefisso `homelab-rustfs-smoke` dopo il collaudo.

## Controlli live e rollback

Controllare `docker compose ps` per ciascuno dei manifest installati. Verificare `node_uname_info` e CPU/RAM container per entrambi; in Loki Docker/journald con etichette host corrette. Emettere un marker `logger` e controllarne l’arrivo. Misurare RAM, swap, OOM e crescita dataset. Limiti iniziali RustFS 768 MiB, Alloy 384 MiB: non sono una promessa di capacità. Collaudare reboot e DAS assente in finestra dedicata.

Rollback: fermare solo i container del progetto e preservare volumi/dataset. Nessuna riconversione automatica RustFS→Garage/MinIO. Vecchi repository GitHub restano intatti fino al collaudo live.
