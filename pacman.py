from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from collections import deque
import os
import sys

"""
Pac-Lab (AFD) — versión amigable para terminal *y* entornos sin entrada interactiva
-------------------------------------------------------------------------------
Juego estilo Pacman modelado como Autómata Finito Determinista (AFD).
- Estados: (r, c, mask, t) donde (r,c) es la posición y 'mask' es un bitmask de pastillas restantes.
- Alfabeto: U, D, L, R (arriba, abajo, izquierda, derecha).
- Transición δ: mueve al vecino si es celda válida; si es pared/afuera/ghost, va a TRAP.
- Aceptación: mask == 0 (no quedan pastillas).

**Importante (fix del error OSError: [Errno 29] I/O error):**
Algunos sandboxes no permiten `input()`. Ahora el programa detecta si **hay TTY**:
- Si **hay TTY** → lanza el **REPL interactivo** (podés jugar en terminal).
- Si **NO hay TTY** → **no usa `input()`**: ejecuta un **demo** y corre **tests automáticos**.

Comandos (sólo en modo interactivo):
- Mové con: U D L R (podés ingresar varios a la vez, p.ej. RRRDDLL)
- `solve` → encuentra un camino óptimo (BFS)
- `reset` → reinicia
- `grid` → imprime el grid base
- `help`  → ayuda
- `quit`  → salir

Editar el mapa:
- Modificá `SAMPLE_GRID`.
  `#` = pared,  `' '` = vacío,  `o` = pastilla,  `S` = start,  `G` = fantasma (estático)

Notas:
- Muchos estados del AFD son inalcanzables; generamos on-the-fly desde q0.
- Preparado para extender a fantasmas con período (usa 't' si querés períodos >1).
"""

SAMPLE_GRID = """
##################
#S o   G     o   #
# ###  o### o    #
#   o    o o     #
##################
"""

# --------- Modelos ---------

@dataclass(frozen=True)
class State:
    r: int
    c: int
    mask: int  # bitmask de pastillas que FALTAN (1 = falta, 0 = comida)
    t: int = 0  # tiempo discreto (para futuros fantasmas periódicos)


class TRAPType:
    """Estado trampa (sumidero)."""
    def __repr__(self) -> str:
        return "TRAP"


TRAP = TRAPType()


class GameConfig:
    def __init__(self, grid_str: str):
        self.grid, self.H, self.W = self._parse_grid(grid_str)
        self.walls: Set[Tuple[int, int]] = set()
        self.ghosts: Set[Tuple[int, int]] = set()
        self.start: Tuple[int, int] = (-1, -1)
        self.pill_index: Dict[Tuple[int, int], int] = {}
        self.pill_pos: List[Tuple[int, int]] = []

        for r in range(self.H):
            for c in range(self.W):
                ch = self.grid[r][c]
                if ch == '#':
                    self.walls.add((r, c))
                elif ch == 'G':
                    self.ghosts.add((r, c))
                elif ch == 'S':
                    self.start = (r, c)
                elif ch == 'o':
                    idx = len(self.pill_pos)
                    self.pill_index[(r, c)] = idx
                    self.pill_pos.append((r, c))
                # ' ' queda como transitable vacío

        if self.start == (-1, -1):
            raise ValueError("El mapa debe tener una 'S' de inicio")

        self.alphabet = {'U', 'D', 'L', 'R'}
        self.period = 1  # para futuros fantasmas periódicos, usar t mod period

    @staticmethod
    def _parse_grid(grid_str: str) -> Tuple[List[List[str]], int, int]:
        lines = [ln.rstrip('\n') for ln in grid_str.splitlines() if ln.strip('\n') != '']
        if not lines:
            raise ValueError("Grid vacío")
        W = max(len(ln) for ln in lines)
        norm = [list(ln.ljust(W)) for ln in lines]
        H = len(norm)
        return norm, H, W

    def inside(self, r: int, c: int) -> bool:
        return 0 <= r < self.H and 0 <= c < self.W


