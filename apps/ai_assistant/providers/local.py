from apps.cases.models import Case

from .base import clean_text
from .context import build_case_context, build_diagnostic_context


class LocalAiProvider:
    provider_name = "local"

    def build_reply(self, session, messages):
        user_message = messages[-1]["content"].strip()
        parts = [f"Hai scritto: {user_message}"]
        if session.case_id is None:
            parts.append("Questa sessione non e' collegata a una pratica specifica.")
            parts.append("Descrivi categoria del problema, sintomi e cosa hai gia' verificato.")
            return " ".join(parts)

        context = build_case_context(session)
        parts.append(context)
        if session.case.status == Case.Statuses.IN_DIAGNOSIS:
            parts.append("Continua con verifiche sicure e non invasive prima di escalare.")
        return " ".join(parts)

    def stream_reply(self, session, messages):
        reply = self.build_reply(session, messages)
        for chunk in reply.split():
            yield f"{chunk} "

    def build_diagnostic_reply(self, session, messages):
        user_message = clean_text(messages[-1]["content"] if messages else "")
        lowered = user_message.lower()
        context = build_diagnostic_context(session)
        chapter_name = context["diagnostic"]["chapter"]["name"]
        option_label = context["diagnostic"]["option"]["label"]
        category = chapter_name or (session.case.category.name if session.case_id is not None else "problema domestico")
        if option_label:
            category = f"{category} / {option_label}"

        danger_terms = {
            "odore di bruciato",
            "bruciato",
            "fumo",
            "scintille",
            "scossa",
            "surriscalda",
            "caldo",
        }
        electrical_terms = {"salvavita", "corrente", "presa", "luce", "quadro", "interruttore"}

        if any(term in lowered for term in danger_terms):
            return {
                "assistant_response": (
                    "La descrizione indica un possibile rischio. Evita verifiche invasive e coinvolgi un professionista."
                ),
                "case_summary": f"Problema {category}: {user_message}",
                "risk_level": "urgent",
                "next_question": "Ci sono fumo, scintille o odore persistente anche dopo aver smesso di usare l'impianto?",
                "escalation_recommended": True,
                "escalation_reason": "Segnali compatibili con rischio elettrico o surriscaldamento.",
                "recommendation": "Mettere in sicurezza la situazione e richiedere supporto professionale.",
                "facts": {"reported_issue": user_message, "category": category},
                "excluded_facts": {},
                "asked_questions": [],
                "safety_notes": ["Non aprire quadri o componenti elettrici.", "Non manipolare cavi o parti in tensione."],
            }

        if any(term in lowered for term in electrical_terms):
            return {
                "assistant_response": "Ho aggiornato il quadro del problema. Procediamo con una sola domanda di chiarimento.",
                "case_summary": f"Problema {category}: {user_message}",
                "risk_level": "medium",
                "next_question": "Il problema riguarda un solo punto della casa o piu' stanze/utenze?",
                "escalation_recommended": False,
                "escalation_reason": "",
                "recommendation": "Raccogliere ancora informazioni senza eseguire interventi tecnici.",
                "facts": {"reported_issue": user_message, "category": category},
                "excluded_facts": {},
                "asked_questions": [],
                "safety_notes": ["Limitarsi a osservazioni esterne e sicure."],
            }

        return {
            "assistant_response": "Ho registrato la descrizione. Mi serve un dettaglio per classificare meglio il problema.",
            "case_summary": f"Problema {category}: {user_message}",
            "risk_level": "unknown",
            "next_question": "Da quando si presenta il problema e cosa stava succedendo quando e' comparso?",
            "escalation_recommended": False,
            "escalation_reason": "",
            "recommendation": "Continuare la raccolta di informazioni.",
            "facts": {"reported_issue": user_message, "category": category},
            "excluded_facts": {},
            "asked_questions": [],
            "safety_notes": [],
        }
