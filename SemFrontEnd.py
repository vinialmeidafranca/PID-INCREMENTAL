import time # aplica delay de T após cada correção

# Sem front end: 
#  - inicializar todas as variáveis antes de rodar o código manual ou automático
#  - tratar interrupção de mudança de modo
#  - escolher ação direta ou indireta
#  - gerar lista de Mk e k para plotar gráfico no excel

# variáveis que seriam definidas via formulário html/flask
Kp = 0.0
Ki = 0.0
Kd = 0.0
T = 0 # período de amostragem em segundos
K = 0 # qttde amostras
min_limite = 0
max_limite = 100
erro_constante = 0.0
modo_manual = False
acao_direta = True

# variáveis de estado do controlador
modo_anterior_manual = False

# histórico de variáveis
Rk, Ck, Mk = 0.0, 0.0, 0.0
Ek, Ep, Epp = 0.0, 0.0, 0.0
Rp, Cp, Mp = 0.0, 0.0, 0.0
Rpp, Cpp, Epp = 0.0, 0.0, 0.0
Mk_manual = 0.0
Mk_history = []
k_history = []

def calcula_coeficientes():
    if Ki == 0 or T == 0:
        return 0, 0, 0
    
    A0 = Kp * (1.0 + T / Ki + Kd / T) 
    A1 = -Kp * (1.0 + 2.0 * Kd / T)
    A2 = Kp * (Kd / T)

    return A0, A1, A2

def controlador_loop(k):
    """Executa uma única iteração do loop do controlador."""
    global Ek, Ep, Epp, Mk, Mp, Cp, Cpp, Rp, Rpp, modo_anterior_manual

    print(f"\n[SIMULAÇÃO] Amostra: {k+1}")
    print(f"Erro constante: {erro_constante}")
    
    # Controlador
    if not modo_manual: # automatico
        # bumpless
        if modo_anterior_manual:
            Mp = Mk_manual
            modo_anterior_manual = False
        
        # Ação Direta/Reversa
        if acao_direta:
            Ek = erro_constante # sem set point e vp
            # Ek = Rk - Ck erro atual
        else:
            Ek = erro_constante # sem set point e vp
            # Ek = - Rk + Ck erro atual
            
        # Cálculo da Correção (Mk)
        A0, A1, A2 = calcula_coeficientes()
        Mk = (A0 * Ek) + (A1 * Ep) + (A2 * Epp) + Mp
        
        # Lógica Anti-Reset Windup
        if Mk > max_limite:
            Mk = max_limite
        elif Mk < min_limite:
            Mk = min_limite
        
    else: # modo manual
        modo_anterior_manual = True
        Mk_manual = float(input("Digite o valor da correção manual: "))
        Mk = Mk_manual
        
    # === Atualização das Variáveis de Estado para a Próxima Iteração ===
    Mp = Mk
    Ep = Ek
    Epp = Ep
    Cp = Ck
    Cpp = Cp
    Rp = Rk
    Rpp = Rp

    #para  o gráfico
    Mk_history.append(Mk)
    k_history.append(k)
    
    # Exibir o resultado
    print(f"Correção aplicada: {Mk}")

# === Loop Principal ===
if __name__ == "__main__":
    
    T = float(input("Digite o período de amostragem em segundos: "))
    K = int(input("Digite o número de amostras: "))
    erro_constante = float(input("Digite o erro constante: "))
    Kp = float(input("Digite o valor do Kp: "))
    Ki = float(input("Digite o valor do Ki: "))
    Kd = float(input("Digite o valor do Kd: "))
    
    for k in range(K):
        controlador_loop(k)
        time.sleep(T) #atraso para o período de amostragem em segundos !!!

    print("\n--- Dados para o gráfico Mk x k ---")
    print("k:", k_history)
    print("Mk:", Mk_history)