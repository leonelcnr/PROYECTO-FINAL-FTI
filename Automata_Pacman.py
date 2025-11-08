from collections import deque
from automata.fa.dfa import DFA

# dfa = DFA (
#     states={'q0', 'q1', 'q2'},
#     input_symbols={'a', 'b'},
#     transitions={
#         'q0': {'a': 'q1', 'b': 'q2'},
#         'q1': {'a': 'q0', 'b': 'q2'},
#         'q2': {'a': 'q2', 'b': 'q1'}
#     },
#     initial_state='q0',
#     final_states={'q0'}
# )

# print("acepta") if dfa.accepts_input("aab") else print("no acepta")
# print("acepta") if dfa.accepts_input("aa") else print("no acepta")

# print(list(dfa.read_input_stepwise("aa")))    

# --------------------

def mapa(mapa_str):
    filas = [list(r) for r in mapa_str.strip("\n").splitlines()]
    altura, ancho = len(filas), len(filas[0])
    inicio = None
    fantasmas = set()
    paredes = set()
    pastillas = []
    meta = None
    
    for y in range(altura):
        for x in range(ancho):
            c = filas[y][x]
            if c == '#': paredes.add((x,y))
            elif c == 'S': inicio = (x,y)
            elif c == 'G': fantasmas.add((x,y))
            elif c == '.': pastillas.append((x,y))
            elif c == 'E': meta = (x,y)
            # espacios ' ' son transitables
    if inicio is None:
        raise ValueError("Falta 'S' (inicio) en el mapa.")
    
    # terminar de entender el bitmask
    pastillas_index = {p:i for i,p in enumerate(pastillas)}
    full_mask = (1 << len(pastillas)) - 1
    
    return {
        "inicio": inicio, "fantasmas": fantasmas, "paredes": paredes,
        "pastillas": pastillas, "meta": meta, "altura": altura, "ancho": ancho,
        "full_mask": full_mask, "pastillas_index": pastillas_index
    }
    
    
def dfa_pacman(mapa_str):
    G = mapa(mapa_str)
    movimientos = {'W': (0,-1), 'S': (0,1), 'A': (-1,0), 'D': (1,0)}
    
    def dentro_del_mapa(x,y): return 0 <= x < G["ancho"] and 0 <= y < G["altura"]
    def es_muro(x,y): return (x,y) in G["paredes"]
    def es_fantasma(x,y): return (x,y) in G["fantasmas"]
    def es_pastilla(x,y): return (x,y) in G["pastillas_index"]
    def es_meta(x,y): return (x,y) == G["meta"]
    
    q0 = (G["inicio"][0], G["inicio"][1], G["full_mask"]) # (cordenada x, cordenada y, bitmask)
    MUERTE = "MUERTE"
    
    states = set([q0, MUERTE])
    input_symbols = set(movimientos.keys())
    transiciones = {}
    finals = set()
    
    transiciones[MUERTE] = {c: MUERTE for c in input_symbols}
    
    queue = deque([q0])
    seen = set([q0])
    
    
    #LA IDE DE ACA ES VERIFICAR Y AGREGAR TODOS LOS ESTADOS POSIBLES 
    #QUE SE PUEDEN OBTENER DESDE CADA UNO DE LOS ESTADOS EN LA COLA
    
    while queue:
        (x, y, mask) = queue.popleft()
        transiciones [(x,y,mask)] = {}
        mask_vacia = mask == 0
        
        if es_meta(x, y) and mask_vacia:
            finals.add((x, y, mask))

        # Explora movimientos posibles
        #Parte desde la posicion actual (x, y) y verifica si se puede mover en cada direccion
        # Si se puede mover, se agrega el nuevo estado a la cola y al conjunto de estados visitados
        # Si se mueve a una pastilla, se actualiza la mascara para reflejar que la pastilla ha sido consumida
        # Si se mueve a un fantasma, se marca como muerte
        # Si se mueve a un espacio transitable, se mantiene la mascara sin cambios
        
        for c, (dx, dy) in movimientos.items():
            nx, ny = x + dx, y + dy # x,y son las coordenadas actuales, dx, dy son los cambios en x,y
            
            if (not dentro_del_mapa(nx, ny)) or es_muro(nx, ny):
                transiciones[(x,y,mask)][c] = (x,y,mask)
                continue
            
            if es_fantasma(nx, ny):
                transiciones[(x,y,mask)][c] = MUERTE
                continue
            
            nueva_mask = mask
            if es_pastilla(nx, ny):
                i = G["pastillas_index"][(nx, ny)]
                if (nueva_mask >> i) & 1:
                    nueva_mask = nueva_mask & ~(1 << i)
            
            qn = (nx, ny, nueva_mask)
            transiciones[(x,y,mask)][c] = qn    
            
            if qn not in seen:
                seen.add(qn)
                states.add(qn)
                queue.append(qn)
        
    
    states.update(seen)
            
            
    dfa = DFA(
        states=states,
        input_symbols=input_symbols,
        transitions=transiciones,
        initial_state=q0,
        final_states=finals
    )
    
    return dfa, G


