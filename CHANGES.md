# Changelog — ansible-eduwisp

## Non rilasciato / Unreleased

- Creazione del repository (fase di progettazione). / *Repository created (design phase).*
- Licenza AGPL-3.0-or-later con termini aggiuntivi (sezione 7), publiccode.yml e controllo DCO. / *AGPL-3.0-or-later licence with additional terms, publiccode.yml and DCO check.*
- Prototipo v0: ruolo per Debian 13 con applicazione, PostgreSQL, nginx/TLS, firewall nftables, fail2ban, Suricata, AIDE, auditd e hardening. / *v0 prototype: Debian 13 role with app, PostgreSQL, nginx/TLS, nftables, fail2ban, Suricata, AIDE, auditd and hardening.*
- Valkey e Celery (worker e beat) per le attività in background (ADR-0016, #5). / *Valkey and Celery worker/beat (ADR-0016).*
- Backup con BorgBackup e prova di ripristino mensile (ADR-0016, #6). / *BorgBackup backups with monthly restore test.*
- Monitoraggio con Monit, avvisi via email (msmtp), avviso sui fallimenti dei backup, riepilogo quotidiano di sicurezza (#7). / *Monit monitoring, email alerts, backup failure alerts, daily security summary.*
- Amministratore gestito da Ansible con password dal vault. / *Admin account managed from the vault.*
- Limiti di richieste su nginx e conservazione dei log a 90 giorni al massimo (#8). / *nginx rate limiting and 90-day log retention.*
- Rilascio della piattaforma 0.1.0 con le versioni dei moduli fissate per commit; il ruolo non aggiorna più i moduli da solo. / *Platform release 0.1.0 pinning module commits; the role no longer upgrades modules implicitly.*
- Rilascio 0.2.0: aggiunge `eduwisp-utils` con l'endpoint `/health/`, usato da Monit e dalla verifica dell'aggiornamento (eduwisp-utils#3). / *Release 0.2.0 adds `/health/`, used by Monit and upgrade checks.*
- I servizi dell'applicazione non si fermano più quando PostgreSQL o Valkey si riavviano (`Wants=` al posto di `Requires=`): prima restavano spenti. / *App services no longer stop (and stay down) when PostgreSQL or Valkey restart.*
- Aggiornamento con un solo comando (`aggiorna.yml`): punto di ripristino, pagina di manutenzione, migrazioni, verifica e **ripristino automatico** in caso di errore, con avviso email (#9). / *One-command upgrade with restore point, maintenance page, verification and automatic rollback.*
