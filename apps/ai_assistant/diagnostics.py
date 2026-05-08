def build_diagnostic_selection_metadata(chapter=None, option=None):
    metadata = {"kind": "user_observation"}
    if chapter is not None:
        metadata.update(
            {
                "diagnostic_chapter_id": chapter.id,
                "diagnostic_chapter_name": chapter.name,
                "diagnostic_chapter_slug": chapter.slug,
                "diagnostic_chapter_prompt_context": chapter.prompt_context,
                "diagnostic_chapter_safety_context": chapter.safety_context,
                "diagnostic_chapter_safety_rules": [
                    {
                        "title": rule.title,
                        "trigger_terms": rule.trigger_terms_json,
                        "guidance": rule.guidance,
                        "risk_level": rule.risk_level,
                        "escalation_level": rule.escalation_level,
                    }
                    for rule in chapter.safety_rules.filter(is_active=True).order_by("sort_order", "id")
                ],
            }
        )
    if option is not None:
        metadata.update(
            {
                "diagnostic_chapter_option_id": option.id,
                "diagnostic_chapter_option_label": option.label,
                "diagnostic_chapter_option_slug": option.slug,
                "diagnostic_chapter_option_type": option.option_type,
                "diagnostic_chapter_option_prompt_hint": option.prompt_hint,
            }
        )
    return metadata
