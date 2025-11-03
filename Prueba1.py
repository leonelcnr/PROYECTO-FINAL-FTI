from automata.fa.dfa import DFA
from collections import deque

# ---------------------------
# Helpers de grid
# ---------------------------
def parse_grid(grid_str):
    rows = [list(r) for r in grid_str.strip("\n").splitlines()]
    h, w = len(rows), len(rows[0])
    start = None
    ghosts = set()
    walls = set()
    pellets = []
    goal = None

    for y in range(h):
        for x in range(w):
            c = rows[y][x]
            if c == '#': walls.add((x,y))
            elif c == 'S': start = (x,y)
            elif c == 'G': ghosts.add((x,y))
            elif c == '.': pellets.append((x,y))
            elif c == 'E': goal = (x,y)
            # espacios ' ' son transitables
    if start is None:
        raise ValueError("Falta 'S' (inicio) en el mapa.")

    # Indizar pastillas para bitmask 0..(2^P - 1)
    pellet_index = {p:i for i,p in enumerate(pellets)}
    full_mask = (1 << len(pellets)) - 1

    return {
        "rows": rows, "w": w, "h": h, "start": start, "walls": walls,
        "ghosts": ghosts, "pellets": pellets, "pellet_index": pellet_index,
        "full_mask": full_mask, "goal": goal
    }

# ---------------------------
# Construcción del DFA Pac-Man
# ---------------------------
def build_pacman_dfa(grid_str, *, bounce_on_wall=True, require_goal=False):
    G = parse_grid(grid_str)
    moves = {'U':(0,-1), 'D':(0,1), 'L':(-1,0), 'R':(1,0)}

    def in_bounds(x,y): return 0 <= x < G["w"] and 0 <= y < G["h"]
    def is_wall(x,y):  return (x,y) in G["walls"]
    def is_ghost(x,y): return (x,y) in G["ghosts"]
    def has_pellet(x,y): return (x,y) in G["pellet_index"]

    q0 = (G["start"][0], G["start"][1], G["full_mask"])
    DEAD = "DEAD"          # sink por fantasma
    SINK = "SINK"          # sink opcional por movimiento inválido
    use_sink = not bounce_on_wall

    states = set([q0, DEAD] + ([SINK] if use_sink else []))
    input_symbols = set(moves.keys())
    transitions = {}
    finals = set()

    # Los sinks se auto-loop-ean
    transitions[DEAD] = {a: DEAD for a in input_symbols}
    if use_sink:
        transitions[SINK] = {a: SINK for a in input_symbols}

    # BFS de expansión de estados alcanzables
    queue = deque([q0])
    seen = {q0}

    while queue:
        (x, y, mask) = queue.popleft()
        transitions[(x,y,mask)] = {}
        # ¿es final?
        is_mask_empty = (mask == 0)
        if is_mask_empty and (not require_goal or (G["goal"] and (x,y)==G["goal"])):
            finals.add((x,y,mask))

        for a, (dx,dy) in moves.items():
            nx, ny = x+dx, y+dy

            # 1) fuera de grilla o pared
            if (not in_bounds(nx,ny)) or is_wall(nx,ny):
                if use_sink:
                    transitions[(x,y,mask)][a] = SINK
                else:
                    transitions[(x,y,mask)][a] = (x,y,mask)  # rebota
                continue

            # 2) fantasma => muerte
            if is_ghost(nx,ny):
                transitions[(x,y,mask)][a] = DEAD
                continue

            # 3) celda libre: actualizar pastillas
            new_mask = mask
            if has_pellet(nx,ny):
                i = G["pellet_index"][(nx,ny)]
                if (new_mask >> i) & 1:  # si no estaba comida
                    new_mask = new_mask & ~(1 << i)

            qn = (nx, ny, new_mask)
            transitions[(x,y,mask)][a] = qn
            if qn not in seen:
                seen.add(qn)
                states.add(qn)
                queue.append(qn)

    # Aseguramos incluir todos los estados descubiertos
    states.update(seen)

    dfa = DFA(
        states=states,
        input_symbols=input_symbols,
        transitions=transitions,
        initial_state=q0,
        final_states=finals
    )
    return dfa

# ---------------------------
# Búsqueda de palabra ganadora mínima (BFS en el grafo del DFA)
# ---------------------------
def shortest_winning_word(dfa):
    from collections import deque
    q0 = dfa.initial_state
    finals = dfa.final_states
    moves = sorted(next(iter(dfa.transitions.values())).keys())  # ['D','L','R','U'] etc.

    Q = deque([(q0, "")])
    seen = {q0}
    while Q:
        q, word = Q.popleft()
        if q in finals:
            return word  # puede ser "" si ya arrancás en final
        for a in moves:
            qn = dfa.transitions[q][a]
            if qn not in seen:
                seen.add(qn)
                Q.append((qn, word + a))
    return None

# ---------------------------
# Demo mínima
# ---------------------------
if __name__ == "__main__":
    grid = """
########
#S .  G#
#  ##  #
# .   .#
########
""".strip("\n")

    dfa = build_pacman_dfa(grid, bounce_on_wall=False, require_goal=False)
    word = shortest_winning_word(dfa)
    print("Palabra ganadora mínima:", word)

    if word is not None:
        print("¿Acepta?", dfa.accepts_input(word))
        print("Traza de estados:")
        for st in dfa.read_input_stepwise(word):
            print("  ", st)
