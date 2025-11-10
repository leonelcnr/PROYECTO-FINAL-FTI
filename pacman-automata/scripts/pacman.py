from Automata_Pacman import Turno, dfa_pacman
# from Automata_pastillas import Automata_Pastillas
from exportar_dfa import export_dfa_to_json



if __name__ == "__main__":
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


    dfa, contexto = dfa_pacman(grid2)
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