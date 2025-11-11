import json

def _state_str(st):
    return st if isinstance(st, str) else f"{st[0]},{st[1]}"

def export_dfa_to_json(lista_dfa, lista_ctx, path="../public/dfa.json"):
    def to_list_pairs(s):  
        return [[x, y] for (x, y) in s]
    
    mapas = []
    i = 0
    for dfa, ctx in zip(lista_dfa, lista_ctx):
        i += 1
        mapa = {
            "estado_inicial": _state_str(dfa.initial_state),
            "estados_finales":  [_state_str(s) for s in dfa.final_states],
            "alfabeto": sorted(list(dfa.input_symbols)),
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
                "pastillas": [[x, y] for (x, y) in ctx["pastillas"]]
            }
        }
        mapas.append(mapa)
        
    
    datas = {
        f"mapa_{i}": mapa
        for i, mapa in enumerate(mapas)
    }
        
    with open(path, "w", encoding="utf-8") as f:
        json.dump(datas, f, ensure_ascii=False)
