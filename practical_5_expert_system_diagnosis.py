"""
Practical 5 - Artificial Intelligence (01AI0511)

Aim:
    Build a small rule-based expert system / logic inference engine for
    a diagnosis or advisory problem.

Approach:
    - Knowledge base: a set of IF <symptoms> THEN <diagnosis> rules, each
      also carrying a short advisory action (a simple plant-health
      advisor, so the reasoning is easy to follow and check by hand).
    - Working memory: the set of known facts, seeded with the observed
      symptoms.
    - Inference: forward chaining. The engine repeatedly scans the rule
      base; any rule whose full set of conditions is already a subset of
      the known facts "fires", adding its conclusion as a new fact. This
      repeats until a full pass adds nothing new (fixed point).
    - Explanation facility: every fired rule is logged with the symptoms
      that triggered it, so the final diagnosis can be justified rather
      than just asserted.
"""


class ExpertSystem:
    def __init__(self, rules):
        self.rules = rules
        self.facts = set()
        self.fired_rules = []  # order in which rules fired, for explanation

    def add_fact(self, fact):
        self.facts.add(fact)

    def forward_chain(self):
        """Keep sweeping the rule base until no rule fires in a full pass."""
        changed = True
        while changed:
            changed = False
            for rule in self.rules:
                if rule["conclusion"] in self.facts:
                    continue
                if rule["conditions"].issubset(self.facts):
                    self.facts.add(rule["conclusion"])
                    self.fired_rules.append(rule)
                    changed = True

    def explain(self):
        print("--- Explanation facility ---")
        if not self.fired_rules:
            print("No rule's conditions were fully satisfied; no diagnosis reached.")
            return
        for rule in self.fired_rules:
            conds = ', '.join(sorted(rule["conditions"]))
            print(f"[{rule['id']}] IF ({conds}) is observed")
            print(f"      THEN diagnosis = {rule['conclusion']}")
            print(f"      Advice: {rule['advice']}\n")


# Knowledge base -------------------------------------------------------
RULES = [
    {"id": "R1", "conditions": {"yellow_leaves", "wilting"},
     "conclusion": "Root Rot",
     "advice": "Cut back on watering and improve soil drainage; trim any mushy roots."},

    {"id": "R2", "conditions": {"brown_spots", "yellow_leaves"},
     "conclusion": "Leaf Spot Disease",
     "advice": "Remove infected leaves, apply a fungicide, avoid wetting the foliage."},

    {"id": "R3", "conditions": {"white_powder"},
     "conclusion": "Powdery Mildew",
     "advice": "Improve air circulation; apply a sulfur or neem-oil based spray."},

    {"id": "R4", "conditions": {"black_spots", "leaf_curl"},
     "conclusion": "Black Spot Fungus",
     "advice": "Prune affected growth and apply a copper-based fungicide."},

    {"id": "R5", "conditions": {"holes_in_leaves", "sticky_residue"},
     "conclusion": "Insect Infestation",
     "advice": "Check for aphids/caterpillars; treat with insecticidal soap or neem oil."},

    {"id": "R6", "conditions": {"stunted_growth", "yellow_leaves"},
     "conclusion": "Nutrient Deficiency",
     "advice": "Apply a balanced fertilizer and check soil nitrogen levels."},

    {"id": "R7", "conditions": {"wilting", "moldy_smell"},
     "conclusion": "Fungal Root Infection",
     "advice": "Repot in fresh, sterile soil and apply a fungicide drench."},

    # a second-level rule: fires only once a first-level diagnosis is
    # already a known fact -- shows the engine chaining rule to rule,
    # not just symptom to rule.
    {"id": "R8", "conditions": {"Root Rot", "Fungal Root Infection"},
     "conclusion": "Severe Root System Failure",
     "advice": "Consider taking a healthy cutting to propagate; the current root system is unlikely to recover."},
]

SYMPTOM_LIST = [
    "yellow_leaves", "brown_spots", "wilting", "white_powder", "black_spots",
    "leaf_curl", "stunted_growth", "holes_in_leaves", "sticky_residue", "moldy_smell",
]


def run_case(symptoms, title):
    print("=" * 60)
    print(title)
    print("=" * 60)
    es = ExpertSystem(RULES)
    for s in symptoms:
        es.add_fact(s)
    print("Observed symptoms:", sorted(symptoms))

    es.forward_chain()

    derived = es.facts - symptoms
    print("Facts derived by inference:", sorted(derived) if derived else "(none)")
    print()
    es.explain()

    if es.fired_rules:
        print("FINAL DIAGNOSIS:", ", ".join(r["conclusion"] for r in es.fired_rules))
    else:
        print("FINAL DIAGNOSIS: inconclusive - not enough matching symptoms.")
    print()


def interactive_case():
    print("Available symptoms:")
    for i, s in enumerate(SYMPTOM_LIST, 1):
        print(f"  {i}. {s.replace('_', ' ')}")
    raw = input("\nEnter the numbers of observed symptoms, comma-separated (e.g. 1,3,6): ").strip()
    chosen = set()
    for tok in raw.split(','):
        tok = tok.strip()
        if tok.isdigit() and 1 <= int(tok) <= len(SYMPTOM_LIST):
            chosen.add(SYMPTOM_LIST[int(tok) - 1])
    run_case(chosen, "Your Case")


if __name__ == "__main__":
    # A couple of fixed demo cases exercise the engine end to end...
    run_case({"yellow_leaves", "wilting", "moldy_smell"}, "Demo Case 1")
    run_case({"white_powder"}, "Demo Case 2")
    run_case({"holes_in_leaves"}, "Demo Case 3 (inconclusive - only one symptom)")

    # ...then let the user try their own combination.
    interactive_case()
