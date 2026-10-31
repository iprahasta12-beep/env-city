# heli_cycle: idle 0-20 (rotor stopped, spins up 18-20) · 20 lift + turn · 23 fly away · 27-57 gone (30s) · 57 fly back
# · 61 turn to pad · 62.5 descend · 64.5 rotor spin-down · 66 loop
HC = 66
S0, L0, F0, G0, G1, B1, D0, D1 = 18, 20, 23, 27, 57, 61, 62.5, 64.5
FLY = (760, 560)       # skeleton units (y-up): away to upper-right (off frame)
FX, FY = FLY
anims["heli_cycle"] = {
    "slots": {"heli_rotor": {"attachment": att_keys([(0, "rotor_blade"), (19.4, "rotor_blur"), (65.2, "rotor_blade")])},
              "heli_tail_rotor": {"attachment": att_keys([(0, "tail_rotor"), (19.4, "tail_rotor_blur"), (65.2, "tail_rotor")])},
              "heli_shadow": {"alpha": keys1([(0, 0.55), (L0, 0.55), (F0, 0.2), (F0 + 2, 0), (B1 - 2, 0), (B1, 0.2), (D1, 0.55), (HC, 0.55)])},
              "heli_body": {"alpha": [{"value": 1, "curve": "stepped"}, {"time": G0, "value": 0, "curve": "stepped"}, {"time": G1, "value": 1}]},
              "heli_rotor": {"alpha": [{"value": 1, "curve": "stepped"}, {"time": G0, "value": 0, "curve": "stepped"}, {"time": G1, "value": 1}]},
              "heli_tail_rotor": {"alpha": [{"value": 1, "curve": "stepped"}, {"time": G0, "value": 0, "curve": "stepped"}, {"time": G1, "value": 1}]}},
    "bones": {
        "heli_rotor": {"rotate": omega_keys([(0, 0), (S0, 0), (19.6, 1200), (D1, 1200), (HC, 0)], HC, step=0.1)},
        "heli_tail_rotor": {"rotate": omega_keys([(0, 0), (S0, 0), (19.6, 2400), (D1, 2400), (HC, 0)], HC, step=0.1)},
        "heli_lift": {
            "scale": keys2([(0, 1, 1), (L0, 1, 1), (F0, 1.35, 1.35), (G0, 1.6, 1.6), (G1, 1.6, 1.6), (B1, 1.35, 1.35), (D0, 1.35, 1.35), (D1, 1, 1), (HC, 1, 1)], k=0.45),
            "translate": [{"x": 0, "y": 0, "curve": "stepped"}, {"time": F0, "x": 0, "y": 0, "curve": easein2(F0, (0, 0), G0, FLY)},
                          {"time": G0, "x": FX, "y": FY, "curve": "stepped"}, {"time": G1, "x": FX, "y": FY, "curve": easeout2(G1, FLY, B1, (0, 0))},
                          {"time": B1, "x": 0, "y": 0}, {"time": HC, "x": 0, "y": 0}],
            "rotate": [{"value": 0, "curve": "stepped"}, {"time": L0 + 0.5, "value": 0, "curve": ease1(L0 + 0.5, 0, F0, -143.6)},
                       {"time": F0, "value": -143.6, "curve": "stepped"}, {"time": G1 - 0.01, "value": -143.6, "curve": "stepped"},
                       {"time": G1, "value": 36.4, "curve": "stepped"}, {"time": B1, "value": 36.4, "curve": ease1(B1, 36.4, D0, 0)},
                       {"time": D0, "value": 0}, {"time": HC, "value": 0}]},
        "heli_shadow": {
            "translate": [{"x": 10, "y": -12, "curve": "stepped"}, {"time": L0, "x": 10, "y": -12, "curve": ease2(L0, (10, -12), F0, (70, -80), 0.45)},
                          {"time": F0, "x": 70, "y": -80, "curve": easein2(F0, (70, -80), G0, (70 + FX, -80 + FY))},
                          {"time": G0, "x": 70 + FX, "y": -80 + FY, "curve": "stepped"},
                          {"time": G1, "x": 70 + FX, "y": -80 + FY, "curve": easeout2(G1, (70 + FX, -80 + FY), B1, (70, -80))},
                          {"time": B1, "x": 70, "y": -80, "curve": "stepped"}, {"time": D0, "x": 70, "y": -80, "curve": ease2(D0, (70, -80), D1, (10, -12), 0.45)},
                          {"time": D1, "x": 10, "y": -12}, {"time": HC, "x": 10, "y": -12}],
            "scale": keys2([(0, 1, 1), (L0, 1, 1), (F0, 0.8, 0.8), (D0, 0.8, 0.8), (D1, 1, 1), (HC, 1, 1)]),
            "rotate": [{"value": 0, "curve": "stepped"}, {"time": L0 + 0.5, "value": 0, "curve": ease1(L0 + 0.5, 0, F0, -143.6)},
                       {"time": F0, "value": -143.6, "curve": "stepped"}, {"time": G1, "value": 36.4, "curve": "stepped"},
                       {"time": B1, "value": 36.4, "curve": ease1(B1, 36.4, D0, 0)}, {"time": D0, "value": 0}, {"time": HC, "value": 0}]},
        "heli_body": {"translate": keys2([(0, 0, 0), (19.5, 0, 0), (19.6, 0.5, 0.4), (19.7, -0.4, -0.3), (19.8, 0, 0), (HC, 0, 0)], ease=False)},
    }}
anims["bus_static"] = {"bones": {"bus": {"translate": [{"x": 0, "y": 0}, {"time": 1, "x": 0, "y": 0}]}}}
