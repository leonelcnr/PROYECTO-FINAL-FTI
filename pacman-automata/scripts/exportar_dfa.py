# exportar_dfa.py
import json

def _state_str(st):
    # "MUERTE" queda igual; (x,y,mask) -> "x,y|mask"
    return st if isinstance(st, str) else f"{st[0]},{st[1]}|{st[2]}"

def export_dfa_to_json(dfa, ctx, path="../public/dfa.json"):
    def to_list_pairs(s):  # {(x,y),...} -> [[x,y],...]
        return [[x, y] for (x, y) in s]

    data = {
        "estado_inicial": _state_str(dfa.initial_state),
        "estados_finales":  [_state_str(s) for s in dfa.final_states],
        "alfabeto": sorted(list(dfa.input_symbols)),  # ej. ["A","D","S","W"] (+ "R" si lo modelaste)
        "transiciones": {
            _state_str(s): {a: _state_str(t) for a, t in dfa.transitions[s].items()}
            for s in dfa.states
        },
        "ctx": {
            "w": ctx["ancho"], "h": ctx["altura"],
            "paredes":   to_list_pairs(ctx["paredes"]),
            "fantasmas":  to_list_pairs(ctx["fantasmas"]),
            "inicio":   [ctx["inicio"][0], ctx["inicio"][1]],
            "meta":    ([ctx["meta"][0], ctx["meta"][1]] if ctx["meta"] is not None else None),
            "pastillas": [[x, y] for (x, y) in ctx["pastillas"]]  # el orden define los bits del mask
        }
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
