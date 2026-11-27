# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Michele Salerno e i contributori di EduWISP
"""Dati di esempio per l'ambiente demo (ADR-0015). TUTTI INVENTATI: nessuna persona reale.

Liceo scientifico piccolo: 2 sezioni (A ordinamento, B scienze applicate) e 5 anni, cioè
10 classi, 50 studenti e 13 docenti. Tablet personali per il biennio, un carrello condiviso
per sezione.
Famiglie (ADR-0018): un referente per studente e spesso un secondo familiare; casi con un solo
genitore, tutori, affidatari, un collegamento disattivato e fratelli nello stesso istituto.
Maggiorenni: data della maggiore età per tutti; chi è già maggiorenne ha scelto (o non ancora)
se lasciare l'accesso ai familiari, come farebbe dal tablet.

Uso: manage.py shell < demo_data.py   (EDUWISP_DEMO_RESET=1 per ricreare tutto)
Idempotente: se l'istituto di esempio esiste già non cambia nulla.
"""

import os
import random
from datetime import date, datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from eduwisp_devices.models import Device, DeviceAssignment, DevicePolicy, EnrollmentToken
from django.contrib.auth.models import Group
try:  # app consentite dal rilascio 0.5.0 (ADR-0019)
    from eduwisp_apps.models import App, AppPolicyState, AppRule, TemporaryUnlock
except ImportError:
    App = None
try:  # richieste di app dal rilascio 0.7.0 (ADR-0021)
    from eduwisp_apps.models import AppRequest
except ImportError:
    AppRequest = None
from eduwisp_devices.secrets import hash_secret, new_secret
from eduwisp_school.models import (
    ADULT_AGE,
    AssignmentKind,
    Guardian,
    GuardianKind,
    SchoolClass,
    SchoolLevel,
    SchoolYear,
    Section,
    Site,
    Student,
    StudentEnrollment,
    TeachingAssignment,
    Track,
    born_by,
)
from eduwisp_users.models import Membership, Organization, Role

SLUG = "liceo-esempio"
NOME = "Liceo Scientifico «Città di Esempio» (dati fittizi)"
DOMINIO_EMAIL = "liceo-esempio.invalid"  # .invalid: dominio riservato, non esiste (RFC 2606)
SEZIONI = "AB"
SCIENZE_APPLICATE = "B"
STUDENTI_PER_CLASSE = (5, 5, 5, 5, 5)  # dal primo al quinto anno: 50 studenti

NOMI = """Alessandro Alice Andrea Anna Antonio Arianna Aurora Beatrice Bianca Camilla Carlo Caterina
Chiara Christian Cristina Daniele Davide Diego Edoardo Elena Elisa Emanuele Emma Enea Federica
Federico Filippo Francesca Francesco Gabriele Gaia Giacomo Giada Ginevra Giorgia Giorgio Giovanni
Giulia Giulio Greta Irene Jacopo Laura Leonardo Lorenzo Luca Lucia Ludovica Marco Margherita Maria
Martina Matilde Matteo Mattia Michele Nicola Noemi Paolo Pietro Rachele Riccardo Roberto Samuele
Sara Simone Sofia Stefano Tommaso Valentina Viola Vittoria""".split()
COGNOMI = """Amato Barbieri Bellini Benedetti Bernardi Bianchi Bruno Caruso Cattaneo Colombo Conti
Costa D'Angelo De Luca De Santis Esposito Fabbri Farina Ferrara Ferrari Ferri Fiore Fontana Galli
Gallo Gentile Giordano Greco Guerra Leone Lombardi Lombardo Longo Mancini Marchetti Mariani Marini
Martinelli Martini Messina Monti Morelli Moretti Neri Orlando Palumbo Parisi Pellegrini Rinaldi Rizzi
Rizzo Romano Rossetti Rossi Ruggiero Russo Sala Sanna Santoro Serra Silvestri Testa Valentini Villa
Vitale""".split()

