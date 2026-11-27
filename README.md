<p align="center"><img src="https://raw.githubusercontent.com/EduWISP/.github/main/branding/eduwisp-mark.svg" alt="EduWISP" height="72"></p>

# ansible-eduwisp

**Installazione con Ansible** · *Ansible deployment*

Ruolo Ansible per installare e aggiornare EduWISP su Debian GNU/Linux 13 (Trixie).

> 🧪 **Stato: prototipo v0.** Ruolo funzionante: installa `demo.eduwisp.org` (ADR-0015). La progettazione è nella [documentazione EduWISP](https://eduwisp.org/docs/architettura/deployment/).

🇬🇧 *Ansible role to install and upgrade EduWISP on Debian GNU/Linux 13 (Trixie). **Status: design phase**, no code yet. See the [design docs](https://eduwisp.org/docs/en/architecture/deployment/).*

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
| Backup | **BorgBackup** cifrato (repokey-blake2): dump notturno del database e della configurazione, conservazione 7/4/6, **prova di ripristino automatica mensile** in un database temporaneo. Archivio locale o remoto via SSH (consigliato: remoto in modalità *append-only*) |
| Monitoraggio e avvisi | **Monit** (servizi, disco, memoria, carico, risposta HTTPS e scadenza del certificato), invio della posta con **msmtp** tramite un relay SMTP autenticato, **avviso immediato** se il backup o la prova di ripristino falliscono, **riepilogo quotidiano** di sicurezza (allarmi Suricata, fail2ban, backup, certificato, aggiornamenti) |
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
