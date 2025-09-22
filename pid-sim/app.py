from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/simulate", methods=["POST"])
def simulate():
    dados = request.get_json(force=True)

    # Ganhos e tempo
    kp = float(dados.get("kp", 1.0))
    ki = float(dados.get("ki", 0.0))
    kd = float(dados.get("kd", 0.0))
    Ts = float(dados.get("tempo_amostragem", 1.0))

    # Execução
    N = int(dados.get("quantidade_amostras", 100))
    u_min = float(dados.get("minimo_saida", -10.0))
    u_max = float(dados.get("maximo_saida", 10.0))

    # Entradas de operação
    modo = str(dados.get("modo", "AUTO")).upper()         # "AUTO" ou "MANUAL"
    erro_constante = float(dados.get("erro_constante", 0.0))
    correcao_manual = float(dados.get("correcao_manual", 0.0))  # M[k] manual

    # Estados do erro (e[k-1], e[k-2])
    e = 0.0
    e1 = 0.0
    e2 = 0.0

    # Memórias da saída:
    # u_sat_prev = saída aplicada (limitada)
    # u_nsat_prev = saída interna (sem limite)
    u_sat_prev = 0.0
    u_nsat_prev = 0.0

    k = 0
    amostras = []
    saida = []

    while k < N:
        if modo == "MANUAL":
            # Em MANUAL, a saída é o valor informado pelo usuário
            u_sat = correcao_manual
            u_nsat = correcao_manual  # tracking interno (prepara bumpless)
            e = erro_constante        # erro pode ficar visível, mas não entra no cálculo aqui

        else:  # AUTO
            # Bumpless simples: se veio de um valor manual, alinhar memória na primeira amostra
            if k == 0 and correcao_manual != 0.0:
                u_sat_prev = correcao_manual
                u_nsat_prev = correcao_manual
                e1 = erro_constante
                e2 = erro_constante

            # Erro usado no cálculo
            e = erro_constante

            # Termos incremental do PID
            p_term = kp * (e - e1)
            i_term = ki * Ts * e
            d_term = (kd / Ts) * (e - 2.0 * e1 + e2)

            # Tentativa sem limite
            u_nsat_try = u_nsat_prev + p_term + i_term + d_term

            # Aplica saturação
            if u_nsat_try > u_max:
                u_sat_try = u_max
            elif u_nsat_try < u_min:
                u_sat_try = u_min
            else:
                u_sat_try = u_nsat_try

            # Anti-windup por clamping:
            # Se saturou e o termo integral empurra na mesma direção da saturação,
            # não acumula a parte integral nesta amostra.
            if u_sat_try != u_nsat_try:
                if u_sat_try == u_max and i_term > 0:
                    i_term_eff = 0.0
                elif u_sat_try == u_min and i_term < 0:
                    i_term_eff = 0.0
                else:
                    i_term_eff = i_term

                u_nsat = u_nsat_prev + p_term + i_term_eff + d_term
                # Reaplica saturação após ajustar o integral
                if u_nsat > u_max:
                    u_sat = u_max
                elif u_nsat < u_min:
                    u_sat = u_min
                else:
                    u_sat = u_nsat
            else:
                # Não saturou: usa integral normalmente
                u_nsat = u_nsat_try
                u_sat = u_sat_try

        # Guarda histórico
        amostras.append(k)
        saida.append(u_sat)

        # Avança estados
        e2 = e1
        e1 = e
        u_nsat_prev = u_nsat
        u_sat_prev = u_sat
        k += 1

    return jsonify({"amostras": amostras, "saida": saida})


if __name__ == "__main__":
    app.run(debug=True)
