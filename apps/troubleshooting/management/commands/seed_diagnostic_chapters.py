from django.core.management.base import BaseCommand

from apps.troubleshooting.models import DiagnosticChapter, DiagnosticChapterOption, DiagnosticSafetyRule


CHAPTERS = [
    {
        "name": "Problemi elettrici",
        "slug": "problemi-elettrici",
        "description": "Guida chat-first per guasti e segnali legati all'impianto elettrico domestico.",
        "prompt_context": "Ambito elettrico domestico. Fare domande semplici e non invasive.",
        "safety_context": "Non suggerire apertura quadri, manipolazione cavi o misure su circuiti in tensione.",
        "options": [
            ("salvavita", "Salvavita", "asset_type"),
            ("presa", "Presa", "asset_type"),
            ("luce", "Luce", "asset_type"),
            ("quadro-elettrico", "Quadro elettrico", "asset_type"),
            ("blackout-parziale", "Blackout parziale", "symptom"),
        ],
        "safety_rules": [
            {
                "title": "Segnali elettrici pericolosi",
                "trigger_terms_json": ["odore di bruciato", "fumo", "scintille", "scossa", "surriscaldamento"],
                "guidance": "Fermare le verifiche autonome e coinvolgere un professionista.",
                "risk_level": "urgent",
                "escalation_level": "urgent",
            }
        ],
    },
    {
        "name": "Elettrodomestici",
        "slug": "elettrodomestici",
        "description": "Problemi su apparecchi domestici, con scelta iniziale del tipo di elettrodomestico.",
        "prompt_context": "Identificare apparecchio, sintomo, frequenza e condizioni in cui si presenta il problema.",
        "safety_context": "Non suggerire smontaggi, bypass di sicurezze o interventi su parti elettriche interne.",
        "options": [
            ("lavatrice", "Lavatrice", "asset_type"),
            ("lavastoviglie", "Lavastoviglie", "asset_type"),
            ("forno", "Forno", "asset_type"),
            ("frigorifero", "Frigorifero", "asset_type"),
            ("piano-cottura", "Piano cottura", "asset_type"),
            ("asciugatrice", "Asciugatrice", "asset_type"),
        ],
        "safety_rules": [],
    },
    {
        "name": "Idraulica",
        "slug": "idraulica",
        "description": "Perdite, scarichi, rubinetti, sanitari e pressione acqua.",
        "prompt_context": "Capire posizione, entita' della perdita o blocco, frequenza e urgenza.",
        "safety_context": "In caso di perdita importante o rischio danni, consigliare chiusura acqua se sicura e professionista.",
        "options": [
            ("perdita", "Perdita", "symptom"),
            ("scarico-lento", "Scarico lento", "symptom"),
            ("rubinetto", "Rubinetto", "asset_type"),
            ("sanitario", "Sanitario", "asset_type"),
            ("pressione-acqua", "Pressione acqua", "symptom"),
        ],
        "safety_rules": [],
    },
    {
        "name": "Climatizzazione",
        "slug": "climatizzazione",
        "description": "Condizionatori, pompe di calore e problemi di comfort.",
        "prompt_context": "Raccogliere modello se noto, sintomo, modalita' d'uso, rumori e perdite.",
        "safety_context": "Non suggerire apertura unita' o interventi su gas refrigerante.",
        "options": [
            ("split", "Split", "asset_type"),
            ("unita-esterna", "Unita' esterna", "asset_type"),
            ("aria-non-fredda", "Aria non fredda", "symptom"),
            ("perdita-acqua", "Perdita acqua", "symptom"),
            ("rumore", "Rumore", "symptom"),
        ],
        "safety_rules": [],
    },
    {
        "name": "Domotica",
        "slug": "domotica",
        "description": "Dispositivi smart, hub, sensori e automazioni domestiche.",
        "prompt_context": "Capire dispositivo, rete, hub, automazione coinvolta e ultimo cambiamento noto.",
        "safety_context": "Separare problemi software/rete da interventi elettrici fisici.",
        "options": [
            ("dispositivo-offline", "Dispositivo offline", "symptom"),
            ("automazione", "Automazione", "asset_type"),
            ("sensore", "Sensore", "asset_type"),
            ("hub", "Hub", "asset_type"),
            ("rete", "Rete", "asset_type"),
        ],
        "safety_rules": [],
    },
    {
        "name": "Sicurezza domestica",
        "slug": "sicurezza-domestica",
        "description": "Allarmi, sensori, videocitofoni e dispositivi di sicurezza.",
        "prompt_context": "Capire dispositivo, evento, falsi allarmi, alimentazione e connettivita'.",
        "safety_context": "Non suggerire disattivazioni permanenti di dispositivi di sicurezza.",
        "options": [],
        "safety_rules": [],
    },
    {
        "name": "Manutenzione generale",
        "slug": "manutenzione-generale",
        "description": "Promemoria, piccoli controlli e manutenzioni non urgenti.",
        "prompt_context": "Guidare verso raccolta dati, periodicita' e priorita'.",
        "safety_context": "Evitare istruzioni operative specialistiche.",
        "options": [],
        "safety_rules": [],
    },
]


class Command(BaseCommand):
    help = "Seed initial diagnostic chapters for local/demo use."

    def handle(self, *args, **options):
        created_chapters = 0
        updated_chapters = 0
        created_options = 0
        updated_options = 0
        created_rules = 0
        updated_rules = 0

        for sort_order, chapter_data in enumerate(CHAPTERS, start=10):
            chapter, created = DiagnosticChapter.objects.update_or_create(
                slug=chapter_data["slug"],
                defaults={
                    "name": chapter_data["name"],
                    "description": chapter_data["description"],
                    "prompt_context": chapter_data["prompt_context"],
                    "safety_context": chapter_data["safety_context"],
                    "status": DiagnosticChapter.Statuses.PUBLISHED,
                    "is_public": True,
                    "sort_order": sort_order,
                },
            )
            created_chapters += int(created)
            updated_chapters += int(not created)

            for option_order, (slug, label, option_type) in enumerate(chapter_data["options"], start=10):
                _option, option_created = DiagnosticChapterOption.objects.update_or_create(
                    chapter=chapter,
                    slug=slug,
                    defaults={
                        "label": label,
                        "option_type": option_type,
                        "sort_order": option_order,
                        "is_active": True,
                    },
                )
                created_options += int(option_created)
                updated_options += int(not option_created)

            for rule_order, rule_data in enumerate(chapter_data["safety_rules"], start=10):
                _rule, rule_created = DiagnosticSafetyRule.objects.update_or_create(
                    chapter=chapter,
                    title=rule_data["title"],
                    defaults={
                        "trigger_terms_json": rule_data["trigger_terms_json"],
                        "guidance": rule_data["guidance"],
                        "risk_level": rule_data["risk_level"],
                        "escalation_level": rule_data["escalation_level"],
                        "sort_order": rule_order,
                        "is_active": True,
                    },
                )
                created_rules += int(rule_created)
                updated_rules += int(not rule_created)

        self.stdout.write(
            self.style.SUCCESS(
                "Diagnostic chapters seeded: "
                f"{created_chapters} created/{updated_chapters} updated chapters, "
                f"{created_options} created/{updated_options} updated options, "
                f"{created_rules} created/{updated_rules} updated safety rules."
            )
        )
