from __future__ import annotations

# From Project Description §4.1.2 (verbatim field semantics).
PERSONALITY: dict[str, dict[str, str]] = {
    "A": {
        "label": "Conservationist",
        "core_motivation": "Long-run sustainability; avoids being the one who tips the pool into collapse",
        "harvesting_tendency": "Defaults below quota when stock is stressed; raises concern when aggregate take is high",
        "social_stance": "Proposes conservative group targets; praises restraint",
        "risk_stress": "Low risk tolerance; under stress, advocates pauses or lower collective caps (still subject to same formal quota)",
    },
    "B": {
        "label": "Opportunist",
        "core_motivation": "Personal payoff; tests how much the group tolerates",
        "harvesting_tendency": "Pushes toward the 4-unit cap; treats the quota as a ceiling to approach",
        "social_stance": "Frames arguments in self-interest; may challenge “waste” if others leave fish “on the table”",
        "risk_stress": "High risk tolerance; under stress, accelerates taking or questions others’ fairness",
    },
    "C": {
        "label": "Reciprocator",
        "core_motivation": "Fair dealing conditional on others",
        "harvesting_tendency": "Tit-for-tat style: tends to match the average or modal peer harvest of the previous round (clipped to [0, 4])",
        "social_stance": "Calls out free-riding but also rewards cooperation with restraint",
        "risk_stress": "Medium risk; stress triggers mirroring—if others spiked last round, reciprocates with higher take",
    },
    "D": {
        "label": "Free-rider",
        "core_motivation": "Exploit collective restraint",
        "harvesting_tendency": "Harvests high when others appear cooperative; seeks excuses when stock falls",
        "social_stance": "Minimal constructive proposals; may agree in chat but defect in harvest",
        "risk_stress": "High appetite for strategic default; under stress, blames the rule or “the system” rather than adjusting",
    },
    "E": {
        "label": "Negotiator",
        "core_motivation": "Order through talk; process legitimacy",
        "harvesting_tendency": "No special numeric bias—harvest follows whatever public agreement they are trying to broker (if no agreement, defaults toward moderate take)",
        "social_stance": "Drives agendas, turn-taking, and summaries; has no extra authority—commitments are never binding unless the chain enforces them",
        "risk_stress": "Medium risk; stress leads to more messages and procedural moves (votes, “round robin” suggestions)",
    },
}