# Discipline del liceo scientifico: (nome, anni). Per sezione intera se valgono per tutti e 5.
DISCIPLINE = [
    ("Lingua e letteratura italiana", (1, 2, 3, 4, 5)),
    ("Matematica", (1, 2, 3, 4, 5)),
    ("Fisica", (1, 2, 3, 4, 5)),
    ("Lingua e cultura inglese", (1, 2, 3, 4, 5)),
    ("Scienze naturali", (1, 2, 3, 4, 5)),
    ("Disegno e storia dell'arte", (1, 2, 3, 4, 5)),
    ("Scienze motorie e sportive", (1, 2, 3, 4, 5)),
    ("Religione cattolica", (1, 2, 3, 4, 5)),
    ("Storia e geografia", (1, 2)),
    ("Storia e filosofia", (3, 4, 5)),
]
SOLO_ORDINAMENTO = [("Lingua e cultura latina", (1, 2, 3, 4, 5))]
SOLO_SCIENZE_APPLICATE = [("Informatica", (1, 2, 3, 4, 5))]

rnd = random.Random(2026)  # sempre gli stessi dati
User = get_user_model()
usati = set()


def persona(cognome=None):
    for _ in range(1000):
        nome, c = rnd.choice(NOMI), cognome or rnd.choice(COGNOMI)
        if (nome, c) not in usati:
            usati.add((nome, c))
            return nome, c
    return persona()  # cognome esaurito: se ne sceglie un altro


def utente(ruolo_org, org, prefisso="", cognome=None):
    nome, cognome = persona(cognome)
    base = f"{prefisso}{nome}.{cognome}".lower().replace("'", "").replace(" ", "")
    user = User(
        username=base,
        first_name=nome,
        last_name=cognome,
        email=f"{base}@{DOMINIO_EMAIL}",
    )
    user.set_unusable_password()  # accessi demo per ruolo: quando ci sarà l'interfaccia
    user.save()
    Membership.objects.create(user=user, organization=org, role=ruolo_org)
    return user


@transaction.atomic
def elimina():
    """Tutto o niente: un errore non lascia la demo a metà."""
    org = Organization.objects.filter(slug=SLUG).first()
    if org is None:
        return
    utenti = User.objects.filter(email__endswith="@" + DOMINIO_EMAIL)
    if App is not None:
        if AppRequest is not None:
            AppRequest.objects.filter(organization=org).delete()
        for model in (TemporaryUnlock, AppRule, App, AppPolicyState):
            model.objects.filter(organization=org).delete()
    for model in (
        Guardian, DeviceAssignment, TeachingAssignment, StudentEnrollment, Device, DevicePolicy,
        EnrollmentToken,
    ):
        model.objects.filter(organization=org).delete()
    for model in (SchoolClass, Student, Section, Track, SchoolYear, Site):
        model.objects.filter(organization=org).delete()
    Membership.objects.filter(organization=org).delete()
    utenti.delete()
    org.delete()


