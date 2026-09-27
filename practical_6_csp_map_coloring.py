"""
Practical 6 - Artificial Intelligence (01AI0511)

Aim:
    Solve a constraint satisfaction problem (map coloring) using
    backtracking search and consistency-checking techniques.

Problem:
    Colour the mainland Australian territories so that no two
    neighbouring territories share a colour (the classic CSP example
    from the course textbook, Russell & Norvig).

    Variables : WA, NT, SA, Q, NSW, V, T
    Domain    : {Red, Green, Blue}
    Adjacency :
        WA - NT, SA
        NT - WA, SA, Q
        SA - WA, NT, Q, NSW, V
        Q  - NT, SA, NSW
        NSW- SA, Q, V
        V  - SA, NSW
        T  - (Tasmania is an island; no neighbours)

Approach - three techniques are compared:
    1. Plain backtracking: assign, check consistency against already-
       assigned neighbours only, backtrack on failure.
    2. Backtracking + forward checking: whenever a variable is assigned,
       immediately remove that value from every *unassigned* neighbour's
       domain. If a domain is emptied, that branch is abandoned right
       away instead of discovering the conflict several variables later.
    3. AC-3 (arc consistency) as a preprocessing pass: for every
       directed arc (Xi, Xj), remove values from Xi's domain that have
       no supporting value in Xj's domain, repeating until stable.
"""


class CSP:
    def __init__(self, variables, domains, neighbors):
        self.variables = variables
        self.domains = domains
        self.neighbors = neighbors

    def is_consistent(self, var, value, assignment):
        return all(
            assignment.get(n) != value
            for n in self.neighbors[var]
        )


def backtracking_search(csp, use_forward_checking=False):
    """Returns (solution_dict_or_None, stats)."""
    stats = {"assignments_tried": 0, "backtracks": 0}
    domains = {v: list(csp.domains[v]) for v in csp.variables}

    def backtrack(assignment, domains):
        if len(assignment) == len(csp.variables):
            return dict(assignment)

        var = next(v for v in csp.variables if v not in assignment)

        for value in list(domains[var]):
            stats["assignments_tried"] += 1
            if not csp.is_consistent(var, value, assignment):
                continue

            assignment[var] = value

            if use_forward_checking:
                saved = {v: list(domains[v]) for v in domains}
                wiped_out = False
                for n in csp.neighbors[var]:
                    if n not in assignment and value in domains[n]:
                        domains[n].remove(value)
                        if not domains[n]:
                            wiped_out = True

                if not wiped_out:
                    result = backtrack(assignment, domains)
                    if result is not None:
                        return result

                for v in domains:            # undo the pruning (restore state)
                    domains[v] = saved[v]
            else:
                result = backtrack(assignment, domains)
                if result is not None:
                    return result

            del assignment[var]
            stats["backtracks"] += 1

        return None

    return backtrack({}, domains), stats


def ac3(csp):
    """Enforces arc consistency. Returns pruned domains, or None if some
    domain is wiped out (a certificate that NO solution exists)."""
    domains = {v: list(csp.domains[v]) for v in csp.variables}
    queue = [(xi, xj) for xi in csp.variables for xj in csp.neighbors[xi]]

    def revise(xi, xj):
        revised = False
        for x in list(domains[xi]):
            if not any(x != y for y in domains[xj]):  # no supporting value in xj
                domains[xi].remove(x)
                revised = True
        return revised

    while queue:
        xi, xj = queue.pop(0)
        if revise(xi, xj):
            if not domains[xi]:
                return None
            for xk in csp.neighbors[xi]:
                if xk != xj:
                    queue.append((xk, xi))
    return domains


def validate(assignment, neighbors):
    """Independently double-checks a solution respects every constraint."""
    if assignment is None:
        return False
    return all(
        assignment[n] != assignment[var]
        for var in assignment for n in neighbors[var]
    )


