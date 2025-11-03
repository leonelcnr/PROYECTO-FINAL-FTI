from automata.fa.dfa import DFA

dfa = DFA (
    states={'q0', 'q1', 'q2'},
    input_symbols={'a', 'b'},
    transitions={
        'q0': {'a': 'q1', 'b': 'q2'},
        'q1': {'a': 'q0', 'b': 'q2'},
        'q2': {'a': 'q2', 'b': 'q1'}
    },
    initial_state='q0',
    final_states={'q0'}
)

print("acepta") if dfa.accepts_input("aab") else print("no acepta")
print("acepta") if dfa.accepts_input("aa") else print("no acepta")

print(list(dfa.read_input_stepwise("aa")))    

