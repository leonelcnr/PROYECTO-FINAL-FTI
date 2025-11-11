from collections import deque
from automata.fa.dfa import DFA
from automata.fa.nfa import NFA


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
    if inicio is None:
        raise ValueError("Falta 'S' (inicio) en el mapa.")
    

    
    return {
        "inicio": inicio, "fantasmas": fantasmas, "paredes": paredes,
        "pastillas": pastillas, "meta": meta, "altura": altura, "ancho": ancho
    }
    
    


def dfa_pacman(mapa_str):
    G = mapa(mapa_str)
    movimientos = {'W': (0,-1), 'S': (0,1), 'A': (-1,0), 'D': (1,0)}
    
    def dentro_del_mapa(x,y): return 0 <= x < G["ancho"] and 0 <= y < G["altura"]
    def es_muro(x,y): return (x,y) in G["paredes"]
    def es_fantasma(x,y): return (x,y) in G["fantasmas"]
    def es_pastilla(x,y): return (x,y) in G["pastillas"]
    def es_meta(x,y): return (x,y) == G["meta"]
    
    q0 = (G["inicio"][0], G["inicio"][1])
    MUERTE = "MUERTE"
    PASTILLA = "PASTILLA"
    
    estados = set([q0, MUERTE])
    simbolos_entrada = set(movimientos.keys() | {'R'})
    transiciones = {}
    finals = set()

    transiciones[MUERTE] = {c: MUERTE for c in simbolos_entrada if c != 'R'}
    transiciones[MUERTE]['R'] = q0
    
    queue = deque([q0])
    seen = set([q0])
    
    
    #LA IDE DE ACA ES VERIFICAR Y AGREGAR TODOS LOS ESTADOS POSIBLES 
    #QUE SE PUEDEN OBTENER DESDE CADA UNO DE LOS ESTADOS EN LA COLA
    
    while queue:
        (x, y) = queue.popleft()
        transiciones [(x,y)] = {}
        
        if es_meta(x, y):
            finals.add((x, y))

        # Explora movimientos posibles
        #Parte desde la posicion actual (x, y) y verifica si se puede mover en cada direccion
        # Si se puede mover, se agrega el nuevo estado a la cola y al conjunto de estados visitados
        # Si se mueve a una pastilla, se actualiza la mascara para reflejar que la pastilla ha sido consumida
        # Si se mueve a un fantasma, se marca como muerte
        # Si se mueve a un espacio transitable, se mantiene la mascara sin cambios
        
        for c, (dx, dy) in movimientos.items():
            nx, ny = x + dx, y + dy # x,y son las coordenadas actuales, dx, dy son los cambios en x,y
            
            if (not dentro_del_mapa(nx, ny)) or es_muro(nx, ny):
                transiciones[(x,y)][c] = (x,y)
                continue
            
            if es_fantasma(nx, ny):
                transiciones[(x,y)][c] = MUERTE
                continue
            
            
            qn = (nx, ny)
            transiciones[(x,y)][c] = qn    
            
            transiciones[(x,y)]['R'] = (x, y)
            
            if qn not in seen:
                seen.add(qn)
                estados.add(qn)
                queue.append(qn)
        
    
    estados.update(seen)
            
            
    dfa = DFA(
        states=estados,
        input_symbols=simbolos_entrada,
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
        movimiento = movimiento.upper()
        if movimiento not in self.automata.input_symbols:
            raise ValueError(f"Símbolo inválido: {movimiento}. Usá {sorted(self.automata.input_symbols)}")
        
        self.estado = self.automata.transitions[self.estado][movimiento]
        return self.estado
    
    def esta_aceptado(self) -> bool:
        return self.estado in self.automata.final_states
    
    def resetear(self):
        self.estado = self.automata.initial_state
