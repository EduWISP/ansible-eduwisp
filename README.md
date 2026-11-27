<p align="center"><img src="https://raw.githubusercontent.com/EduWISP/.github/main/branding/eduwisp-mark.svg" alt="EduWISP" height="72"></p>

# ansible-eduwisp

**Installazione con Ansible** · *Ansible deployment*

Ruolo Ansible per installare e aggiornare EduWISP su Debian GNU/Linux 13 (Trixie).

> 🧪 **Stato: prototipo v0.** Ruolo funzionante: installa `demo.eduwisp.org` (ADR-0015). La progettazione è nella [documentazione EduWISP](https://eduwisp.org/docs/architettura/deployment/).

🇬🇧 *Ansible role to install and upgrade EduWISP on Debian GNU/Linux 13 (Trixie). **Status: prototype v0**: working role, installs `demo.eduwisp.org`; safe upgrades with automatic rollback. See the [design docs](https://eduwisp.org/docs/en/architecture/deployment/).*

## Documentazione / Documentation

- Progettazione / Design: <https://eduwisp.org/docs/architettura/deployment/>
- Mappa dei repository / Repository map: <https://eduwisp.org/docs/architettura/repository/>
- Documentazione del modulo / Module docs: [`docs/user/`](docs/user/) · [`docs/developer/`](docs/developer/)

## Cosa installa / What it installs

| Area | Componenti |
|---|---|
| Applicazione | Moduli EduWISP in un ambiente virtuale, Django 5.2 LTS, gunicorn come servizio systemd **isolato** (esposizione 1,7/10 secondo `systemd-analyze security`) |
| Attività in background | **Valkey** (solo socket Unix locale, con password, persistenza AOF) e **Celery** worker e beat, isolati come gunicorn |
| Dati | PostgreSQL 17 con autenticazione locale (nessuna password), configurazione non leggibile da altri utenti |
| Web | nginx con HTTPS (TLS 1.2/1.3), HSTS, header di sicurezza, **limiti di richieste** su registrazione dei dispositivi e accesso all'amministrazione (429); **certificato fornito dall'esterno** (per esempio ACME via DNS). Senza certificato: solo HTTP e `/admin/` limitato alle reti locali |
| Backup | **BorgBackup** cifrato (repokey-blake2): dump notturno del database e della configurazione, conservazione 7/4/6, **prova di ripristino automatica mensile** in un database temporaneo. Archivio remoto via SSH sul **server di backup dedicato** ([`ansible-eduwisp-backup`](https://github.com/EduWISP/ansible-eduwisp-backup), ADR-0017), in sola aggiunta; l'archivio locale resta solo per le prove |
| Monitoraggio e avvisi | **Monit** (servizi, disco, memoria, carico, risposta HTTPS e scadenza del certificato), invio della posta con **msmtp** tramite un relay SMTP autenticato, **avviso immediato** se il backup o la prova di ripristino falliscono, **riepilogo quotidiano** di sicurezza (allarmi Suricata, fail2ban, backup, certificato, aggiornamenti) |
| App consentite | Dal rilascio 0.5.0: [`eduwisp-apps`](https://github.com/EduWISP/eduwisp-apps), elenco di app consentite per istituto, indirizzo e classe e sblocchi temporanei dei docenti (ADR-0019) |
| Interfaccia per ruoli | Dal rilascio 0.3.0: [`eduwisp-portal`](https://github.com/EduWISP/eduwisp-portal) con le pagine di dirigente, docente e famiglia, l'area dell'amministratore e il **«vedi come» in sola lettura**, registrato in [`eduwisp-audit`](https://github.com/EduWISP/eduwisp-audit) (ADR-0018); accesso da `/accedi/` con lo stesso limite di richieste dell'amministrazione |
| Amministratore | Creato o aggiornato da Ansible con la password presa dal vault (almeno 12 caratteri), senza mai mostrarla nei log |
| Firewall | nftables: in ingresso solo SSH, HTTP, HTTPS e l'ICMP necessario; limite di nuove connessioni SSH |
| Prevenzione intrusioni | fail2ban (SSH, nginx, recidive) |
| IDS | **Suricata** con regole ET Open aggiornate ogni giorno; **AIDE** per l'integrità dei file; **auditd** |
| Log | journald persistente, **al massimo 90 giorni** e 1 GB; Suricata 30 giorni; nginx 14 giorni; accesso solo agli amministratori |
| Hardening | parametri del kernel e della rete, SSH solo con chiavi e cifrari moderni (con ripristino automatico se la configurazione non è valida), niente core dump, aggiornamenti di sicurezza automatici |

Su `server.eduwisp.org` l'audit **Lynis** dà un indice di hardening di **78/100**. Il ruolo è idempotente.

## Uso / Usage

```bash
ansible-galaxy collection install -r requirements.yml
cp examples/inventory.example.yml ~/eduwisp-inventory.yml   # e adattalo
ANSIBLE_ROLES_PATH=.. ansible-playbook -i ~/eduwisp-inventory.yml examples/playbook.yml
```

Le variabili sono in [`defaults/main.yml`](defaults/main.yml). **Non pubblicare il tuo inventario**: contiene indirizzi e impostazioni della tua rete.

### Segreti

Password SMTP e password dell'amministratore vanno tenute in un file cifrato con **ansible-vault**, mai in chiaro nell'inventario:

```yaml
# inventario
eduwisp_smtp_password: "{{ vault_smtp_password }}"
eduwisp_admin_password: "{{ vault_admin_password }}"
```

Gli altri segreti (chiave di Django, password di Valkey, passphrase di Borg) vengono **generati sul server** alla prima installazione. Esporta subito chiave e passphrase di Borg e conservale fuori dal server: senza di esse i backup sono illeggibili.

### Backup remoto

1. Imposta `eduwisp_backup_repo: "ssh://borg@<server-di-backup>:<porta>/srv/borg/repos/<nome-del-server>"` e applica il ruolo: crea la chiave `/root/.ssh/eduwisp_backup` (l'inizializzazione dell'archivio fallisce finché il server di backup non la conosce).
2. Copia `/root/.ssh/eduwisp_backup.pub` in `eduwisp_bk_clients` di [`ansible-eduwisp-backup`](https://github.com/EduWISP/ansible-eduwisp-backup) e applica quel ruolo.
3. Applica di nuovo questo ruolo: crea l'archivio cifrato. Esporta subito chiave (`borg key export --paper`) e passphrase.

## Dati di esempio (solo demo) / Demo data

Con `eduwisp_demo_data: true` il ruolo carica un **liceo scientifico inventato**: 6 sezioni (A-D ordinamento, E-F scienze applicate) per 5 anni, cioè 30 classi, circa 700 studenti, preside, amministratore IT, docenti con le discipline del liceo, coordinatori, sostegno, tablet personali per il biennio e un carrello condiviso per sezione. Dal rilascio 0.3.0 anche le **famiglie** (ADR-0018): un referente per ogni studente e spesso un secondo genitore, casi con un solo genitore, tutori, affidatari, collegamenti disattivati e fratelli. Dal rilascio 0.4.0 anche le **date della maggiore età** e le scelte degli studenti maggiorenni sull'accesso dei familiari. Nomi generati a caso, indirizzi email sul dominio riservato `.invalid`, nessuna persona reale. Lo script è [`files/demo_data.py`](files/demo_data.py).

Funziona solo se è impostato `eduwisp_environment_notice` (ambiente di prova, ADR-0015) e carica i dati una volta sola; `eduwisp_demo_data_reset: true` li ricrea da zero.

🇬🇧 *`eduwisp_demo_data: true` loads a made-up scientific high school (6 sections × 5 years, ~700 students, teachers, devices). Test environments only; fully fictitious.*

## Aggiornamento / Upgrade

Le versioni dei moduli sono fissate da un **rilascio della piattaforma** ([`releases/`](releases/), ADR-0016): per ogni modulo, il commit esatto. Il ruolo installa i moduli **solo alla prima installazione**; se trova versioni diverse da quelle del rilascio si ferma, per non cambiare il database senza backup.

Per aggiornare basta un comando:

```bash
ANSIBLE_ROLES_PATH=.. ansible-playbook -i ~/eduwisp-inventory.yml examples/aggiorna.yml -e eduwisp_platform_release=0.5.0
```

La procedura:

1. **controlli**: servizi attivi, spazio libero, nessuna migrazione in sospeso;
2. **punto di ripristino**: backup con BorgBackup, copia del database (`pg_dump`), dell'ambiente Python e del progetto in `/var/backups/eduwisp/aggiornamenti/` (restano gli ultimi 3);
3. **manutenzione**: nginx risponde 503 con una pagina bilingue e `Retry-After`; i dispositivi continuano ad applicare le regole già ricevute e riprovano più tardi; i controlli di Monit sull'applicazione sono sospesi;
4. **installazione** dei moduli del rilascio, migrazioni, file statici, `manage.py check`;
5. **verifica**: risposte dell'applicazione chieste direttamente a gunicorn (compreso `/health/` dal rilascio 0.2.0), worker di Celery, nessuna migrazione in sospeso, servizi attivi; poi la manutenzione viene tolta.

**Se un passo fallisce**, il ruolo ripristina da solo ambiente Python, progetto e database (ricreato da zero dalla copia, così spariscono anche le tabelle di migrazioni a metà), riavvia i servizi, verifica, toglie la manutenzione e manda un avviso email. Il servizio non resta mai in uno stato a metà.

Dopo un aggiornamento esegui di nuovo il playbook normale: applica le configurazioni che dipendono dal rilascio (per esempio Monit su `/health/`). Se anche la verifica dopo il ripristino fallisce, la pagina di manutenzione resta attiva e l'avviso chiede un intervento manuale.

Per provare il ripristino: `-e eduwisp_upgrade_simulate_failure=true` fa fallire l'aggiornamento subito dopo le migrazioni. Per lo sviluppo, `eduwisp_modules` permette di indicare rami o commit al posto del rilascio.

🇬🇧 *Module versions are pinned by a platform release (`releases/`). The role installs modules only on first install and stops if versions differ. Upgrade with `examples/aggiorna.yml`: pre-checks, restore point (Borg backup, `pg_dump`, venv and project copies), maintenance page (HTTP 503), install, migrate, verify. On any failure it restores venv, project and database automatically, verifies, and emails the admins.*

## Dipendenze / Dependencies

tutti i moduli server

## Privacy

Dati personali previsti e regole: [PRIVACY.md](PRIVACY.md). Il rispetto della normativa su privacy e minori è un vincolo bloccante ([ADR-0008](https://eduwisp.org/docs/decisioni/0008-conformita-normativa/)).

## Responsabile del modulo / Module owner

Cerchiamo persone che vogliano prendere in carico questo modulo! Proponiti in [Discussions](https://github.com/EduWISP/docs/discussions). / *Want to own this module? Say hi in Discussions.*

## Contribuire / Contributing

Vedi [CONTRIBUTING](https://github.com/EduWISP/.github/blob/main/CONTRIBUTING.md) e il [Codice di condotta](https://github.com/EduWISP/.github/blob/main/CODE_OF_CONDUCT.md). **Mai dati personali reali** di studenti, famiglie o personale.

## Licenza / License

**AGPL-3.0-or-later**, con termini aggiuntivi di attribuzione e tutela del nome (sezione 7): vedi [LICENSE](LICENSE) e [NOTICE.md](NOTICE.md). Chi usa o modifica EduWISP deve sempre indicare «Basato su EduWISP» e non può usare il nome e il logo per versioni modificate. Licenza scelta secondo le [linee guida AgID](https://eduwisp.org/docs/decisioni/0006-licenza/) per il software usato via rete.

*AGPL-3.0-or-later with additional attribution and trademark terms (section 7): see LICENSE and NOTICE.md.*

I contributi richiedono il [DCO](https://github.com/EduWISP/.github/blob/main/CONTRIBUTING.md#dco) (`git commit -s`).
