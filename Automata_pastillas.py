from automata.pda.dpda import DPDA


def automata_pastillas():
    pda = DPDA(
        states={'q0', 'q1', 'q2', 'q3'},
        input_symbols={'.', 'E','L'},
        stack_symbols={'P', 'Z', 'L'},
        transitions={
            'q0': {
                '.': {'L': ('q0', 'P')},
            },
            'q1': {
                '.': {'L': ('q1', 'P')},
            },
            'q2': {
                'E': {'Z': ('q3', 'L')},
                'L': {'P': ('q2', 'L')},
            }
        },
        initial_state='q0',
        initial_stack_symbol='Z',
        final_states={'q0'}
    )
    pda.show_diagram(input_str=None, with_machine=True, with_stack=True, path=None, layout_method='dot', horizontal=True, reverse_orientation=False, fig_size=None, font_size=14.0, arrow_size=0.85, state_separation=0.5)

automata_pastillas()