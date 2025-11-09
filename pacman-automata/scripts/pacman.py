from Automata_Pacman import Turno, dfa_pacman
# from Automata_pastillas import Automata_Pastillas
from exportar_dfa import export_dfa_to_json


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
##############
#S .        G#
#  ##   #    #
# . E  .#    #
##############
""".strip("\n")

    grid2 = """
#####
#S  #
#G E#
#####
""".strip("\n")


    dfa, contexto = dfa_pacman(grid)
    export_dfa_to_json(dfa, contexto)
    # turno = Turno(dfa)
    
    # dfa.iter_transitions()
    # for trans in dfa.iter_transitions():
    #     print(trans)

    
    # print("Controles: W (arriba), A (izq), S (abajo), D (der). Enter vacío para salir.\n")
    # while True:
    #     print(render_ascii(contexto, turno.estado))
    #     if turno.esta_aceptado():
    #         print("\n¡Ganaste! Estás en 'E' y no queda ninguna pastilla.")
    #         break
    #     mov = input("\nMovimiento [W/A/S/D]: ").strip().upper()
    #     if mov == "":
    #         print("\nFin.")
    #         break
    #     try:
    #         turno.hacer_turno(mov)
    #         if turno.estado == "MUERTE":        
    #             print(render_ascii(contexto, turno.estado))
    #             break
    #     except Exception as e:
    #         print("Error:", e)