# -------------------------------------------------------

class Turno:
    def __init__(self, automata):
        self.automata = automata
        self.estado = automata.initial_state

    def hacer_turno(self, movimiento: str):
        # """Avanza 1 símbolo (W/A/S/D). Devuelve el nuevo estado."""
        movimiento = movimiento.upper()
        if movimiento not in self.automata.input_symbols:
            raise ValueError(f"Símbolo inválido: {movimiento}. Usá {sorted(self.automata.input_symbols)}")
        
        self.estado = self.automata.transitions[self.estado][movimiento]
        return self.estado
    
    def esta_aceptado(self) -> bool:
        # """¿Está en un estado final? (todas las pastillas comidas y en meta si corresponde)."""
        return self.estado in self.automata.final_states
    
    def resetear(self):
        # """Volver al estado inicial."""
        self.estado = self.automata.initial_state



# =========================
# Render ASCII del estado actual
# =========================
def render_ascii(contexto, state) -> str:
    G = contexto
    """Devuelve un string con el laberinto en ASCII según el 'state' (x,y,mask) o 'MUERTE'."""
    # recuperar contexto
    if isinstance(contexto, dict):
        G = contexto
    else:
        G = getattr(contexto, "_ctx", None)
    if G is None:
        raise ValueError("No se encontró el contexto del mapa (G).")

    # base vacía
    rows = [[' ' for _ in range(G["ancho"])] for _ in range(G["altura"])]

    # paredes
    for (x, y) in G["paredes"]:
        rows[y][x] = '#'

    # meta
    if G["meta"] is not None:
        mx, my = G["meta"]
        rows[my][mx] = 'E'

    # fantasmas
    for (x, y) in G["fantasmas"]:
        rows[y][x] = 'G'

    # estado puede ser 'MUERTE'
    if state == "MUERTE":
        # dibujamos todo estático; marcamos inicio y mostramos HUD abajo
        sx, sy = G["inicio"]
        if rows[sy][sx] == ' ':
            rows[sy][sx] = 'S'
        grid = "\n".join("".join(r) for r in rows)
        hud = "\n[MUERTE] Caíste en un fantasma. La palabra queda rechazada."
        return grid + hud

    # si es tupla (x,y,mask)
    x, y, mask = state

    # pastillas (sólo las que aún faltan, según mask)
    for (px, py), i in G["pastillas_index"].items():
        if (mask >> i) & 1:
            # falta comerla → dibujar '.'
            rows[py][px] = '.'
        else:
            # ya comida → dejar como camino (espacio), salvo si era pared/otro
            if rows[py][px] == ' ':
                rows[py][px] = ' '

    # inicio (si querés verlo cuando no está P encima)
    sx, sy = G["inicio"]
    if (sx, sy) != (x, y) and rows[sy][sx] == ' ':
        rows[sy][sx] = 'S'

    # Pac-Man
    rows[y][x] = 'P'

    grid = "\n".join("".join(r) for r in rows)

    # HUD
    faltan = mask.bit_count()
    en_meta = (G["meta"] is not None) and ((x, y) == G["meta"])
    hud = f"\nPosición: ({x},{y}) | Pastillas restantes: {faltan} | En meta: {en_meta}"
    return grid + hud


if __name__ == "__main__":
    grid = """
#########
#S .   G#
#  ##   #
# . E  .#
#########
""".strip("\n")
    
    dfa, contexto = dfa_pacman(grid)
    turno = Turno(dfa)
    # print(grid)
    
    # while True:
        
    # palabra = "DDDDSSDDAAAAADD"
    # print(dfa.read_input(palabra))
    # print(dfa.accepts_input(palabra))
    
    print("Controles: W (arriba), A (izq), S (abajo), D (der). Enter vacío para salir.\n")
    while True:
        print(render_ascii(contexto, turno.estado))
        if turno.esta_aceptado():
            print("\n¡Ganaste! Estás en 'E' y no queda ninguna pastilla.")
            break
        mov = input("\nMovimiento [W/A/S/D]: ").strip().upper()
        if mov == "":
            print("\nFin.")
            break
        try:
            turno.hacer_turno(mov)
            if turno.estado == "MUERTE":        
                print(render_ascii(contexto, turno.estado))
                break
        except Exception as e:
            print("Error:", e)