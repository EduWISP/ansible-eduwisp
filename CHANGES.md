# Changelog — ansible-eduwisp

## Non rilasciato / Unreleased

- Creazione del repository (fase di progettazione). / *Repository created (design phase).*
- Licenza AGPL-3.0-or-later con termini aggiuntivi (sezione 7), publiccode.yml e controllo DCO. / *AGPL-3.0-or-later licence with additional terms, publiccode.yml and DCO check.*
- Prototipo v0: ruolo per Debian 13 con applicazione, PostgreSQL, nginx/TLS, firewall nftables, fail2ban, Suricata, AIDE, auditd e hardening. / *v0 prototype: Debian 13 role with app, PostgreSQL, nginx/TLS, nftables, fail2ban, Suricata, AIDE, auditd and hardening.*
- Valkey e Celery (worker e beat) per le attività in background (ADR-0016, #5). / *Valkey and Celery worker/beat (ADR-0016).*
- Backup con BorgBackup e prova di ripristino mensile (ADR-0016, #6). / *BorgBackup backups with monthly restore test.*
