from Automata_Pacman import Turno, dfa_pacman
from exportar_dfa import export_dfa_to_json



if __name__ == "__main__":


    mapa_inicial = """
######
#S  G#
# G. #
#  G.#
#.  E#
######
""".strip("\n")

    grid = """
##############
#S .        G#
#  ##   #    #
# . E  .#    #
##############
""".strip("\n")

    grid2 = """
###############
#S       #   .#
#G    .       #
#  #      #   #
#  # #    #   #
# . .#  G ## E#
###############
""".strip("\n")

    grid3 = """
#######################
#S   .            G  E#
#  ########       #   #
# G . ## . G  #####.  #
#     ##      #       #
#G               .    #
#######################
""".strip("\n")

    lista_mapas = [mapa_inicial, grid, grid2, grid3]
    automatas = []
    mapas = []

    for mapa in lista_mapas:
        dfa, contexto = dfa_pacman(mapa)
        automatas.append(dfa)
        mapas.append(contexto)
        
    export_dfa_to_json(automatas, mapas)
        
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