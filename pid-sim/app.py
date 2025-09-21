from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/simulate", methods=["POST"])
def simulate():
    dados = request.get_json(force=True)

    kp = float(dados.get("kp", 1.0))
    ki = float(dados.get("ki", 0.0))
    kd = float(dados.get("kd", 0.0))
    tempo_amostragem = float(dados.get("tempo_amostragem", 1.0))
    quantidade_amostras = int(dados.get("quantidade_amostras", 100))

    modo = str(dados.get("modo", "AUTO")).upper()  
    erro_manual = float(dados.get("erro_manual", 0.0))
    rampa_setpoint = float(dados.get("rampa_setpoint", 0.2))
    pv_constante = float(dados.get("pv_constante", 0.0))  

    minimo_saida = float(dados.get("minimo_saida", -10.0))
    maximo_saida = float(dados.get("maximo_saida",  10.0))

    amostra = 0
    erro = 0.0
    erro_anterior = 0.0
    erro_antes_anterior = 0.0
    saida_anterior = 0.0
    saida_atual = 0.0

    historico_amostras = []
    historico_saida = []

    while amostra < quantidade_amostras:
        if modo == "MANUAL":
            erro = erro_manual
        else:
            setpoint = rampa_setpoint * amostra
            erro = setpoint - pv_constante

        incremento = (
            kp * (erro - erro_anterior)
            + ki * tempo_amostragem * erro
            + (kd / tempo_amostragem) * (erro - 2.0 * erro_anterior + erro_antes_anterior)
        )

        saida_calculada = saida_anterior + incremento

        if saida_calculada > maximo_saida:
            saida_atual = maximo_saida
        elif saida_calculada < minimo_saida:
            saida_atual = minimo_saida
        else:
            saida_atual = saida_calculada

        
        historico_amostras.append(amostra)
        historico_saida.append(saida_atual)

        
        erro_antes_anterior = erro_anterior
        erro_anterior = erro
        saida_anterior = saida_atual
        amostra += 1

    return jsonify({
        "amostras": historico_amostras,
        "saida": historico_saida
    })

if __name__ == "__main__":
    app.run(debug=True)