@transaction.atomic
def crea():
    org = Organization.objects.create(name=NOME, slug=SLUG)
    sede = Site.objects.create(
        organization=org, name="Sede centrale", level=SchoolLevel.SECONDARIA_2, code="DEMO-PS-01"
    )
    ordinamento = Track.objects.create(organization=org, site=sede, name="Liceo scientifico")
    applicate = Track.objects.create(
        organization=org, site=sede, name="Liceo scientifico, opzione scienze applicate"
    )
    anno = SchoolYear.objects.create(
        organization=org,
        label="2026/2027",
        start_date=date(2026, 9, 14),
        end_date=date(2027, 6, 9),
        is_current=True,
    )

    utente(Role.SCHOOL_ADMIN, org, prefisso="preside.")
    utente(Role.IT_ADMIN, org, prefisso="it.")

    sezioni, classi = {}, {}
    for lettera in SEZIONI:
        track = applicate if lettera in SCIENZE_APPLICATE else ordinamento
        sezioni[lettera] = Section.objects.create(
            organization=org, site=sede, name=lettera, track=track
        )
        for n in range(1, 6):
            classi[lettera, n] = SchoolClass.objects.create(
                organization=org, school_year=anno, section=sezioni[lettera], year_number=n
            )

    # Studenti e iscrizioni
    codice = 0
    iscritti = {}
    for (lettera, n), classe in classi.items():
        iscritti[classe] = []
        for _ in range(STUDENTI_PER_CLASSE[n - 1]):
            codice += 1
            nome, cognome = persona()
            # Nati nel 2013 - n (la quinta compie 18 anni nel 2026); circa uno su dieci ha
            # ripetuto un anno ed è più grande dei compagni: l'età è di ognuno, non della classe.
            ripetente = rnd.random() < 0.1
            nascita = date(2013 - n - ripetente, 1, 1) + timedelta(days=rnd.randint(0, 364))
            maggiorenne_dal = nascita.replace(year=nascita.year + 18) if not (
                nascita.month == 2 and nascita.day == 29
            ) else date(nascita.year + 18, 3, 1)
            studente = Student.objects.create(
                organization=org, display_name=f"{cognome} {nome}", internal_code=f"S{codice:04d}",
                birth_date=nascita,
            )
            if maggiorenne_dal <= date.today():
                scelta = rnd.choices([True, False, None], weights=[55, 15, 30])[0]
                if scelta is not None:
                    studente.family_access_granted = scelta
                    deciso = timezone.make_aware(
                        datetime.combine(maggiorenne_dal, time(18)) + timedelta(days=rnd.randint(0, 20))
                    )
                    studente.family_access_decided_at = min(deciso, timezone.now())
                    studente.save()
            StudentEnrollment.objects.create(organization=org, student=studente, school_class=classe)
            iscritti[classe].append(studente)

    # Famiglie (ADR-0018): sempre un referente, spesso un secondo familiare con accesso.
    adesso = timezone.now()
    studenti = [st for elenco in iscritti.values() for st in elenco]
    rnd.shuffle(studenti)
    fratelli = {}
    for primo, secondo in zip(studenti[0:12:2], studenti[1:12:2]):  # 6 coppie di fratelli
        cognome = primo.display_name.split(" ")[0]
        secondo.display_name = f"{cognome} {secondo.display_name.split(' ', 1)[1]}"
        secondo.save(update_fields=["display_name"])
        fratelli[primo] = secondo
    gia_collegati = set(fratelli.values())

    def collega(persona_, figli, **campi):
        for figlio in figli:
            Guardian.objects.create(
                organization=org, user=persona_, student=figlio,
                verified_at=adesso - timedelta(days=rnd.randint(60, 400)), **campi,
            )

    for studente in studenti:
        if studente in gia_collegati:
            continue
        figli = [studente] + ([fratelli[studente]] if studente in fratelli else [])
        cognome = studente.display_name.split(" ")[0]
        caso = rnd.choices(
            ["due_genitori", "un_genitore", "tutore", "affidatario", "disattivato"],
            weights=[65, 26, 4, 3, 2],
        )[0]
        if caso == "tutore":
            collega(utente(Role.GUARDIAN, org, "fam."), figli, kind=GuardianKind.TUTORE,
                    is_primary=True)
            continue
        if caso == "affidatario":
            collega(utente(Role.GUARDIAN, org, "fam."), figli, kind=GuardianKind.AFFIDATARIO,
                    is_primary=True)
            continue
        collega(utente(Role.GUARDIAN, org, "fam.", cognome), figli, is_primary=True)
        if caso == "due_genitori":
            collega(utente(Role.GUARDIAN, org, "fam."), figli)
        elif caso == "disattivato":  # per esempio per un provvedimento: il motivo non si registra
            collega(utente(Role.GUARDIAN, org, "fam."), figli, is_active=False)

    # Docenti e incarichi
    condivisi = {}
    for i, lettera in enumerate(SEZIONI):
        discipline = DISCIPLINE + (
            SOLO_SCIENZE_APPLICATE if lettera in SCIENZE_APPLICATE else SOLO_ORDINAMENTO
        )
        for disciplina, anni in discipline:
            chiave = disciplina  # un docente per disciplina, in entrambe le sezioni
            if chiave in condivisi:
                docente = condivisi[chiave]
            else:
                docente = utente(Role.TEACHER, org)
                condivisi[chiave] = docente
            if len(anni) == 5:
                TeachingAssignment.objects.create(
                    organization=org, teacher=docente, school_year=anno,
                    section=sezioni[lettera], subject=disciplina,
                )
            else:
                for n in anni:
                    TeachingAssignment.objects.create(
                        organization=org, teacher=docente, school_year=anno,
                        section=sezioni[lettera], school_class=classi[lettera, n],
                        subject=disciplina,
                    )
    # Un coordinatore per classe, scelto tra i docenti della sezione
    for (lettera, n), classe in classi.items():
        docenti = list(
            User.objects.filter(
                teaching_assignments__section=sezioni[lettera]
            ).distinct().order_by("username")
        )
        TeachingAssignment.objects.create(
            organization=org, teacher=docenti[(n * 3) % len(docenti)], school_year=anno,
            section=sezioni[lettera], school_class=classe, kind=AssignmentKind.COORDINATORE,
        )
    # Due docenti di sostegno (RC-013: nessun abbinamento al singolo studente)
    for lettera, n in (("A", 1),):
        TeachingAssignment.objects.create(
            organization=org, teacher=utente(Role.TEACHER, org), school_year=anno,
            section=sezioni[lettera], school_class=classi[lettera, n],
            kind=AssignmentKind.SOSTEGNO,
        )

    # Dispositivi: tablet personali al biennio, un carrello per sezione al triennio
    DevicePolicy.objects.create(organization=org, camera_disabled=False, screen_capture_disabled=True)
    numero = 0

    def tablet(classe, studente=None):
        nonlocal numero
        numero += 1
        ritardo = rnd.choices(
            [timedelta(minutes=rnd.randint(1, 15)), timedelta(hours=rnd.randint(1, 20)),
             timedelta(days=rnd.randint(3, 12))],
            weights=[70, 25, 5],
        )[0]
        conforme = rnd.random() > 0.06
        device = Device.objects.create(
            organization=org,
            display_name=f"TAB-{numero:04d}",
            platform="android",
            agent_version="0.1.0",
            os_version=rnd.choice(["14", "15", "15"]),
            model="Tablet di prova 10\"",
            capabilities=["setting:camera_disabled", "setting:screen_capture_disabled"],
            secret_hash=hash_secret(new_secret()),  # credenziale scartata: non si collega
            last_seen_at=adesso - ritardo,
            policy_version_applied=1,
            compliant=conforme,
            non_compliance=[] if conforme else [
                {"setting": "screen_capture_disabled", "reason": "failed"}
            ],
        )
        DeviceAssignment.objects.create(
            organization=org, device=device, school_class=classe, student=studente,
            assigned_at=adesso - timedelta(days=60),
        )

    for (lettera, n), classe in classi.items():
        if n <= 2:
            for studente in iscritti[classe]:
                tablet(classe, studente)
    for lettera in SEZIONI:
        for _ in range(6):
            tablet(classi[lettera, 3])  # carrello della sezione, in prestito alla terza

    if App is not None:
        catalogo_app(org, ordinamento, applicate)
    return org


