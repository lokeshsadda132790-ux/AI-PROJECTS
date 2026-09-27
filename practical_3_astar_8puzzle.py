"""
Practical 3 - Artificial Intelligence (01AI0511)

Aim:
    Implement A* search for the 8-puzzle and evaluate the effect of
    different heuristics on search efficiency.

Approach:
    - The puzzle state is a tuple of 9 numbers (0 = blank), read row-wise.
    - A* uses f(n) = g(n) + h(n), where g(n) is the number of moves made
      so far and h(n) is one of two admissible heuristics:
        1. Misplaced Tiles  - count of tiles not in their goal position.
        2. Manhattan Distance - sum of each tile's grid distance from its
           goal position.
    - Both heuristics never overestimate the true cost, so both guarantee
      an optimal (shortest) solution. The difference is in how many nodes
      each has to expand to find it - a more "informed" heuristic (closer
      to the true remaining cost) prunes the search tree far more.
"""

import heapq
from itertools import count

GOAL_STATE = (1, 2, 3, 4, 5, 6, 7, 8, 0)


def get_neighbors(state):
    """All states reachable from `state` by one legal slide, with move name."""
    neighbors = []
    idx = state.index(0)
    row, col = divmod(idx, 3)
    moves = [(-1, 0, 'Up'), (1, 0, 'Down'), (0, -1, 'Left'), (0, 1, 'Right')]
    for dr, dc, name in moves:
        nr, nc = row + dr, col + dc
        if 0 <= nr < 3 and 0 <= nc < 3:
            nidx = nr * 3 + nc
            new_state = list(state)
            new_state[idx], new_state[nidx] = new_state[nidx], new_state[idx]
            neighbors.append((tuple(new_state), name))
    return neighbors


def misplaced_tiles(state):
    """h1: number of tiles (excluding blank) not in their goal position."""
    return sum(1 for i in range(9) if state[i] != 0 and state[i] != GOAL_STATE[i])


def manhattan_distance(state):
    """h2: sum of |row difference| + |col difference| for every tile."""
    dist = 0
    for i in range(9):
        val = state[i]
        if val == 0:
            continue
        goal_idx = GOAL_STATE.index(val)
        r1, c1 = divmod(i, 3)
        r2, c2 = divmod(goal_idx, 3)
        dist += abs(r1 - r2) + abs(c1 - c2)
    return dist


def is_solvable(state):
    """3x3 puzzle is solvable iff the permutation (ignoring the blank) has
    an even number of inversions."""
    arr = [x for x in state if x != 0]
    inversions = sum(
        1
        for i in range(len(arr))
        for j in range(i + 1, len(arr))
        if arr[i] > arr[j]
    )
    return inversions % 2 == 0


def astar(start, heuristic_fn):
    """Standard A* graph search. Returns (move_list, nodes_expanded)."""
    counter = count()  # tie-breaker so heap never compares states directly
    frontier = [(heuristic_fn(start), 0, next(counter), start, [])]
    best_g = {start: 0}
    nodes_expanded = 0

    while frontier:
        f, g, _, state, path = heapq.heappop(frontier)
        if g > best_g.get(state, float('inf')):
            continue  # stale entry, a cheaper path was already found
        nodes_expanded += 1

        if state == GOAL_STATE:
            return path, nodes_expanded

        for neighbor, move in get_neighbors(state):
            new_g = g + 1
            if new_g < best_g.get(neighbor, float('inf')):
                best_g[neighbor] = new_g
                new_f = new_g + heuristic_fn(neighbor)
                heapq.heappush(frontier, (new_f, new_g, next(counter), neighbor, path + [move]))

    return None, nodes_expanded  # unreachable for a solvable puzzle


def print_state(state, label=""):
    if label:
        print(label)
    for i in range(0, 9, 3):
        row = state[i:i + 3]
        print(' '.join(str(x) if x != 0 else '_' for x in row))
    print()


def main():
    # A fixed, verified-solvable scramble (30 random legal moves from the goal)
    start = (8, 1, 2, 4, 0, 3, 6, 7, 5)

    print_state(start, "Initial State:")
    print_state(GOAL_STATE, "Goal State:")

    if not is_solvable(start):
        print("This configuration is NOT solvable.")
        return

    print("=" * 55)
    print("Solving with Heuristic 1: Misplaced Tiles")
    print("=" * 55)
    path1, nodes1 = astar(start, misplaced_tiles)
    print(f"Solution length : {len(path1)} moves")
    print(f"Move sequence   : {path1}")
    print(f"Nodes expanded  : {nodes1}\n")

    print("=" * 55)
    print("Solving with Heuristic 2: Manhattan Distance")
    print("=" * 55)
    path2, nodes2 = astar(start, manhattan_distance)
    print(f"Solution length : {len(path2)} moves")
    print(f"Move sequence   : {path2}")
    print(f"Nodes expanded  : {nodes2}\n")

    print("=" * 55)
    print("Comparison")
    print("=" * 55)
    print(f"{'Heuristic':<22}{'Nodes Expanded':<18}{'Path Length'}")
    print(f"{'Misplaced Tiles':<22}{nodes1:<18}{len(path1)}")
    print(f"{'Manhattan Distance':<22}{nodes2:<18}{len(path2)}")
    print()
    print("Observation: Both heuristics are admissible, so both return the")
    print("same optimal path length. Manhattan Distance is a tighter (more")
    print("informed) estimate of the true remaining cost, so A* guided by")
    print(f"it expands far fewer nodes ({nodes2} vs {nodes1} here) to reach")
    print("the same solution.")


if __name__ == "__main__":
    main()