class DFA:
    def __init__(self, cfg: GameConfig):
        self.cfg = cfg
        self.initial_mask = (1 << len(cfg.pill_pos)) - 1

    def q0(self) -> State:
        r, c = self.cfg.start
        return State(r, c, self.initial_mask, 0)

    def is_accept(self, s: State | TRAPType) -> bool:
        return isinstance(s, State) and s.mask == 0 and (s.r, s.c) not in self.cfg.ghosts

    def delta(self, s: State | TRAPType, a: str) -> State | TRAPType:
        if not isinstance(s, State):
            return TRAP
        if a not in self.cfg.alphabet:
            return s  # ignoramos símbolos inválidos sin mover

        dr, dc = { 'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1) }[a]
        r2, c2 = s.r + dr, s.c + dc

        # chequeos de validez
        if not self.cfg.inside(r2, c2):
            return TRAP
        if (r2, c2) in self.cfg.walls:
            return TRAP
        if (r2, c2) in self.cfg.ghosts:
            return TRAP

        # comer pastilla si hay y aún falta
        mask2 = s.mask
        if (r2, c2) in self.cfg.pill_index:
            idx = self.cfg.pill_index[(r2, c2)]
            mask2 = mask2 & ~(1 << idx)

        t2 = (s.t + 1) % self.cfg.period
        return State(r2, c2, mask2, t2)


# --------- Utilidades ---------

def _is_tty() -> bool:
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:
        return False


def render(cfg: GameConfig, s: State | TRAPType, *, clear_screen: Optional[bool] = None) -> None:
    if clear_screen is None:
        clear_screen = _is_tty()
    if clear_screen:
        os.system('cls' if os.name == 'nt' else 'clear')

    print("Leyenda: # pared | o pastilla | G fantasma | P pacman | S inicio\n")

    if not isinstance(s, State):
        for r in range(cfg.H):
            row = []
            for c in range(cfg.W):
                ch = cfg.grid[r][c]
                row.append(ch)
            print(''.join(row))
        print("\nEstado: TRAP (movimiento inválido / choque)")
        return

    # construir un buffer del mapa base
    buf = [[' ' for _ in range(cfg.W)] for _ in range(cfg.H)]

    for (r, c) in cfg.walls:
        buf[r][c] = '#'
    for (r, c) in cfg.ghosts:
        buf[r][c] = 'G'

    # pastillas restantes según mask
    for idx, (pr, pc) in enumerate(cfg.pill_pos):
        if s.mask & (1 << idx):
            buf[pr][pc] = 'o'

    # posición inicial (cosmética)
    sr, sc = cfg.start
    if buf[sr][sc] == ' ':
        buf[sr][sc] = 'S'

    # pacman
    buf[s.r][s.c] = 'P'

    for r in range(cfg.H):
        print(''.join(buf[r]))

    left = bin(s.mask).count('1')
    print(f"\nPos: ({s.r},{s.c}) | Pastillas restantes: {left}")


def bfs_solve(dfa: DFA) -> Optional[str]:
    """Encuentra un camino mínimo que coma todas las pastillas, o None si no hay."""
    start = dfa.q0()
    if dfa.is_accept(start):
        return ""

    q = deque([start])
    parent: Dict[Tuple[int, int, int], Tuple[Tuple[int, int, int], str]] = {}
    seen: Set[Tuple[int, int, int]] = {(start.r, start.c, start.mask)}

    moves = ['U', 'D', 'L', 'R']
    while q:
        s = q.popleft()
        for a in moves:
            s2 = dfa.delta(s, a)
            if not isinstance(s2, State):
                continue  # ignoramos transiciones a TRAP en la búsqueda
            key = (s2.r, s2.c, s2.mask)
            if key in seen:
                continue
            seen.add(key)
            parent[key] = ((s.r, s.c, s.mask), a)
            if dfa.is_accept(s2):
                # reconstruir
                path: List[str] = []
                cur = key
                while cur != (start.r, start.c, start.mask):
                    prev, act = parent[cur]
                    path.append(act)
                    cur = prev
                path.reverse()
                return ''.join(path)
            q.append(s2)
    return None


def apply_moves(dfa: DFA, seq: str) -> State | TRAPType:
    """Aplica una secuencia de movimientos y devuelve el estado final."""
    cur: State | TRAPType = dfa.q0()
    for ch in seq:
        cur = dfa.delta(cur, ch)
        if not isinstance(cur, State):
            return TRAP
    return cur


# --------- CLI (sólo si hay TTY) ---------

def repl(cfg: GameConfig, dfa: DFA) -> None:
    print("Pac-Lab (AFD) — Terminal\nEscribí 'help' para ayuda.\n")
    cur: State | TRAPType = dfa.q0()
    render(cfg, cur)

    while True:
        try:
            raw = input("\nMovimiento (U/D/L/R...), o comando: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nChau!")
            return

        if not raw:
            continue
        cmd = raw.lower()

        if cmd in {"q", "quit", "exit"}:
            print("Chau!")
            return
        if cmd == "help":
            print("""
Comandos:
  U/D/L/R   -> mover (podés escribir varias juntas, p.ej. RRDLU)
  solve     -> buscar camino mínimo que coma todas las pastillas (BFS)
  reset     -> reiniciar desde el estado inicial
  grid      -> mostrar mapa base (sin P)
  quit      -> salir
            """)
            continue
        if cmd == "grid":
            # imprimir grid base
            render(cfg, dfa.q0(), clear_screen=False)
            continue
        if cmd == "reset":
            cur = dfa.q0()
            render(cfg, cur)
            continue
        if cmd == "solve":
            path = bfs_solve(dfa)
            if path is None:
                print("No existe camino que coma todas las pastillas sin morir.")
                continue
            print(f"Camino encontrado ({len(path)} pasos): {path}")
            # reproducir el camino
            for ch in path:
                cur = dfa.delta(cur, ch)
                render(cfg, cur)
            if dfa.is_accept(cur):
                print("\n¡Ganaste! :)\n")
            else:
                print("\nTerminado.\n")
            continue

        # tratar como secuencia de movimientos
        seq = raw.upper()
        for ch in seq:
            if ch not in {'U', 'D', 'L', 'R'}:
                continue
            cur = dfa.delta(cur, ch)
            render(cfg, cur)
            if not isinstance(cur, State):
                print("\nPerdiste: movimiento inválido / choque.\n")
                break
            if dfa.is_accept(cur):
                print("\n¡Ganaste! Comiste todas las pastillas.\n")
                break


# --------- Demo + Tests (modo NO interactivo) ---------

def demo_headless(cfg: GameConfig, dfa: DFA) -> None:
    print("[DEMO] Entorno no interactivo detectado. Ejecutando demo automática.\n")
    s0 = dfa.q0()
    render(cfg, s0, clear_screen=False)
    path = bfs_solve(dfa)
    if path is None:
        print("No existe camino que coma todas las pastillas sin morir para este mapa.")
        return
    print(f"Camino BFS ({len(path)} pasos): {path}\n")
    cur: State | TRAPType = s0
    for ch in path:
        cur = dfa.delta(cur, ch)
        render(cfg, cur, clear_screen=False)
    if dfa.is_accept(cur):
        print("\n[DEMO] ¡Ganaste! (aceptación alcanzada)\n")
    else:
        print("\n[DEMO] Terminado (no aceptación).\n")


def _assert(cond: bool, msg: str) -> Tuple[bool, str]:
    return (True, msg) if cond else (False, msg)


def run_tests() -> None:
    print("[TEST] Iniciando tests...\n")
    total = 0
    passed = 0

    def report(ok: bool, name: str):
        nonlocal total, passed
        total += 1
        if ok:
            passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name}")

    # --- Test 1: Aceptación inmediata si no hay pastillas ---
    grid_no_pills = """
#####
#S G#
#   #
#####
"""
    cfg1 = GameConfig(grid_no_pills)
    dfa1 = DFA(cfg1)
    ok1, name1 = _assert(dfa1.is_accept(dfa1.q0()) is True, "Acepta cuando no hay pastillas desde el inicio")
    report(ok1, name1)

    # --- Test 2: BFS encuentra camino en el SAMPLE_GRID ---
    cfg2 = GameConfig(SAMPLE_GRID)
    dfa2 = DFA(cfg2)
    path2 = bfs_solve(dfa2)
    ok2a, name2a = _assert(path2 is not None, "BFS encuentra un camino en SAMPLE_GRID")
    report(ok2a, name2a)
    if path2 is not None:
        end2 = apply_moves(dfa2, path2)
        ok2b, name2b = _assert(isinstance(end2, State) and dfa2.is_accept(end2), "Aplicar camino BFS llega a aceptación")
        report(ok2b, name2b)

    # --- Test 3: Chocar contra pared produce TRAP ---
    # Desde S en SAMPLE_GRID, mover 'U' sube a una pared.
    dfa3 = dfa2
    end3 = apply_moves(dfa3, 'U')
    ok3, name3 = _assert(not isinstance(end3, State), "Mover hacia pared produce TRAP")
    report(ok3, name3)

    # --- Test 4: Chocar contra fantasma produce TRAP ---
    # En la fila de S, un 'G' a la derecha. Con suficientes 'R' se llega a 'G'.
    end4 = apply_moves(dfa2, 'RRRRRR')  # debería alcanzar el fantasma
    ok4, name4 = _assert(not isinstance(end4, State), "Pisar fantasma produce TRAP")
    report(ok4, name4)

    # --- Test 5: Símbolos inválidos no cambian estado ---
    s0 = dfa2.q0()
    s_bad = dfa2.delta(s0, 'X')  # inválido
    ok5, name5 = _assert(s_bad == s0, "Símbolo inválido no altera el estado")
    report(ok5, name5)

    # --- Test 6: Mapa imposible (pastilla aislada) retorna None en BFS ---
    grid_blocked = """
######
#S o #
# ###
######
"""
    cfg6 = GameConfig(grid_blocked)
    dfa6 = DFA(cfg6)
    path6 = bfs_solve(dfa6)
    ok6, name6 = _assert(path6 is None, "BFS devuelve None si la pastilla es inalcanzable")
    report(ok6, name6)

    print(f"\n[TEST] Resultado: {passed}/{total} pasaron.")


# --------- Entry point ---------

def main():
    cfg = GameConfig(SAMPLE_GRID)
    dfa = DFA(cfg)

    if _is_tty():
        # Modo interactivo (terminal real)
        repl(cfg, dfa)
    else:
        # Modo no interactivo (sandbox / runner sin stdin):
        demo_headless(cfg, dfa)
        run_tests()


if __name__ == "__main__":
    main()