# Catalogo dell'istituto di esempio (ADR-0019). Le app di istruzione, ufficio e comunicazione
# (Classroom, Teams, MyLIM, WhatsApp, Firefox...) sono già consentite dal catalogo della
# piattaforma; qui solo le aggiunte del liceo e le app di sistema dell'emulatore AOSP.
CATALOGO = [
    # (nome, pacchetto, ambito): "istituto", "applicate" (indirizzo) o None (solo da sbloccare)
    ("Impostazioni", "com.android.settings", "istituto"),
    ("File", "com.android.documentsui", "istituto"),
    ("Calcolatrice", "com.android.calculator2", "istituto"),
    ("Acode (editor di codice)", "com.foxdebug.acode", "applicate"),
    ("Fotocamera", "com.android.camera2", None),
    ("Galleria", "com.android.gallery3d", None),
    ("Registratore", "com.android.soundrecorder", None),
    ("Mappe (OsmAnd)", "net.osmand.plus", None),
]
# App obbligatorie scelte dal liceo di esempio: ogni istituto decide le proprie.
OBBLIGATORIE = [
    ("Microsoft Teams", "com.microsoft.teams"),
    ("MyLIM (Loescher)", "it.maieuticallabs.mylim"),
]


def catalogo_app(org, ordinamento, applicate):
    for nome, pacchetto, ambito in CATALOGO:
        app = App.objects.create(organization=org, name=nome, identifier=pacchetto)
        if ambito == "istituto":
            AppRule.objects.create(organization=org, app=app)
        elif ambito == "applicate":
            AppRule.objects.create(organization=org, app=app, track=applicate)
    # Elenco unico (ADR-0020): le obbligatorie sono app consentite con la spunta.
    for nome, pacchetto in OBBLIGATORIE:
        app = App.objects.create(organization=org, name=nome, identifier=pacchetto)
        AppRule.objects.create(organization=org, app=app, required=True)
    AppPolicyState.objects.update_or_create(organization=org, defaults={"allowlist_enabled": True})
    if AppRequest is not None:
        richieste_esempio(org)