VARIABLES = ["WA", "NT", "SA", "Q", "NSW", "V", "T"]
NEIGHBORS = {
    "WA": ["NT", "SA"], "NT": ["WA", "SA", "Q"],
    "SA": ["WA", "NT", "Q", "NSW", "V"], "Q": ["NT", "SA", "NSW"],
    "NSW": ["SA", "Q", "V"], "V": ["SA", "NSW"], "T": [],
}


def main():
    print("=" * 60)
    print("Part A: 3-colour map (Red, Green, Blue)")
    print("=" * 60)
    domains3 = {v: ["Red", "Green", "Blue"] for v in VARIABLES}
    csp3 = CSP(VARIABLES, domains3, NEIGHBORS)

    sol_plain, stats_plain = backtracking_search(csp3, use_forward_checking=False)
    sol_fc, stats_fc = backtracking_search(csp3, use_forward_checking=True)

    print("\n1. Plain backtracking:")
    print("  ", sol_plain)
    print(f"   assignments tried: {stats_plain['assignments_tried']}, "
          f"backtracks: {stats_plain['backtracks']}")
    print("   valid solution:", validate(sol_plain, NEIGHBORS))

    print("\n2. Backtracking + forward checking:")
    print("  ", sol_fc)
    print(f"   assignments tried: {stats_fc['assignments_tried']}, "
          f"backtracks: {stats_fc['backtracks']}")
    print("   valid solution:", validate(sol_fc, NEIGHBORS))

    print("\n3. AC-3 arc consistency (run before any search):")
    pruned = ac3(csp3)
    for v in VARIABLES:
        print(f"   {v}: {pruned[v]}")
    print("   -> No domain shrinks below 3 values here: every pair of")
    print("      neighbours can still be coloured differently using only")
    print("      2 of their 3 shared colours, so no single value is ever")
    print("      unsupported. AC-3 doesn't reduce the search here, but it")
    print("      confirms the problem is still arc-consistent before we pay")
    print("      the cost of a full search.")

    print("\n" + "=" * 60)
    print("Comparison (3-colour case)")
    print("=" * 60)
    print(f"{'Method':<32}{'Assignments Tried':<20}{'Backtracks'}")
    print(f"{'Plain backtracking':<32}{stats_plain['assignments_tried']:<20}{stats_plain['backtracks']}")
    print(f"{'Backtracking + forward check':<32}{stats_fc['assignments_tried']:<20}{stats_fc['backtracks']}")
    print("Forward checking finds the conflict the moment a domain is")
    print("emptied, rather than only on the next variable's assignment,")
    print("so it tries fewer assignments overall.")

    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("Part B: what if only 2 colours are available?")
    print("=" * 60)
    print("WA-NT-SA and SA-NT-Q each form a triangle in the adjacency graph")
    print("(three mutually-adjacent territories), and a triangle needs at")
    print("least 3 colours - so this should be unsolvable.\n")

    domains2 = {v: ["Red", "Blue"] for v in VARIABLES}
    csp2 = CSP(VARIABLES, domains2, NEIGHBORS)

    sol2, stats2 = backtracking_search(csp2, use_forward_checking=True)
    print("Backtracking + forward checking result:", sol2)
    print(f"(assignments tried: {stats2['assignments_tried']}, "
          f"backtracks: {stats2['backtracks']})")
    print("-> Correctly proves NO solution exists, by exhausting every option.\n")

    pruned2 = ac3(csp2)
    print("AC-3 result:", "INCONSISTENT (domain wiped out)" if pruned2 is None else pruned2)
    print("-> AC-3 only checks constraints one pair of variables at a time,")
    print("   so for a triangle it can't see that 2 colours are jointly")
    print("   impossible across all three: each *pair* is fine with 2")
    print("   colours, the conflict only appears across all three at once.")
    print("   This is a classic illustration that arc consistency is a")
    print("   NECESSARY but not SUFFICIENT condition for a solution to")
    print("   exist - a full backtracking search is still needed to be sure.")


if __name__ == "__main__":
    main()