def richieste_esempio(org):
    """Richieste di app di esempio (ADR-0021) e un'app del PDP per un solo studente."""
    from eduwisp_apps.requests import add_opinion, decide

    def studente_con_famiglia(sezione, anno, salta=0):
        iscritti = Student.objects.filter(
            enrollments__school_class__section__name=sezione,
            enrollments__school_class__year_number=anno,
            guardians__is_primary=True,
            birth_date__gt=born_by(date.today(), ADULT_AGE),
        ).distinct().order_by("display_name")
        return iscritti[salta]

    def classe_di(studente):
        return studente.enrollments.select_related("school_class").first().school_class

    def docente_di(classe):
        return TeachingAssignment.objects.filter(section=classe.section).order_by("pk").first().teacher

    # In attesa, con il parere favorevole di un genitore
    a = studente_con_famiglia("A", 2)
    r = AppRequest.objects.create(
        organization=org, student=a, school_class=classe_di(a),
        identifier="it.esempio.dizionariolatino", name="Dizionario di latino",
        note="Mi serve per le versioni a casa.",
    )
    add_opinion(a.guardians.get(is_primary=True).user, r, "Lo usa per i compiti di latino.")
    # Approvata da un docente della classe: consentita solo per quello studente
    b = studente_con_famiglia("B", 1)
    r = AppRequest.objects.create(
        organization=org, student=b, school_class=classe_di(b),
        identifier="org.example.atlantestorico", name="Atlante storico",
    )
    decide(docente_di(classe_di(b)), r, True, "Utile per il progetto di storia del secondo periodo.")
    # Vietata: respinta subito
    c = studente_con_famiglia("A", 1)
    AppRequest.objects.create(
        organization=org, student=c, school_class=classe_di(c),
        identifier="com.zhiliaoapp.musically", name="TikTok", status="rejected",
        decision_reason="App vietata in tutti gli istituti (ADR-0019): non si può approvare.",
    )
    # Strumento del PDP per un solo studente, senza motivo registrato (FAQ 12 del Garante)
    registratore = App.objects.get(organization=org, identifier="com.android.soundrecorder")
    AppRule.objects.create(organization=org, app=registratore, student=studente_con_famiglia("A", 1, 1))


def utente_demo():
    """Accesso pubblico alla demo: utente «demo», password «demo», in sola lettura.

    Vede tutto come l'amministratore (anche il «vedi come»), ma il gruppo «sola-lettura» fa
    rifiutare ogni modifica (eduwisp-portal). Solo negli ambienti di prova (ADR-0015).
    """
    gruppo, _ = Group.objects.get_or_create(name="sola-lettura")
    demo, _ = User.objects.get_or_create(username="demo")
    demo.first_name, demo.last_name = "Account", "dimostrativo"
    demo.email = ""
    demo.is_staff = demo.is_superuser = demo.is_active = True
    demo.set_password("demo")  # volutamente debole: account pubblico e in sola lettura
    demo.save()
    demo.groups.add(gruppo)


if os.environ.get("EDUWISP_DEMO_RESET") == "1":
    elimina()
if Organization.objects.filter(slug=SLUG).exists():
    print("Dati di esempio invariati")
else:
    org = crea()
    print(
        "Dati di esempio creati:",
        SchoolClass.objects.filter(organization=org).count(), "classi,",
        Student.objects.filter(organization=org).count(), "studenti,",
        Membership.objects.filter(organization=org, role=Role.TEACHER).count(), "docenti,",
        Membership.objects.filter(organization=org, role=Role.GUARDIAN).count(), "familiari,",
        sum(s.is_adult() for s in Student.objects.filter(organization=org)),
        "maggiorenni,",
        Device.objects.filter(organization=org).count(), "dispositivi",
    )
utente_demo()
