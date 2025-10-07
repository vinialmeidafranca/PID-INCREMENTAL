import time #delay de tempo 
import msvcrt #leitura de teclado em tempo real no Windows
import random
import math

# ==================== MODIFICAÇÕES FEITAS/PENDENTES ======================
# !! 1° TRABALHO
#   -> Derivada no set point: adicionei a equação de ação derivativa que mandei no grupo, não sei é só isso. 
#      E pelo que entendi, ela substitui a fórmula que estamos usando até então (com A0, A1 e A2) # === MARIA ===
#   -> Opção de bumpless rampa/ou "copia e cola": não adicionei. Isso seria extra, pode deixar só o rampa mesmo # === MARIA ===
# !! 2° TRABALHO
#   -> por enquanto só coloquei a equação p/ Ck que ele passou (função simu_feedback_processo); 
#    É chamada no automático e manual para simular o Ck (Variável de processo) de acordo com a correção Mk # === MARIA ===

def simu_feedback_processo(k, Mk, Mp, mk_history, Cp, T, Tm, Tal, Ganhok): # === MARIA ===
    
    Ck_simu = 0.0

    n = 1 + (Tm/T)
    An = Ganhok * (1 - pow(math.e,(-T/Tal)))
    B1 = pow(math.e,(-T/Tal))
    
    Ck_simu = An * mk_history[k-n] + B1 * Cp # === MARIA === Na fórmula que ele passou, é m(k-1) ou m(k-n)? Se for m(k-1), usa Mp no lugar de mk_history[k-n].
    
    return Ck_simu

def main():
    """
    Permite alternar entre modo automático e manual em tempo real
    usando as teclas 'A' e 'M'.
    """
    
    # Declaração de variáveis
    # A0, A1, A2 = constantes PID
    # T = período de amostragem em segundos
    # K = n° amostras
    # Rk = Setpoint atual; Ck = Saída atual/Variável de processo; Mk = Correção atual; Ek = Erro atual;
    # Rp, Cp, Mp, Ep, Rpp, Cpp, Epp = valores de amostras anteriores.
    
    T = 0
    K = 0
    acao = 0
    min_limite = 0
    max_limite = 100 # <----- O máximo foi alterado para ter margem para subir e descer, de acordo com o comando
    A0 = 0.0
    A1 = 0.0
    A2 = 0.0
    Kp = 0.0
    Ki = 0.0
    Kd = 0.0
    Rk = Ck = Ek = Rp = Cp = Mp = Ep = Rpp = Cpp = Mk = Epp = Mk_manual = Mk_auto = E_cte = aux = 0.0
    Mk_inicial = (max_limite - min_limite)/2
    modo_manual = False
    modo_anterior_manual = False
    primeira = True # <-----essa váriavel é apenas para que a primeira vez que o código rodar, Mk inicie em 100
    
    # ===== Variáveis Trabalho 2 ========
    Tm = 0.0 # === MARIA ===
    Tal = 0.0 # === MARIA ===
    GanhoK = 0.0 # === MARIA ===

    # ===== Variáveis de tracking ========
    Rk_simu = 0 ### Setpoint 
    MV_simu = [] ### Vetor MV

    # armazenar o histórico de valores 
    k_history = []
    mk_history = []
    ck_history = []

    print("===============INICIALIZACAO================\n")

    try:
        T = int(input("Digite o periodo de amostragem em segundos: "))
        K = int(input("Digite o numero de amostras: "))
        E_cte = float(input("Digite o erro constante: "))
        Rk_simu = float(input("Informe o SetPoint: "))#<---- Entrada do SetPoint

        Tm = float(input("Digite o tempo morto do processo em segundos: ")) # === MARIA ===
        Tal = float(input("Digite a constante de tempo do processo em segundos: ")) # === MARIA ===
        GanhoK = float(input("Digite o ganho do processo: ")) # === MARIA ===

        while acao not in [1, 2]:
            acao = int(input("Digite 1 - Acao Direta / 2 - Acao Reversa: "))

        while Kp == 0 or Ki == 0 or Kd == 0:
            Kp = float(input("Digite o valor do Kp: "))
            Ki = float(input("Digite o valor do Ki: "))
            Kd = float(input("Digite o valor do Kd: "))

    except ValueError:
        print("Erro: Por favor, digite um valor numerico valido.")
        return

    # constantes PID incremental
    A0 = Kp * (1.0 + T / Ki + Kd / T)
    A1 = -Kp * (1.0 + 2.0 * Kd / T)
    A2 = Kp * (Kd / T)

    print("\n===============SIMULACAO================\n")
    print("Pressione 'A' para o modo automatico ou 'M' para o modo manual.")
    print("Pressione 'Q' para sair.\n")
    
    MV_simu = [0.0] * K # MARIA

    k = 0
    while k < K:
        # verifica se alguma tecla foi pressionada
        if msvcrt.kbhit(): # checagem do teclado - interrupção - acontece a cada amostra 
            tecla_bytes = msvcrt.getch()
            tecla = tecla_bytes.decode('utf-8').lower()
            
            print(f"Tecla pressionada: {tecla}")

            if tecla == 'a':
                modo_manual = False
                print("MODO: Automatico")
            elif tecla == 'm':
                modo_manual = True
                print("MODO: Manual")
            elif tecla == 'q':
                print("Simulacao encerrada pelo usuario.")
                break

        if not modo_manual:
            if modo_anterior_manual:
                Mp = Mk_manual
                modo_anterior_manual = False

            if acao == 1:
                Ek = Ck - Rk
                # Ek = -E_cte # <----- Acao Direta, o valor é invertido
            elif acao == 2:
                Ek = Rk + Ck
                # Ek = E_cte

            if primeira: # <----- Primeira vez que o código roda, inicia em 100 que é nosso 50%
                Mp = Mk_inicial # para começar em 50% -> bias; Mk inicializado em 100
                Mk_auto = (A0 * Ek) + (A1 * Ep) + (A2 * Epp) + Mp
                # ACÃO DERIVATIVA: Mk_auto = kp * (Ek - Ep) + (Kp/ki) * T * Ek + (kd/kp)/T * (Ck - 2 * Cp + Cpp) + Mp # === MARIA ===
                Mp = Mk_auto 
                primeira = False
            else:
                # CÁLCULO DA CORREÇÃO ATUAL
                Mk_auto = (A0 * Ek) + (A1 * Ep) + (A2 * Epp) + Mp
                # ACÃO DERIVATIVA: Mk_auto = kp * (Ek - Ep) + (Kp/ki) * T * Ek + (kd/kp)/T * (Ck - 2 * Cp + Cpp) + Mp # === MARIA ===
                Mk = Mk_auto # <----- Guarda sempre o valor corrigido de Mk auto
                aux = Mk - Mp # <----- Essa auxiliar ajuda a verificar o padrão para a ser seguido ao mudar de auto/manual

            # Logica anti reset wind up
            if Mk > max_limite:
                Mk = float(max_limite)
                Mk_auto = Mk #  === MARIA === SÓ POR CAUSA DA FUNÇÃO FEEDBACK
            elif Mk < min_limite:
                Mk = float(min_limite)
                Mk_auto = Mk # === MARIA === SÓ POR CAUSA DA FUNÇÃO FEEDBACK

            Ck = simu_feedback_processo(k, Mk_auto, Mp, mk_history, Cp, T, Tm, Tal, GanhoK) # === MARIA ===

        else:
            try:
                Mk_manual = float(input("Digite o valor da correcao manual: "))

                if primeira: # <----- Primeira vez que o código roda, inicia em 100 que é nosso 50%
                    Mp = Mk_inicial # para começar em 50% -> bias; Mk_inicial inicializado em (max-min)/2
                    Mk = (A0 * Ek) + (A1 * Ep) + (A2 * Epp) + Mp
                    # ACÃO DERIVATIVA: Mk = kp * (Ek - Ep) + (Kp/ki) * T * Ek + (kd/kp)/T * (Ck - 2 * Cp + Cpp) + Mp # === MARIA ===
                    Mp = Mk 
                    primeira = False

                if not modo_anterior_manual:
                    Mp = Mk_auto
                    modo_anterior_manual = True   
                    
                    if acao == 2: #<-----Se estiver no modo reverso o bumpless é diferente do direto
                        if Mk_manual > Mk_auto:#<-----Se estiver no modo reverso o bumpless é diferente do direto
                            Mk = Mk_auto
                            while Mk_manual > Mk:
                                Mk = (A0 * Ek) + (A1 * Ep) + (A2 * Epp) + Mp
                                # ACÃO DERIVATIVA: Mk = kp * (Ek - Ep) + (Kp/ki) * T * Ek + (kd/kp)/T * (Ck - 2 * Cp + Cpp) + Mp # === MARIA ===
                                Mp = Mk 
                                Epp = Ep 
                                Ep = Ek 
                                print(f"Teste - Amostra {k}/ Erro constante: {E_cte} / Mk = {Mk} (MODO: {'MANUAL' if modo_manual else 'AUTOMATICO'})")
                                #^^^^ este print ser pra ver que ocorreu o bumpless e cada atualização não conta como nova amostra, permanece a mesma
                        else :
                            Mk = Mk_auto
                            while Mk_manual < Mk:
                                #if aux <= 0:   # segurança
                                    #break
                                Mk = Mk - aux
                                print(f"Reversa - Amostra {k}/ Erro constante: {E_cte} / Mk = {Mk} (MODO: {'MANUAL' if modo_manual else 'AUTOMATICO'})")
                                #^^^^ este print ser pra ver que ocorreu o bumpless e cada atualização não conta como nova amostra, permanece a mesma
                    
                    elif acao == 1:#<-----bumpless acao direta
                        if Mk_manual > Mk_auto:# <----- Para não ocorrer o bump e ocorrer de forma linear. 
                            Mk = Mk_auto
                            while Mk_manual > Mk:
                                Mk = Mk - aux
                                print(f"Direta - Amostra {k}/ Erro constante: {E_cte} / Mk = {Mk} (MODO: {'MANUAL' if modo_manual else 'AUTOMATICO'})")
                                #^^^^ este print ser pra ver que ocorreu o bumpless e cada atualização não conta como nova amostra, permanece a mesma
                        else :
                            Mk = Mk_auto
                            while Mk_manual < Mk:
                                Mk = (A0 * Ek) + (A1 * Ep) + (A2 * Epp) + Mp
                                # ACÃO DERIVATIVA: Mk = kp * (Ek - Ep) + (Kp/ki) * T * Ek + (kd/kp)/T * (Ck - 2 * Cp + Cpp) + Mp # === MARIA ===
                                Mp = Mk 
                                Epp = Ep 
                                Ep = Ek 
                                print(f"Direta - Amostra {k}/ Erro constante: {E_cte} / Mk = {Mk} (MODO: {'MANUAL' if modo_manual else 'AUTOMATICO'})")
                                #^^^^ este print ser pra ver que ocorreu o bumpless e cada atualização não conta como nova amostra, permanece a mesma

                Mk = Mk_manual
                Ck = simu_feedback_processo(k, Mk_manual, Mp, mk_history, Cp, T, Tm, Tal, GanhoK) # === MARIA ===
                
            except ValueError:
                print("Entrada invalida. Usando o ultimo valor.")
                
        # Adiciona os valores nas listas (equivalente ao push_back)
        k_history.append(k)
        mk_history.append(Mk)
        ck_history.append(Ck) # === MARIA === HISTÓRICO DE VARIAÇÃO DA VP. IMPRIMIR EM UM SEGUNDO GRÁFICO

        if k == 0: ### SIMULAÇÃO DA VARIAÇÃO DE MV; supondo uma variação entre a ação do controlador (Mk) e a resposta do atuador (MV).
            MV_simu[k] = 0.5 * Mk ###
        else: ###
            MV_simu[k] = MV_simu[k-1] + 0.05 * Mk ###

        print(f"Amostra {k}/ Setpoint {Rk_simu} / Erro constante: {E_cte} / Mk = {Mk} / MV {MV_simu[k]:.1f} (MODO: {'MANUAL' if modo_manual else 'AUTOMATICO'})") # MARIA: INCLUSÃO DE SET POINT E MV SIMULADAS
        
        # Atualiza as variáveis para a próxima amostra 
        Mp = Mk
        Epp = Ep
        Ep = Ek
        Cpp = Cp
        Cp = Ck
        Rpp = Rp
        Rp = Rk
        
        k += 1 # Incrementa o contador da amostra
        time.sleep(T) # Simula o periodo de amostragem

    # Imprime o historico completo no final da simulacao
    print("\n===============HISTORICO DE VALORES================\n")
    print("k,Mk,Ck")
    for i in range(len(k_history)):
        print(f"{k_history[i]},{mk_history[i]:.2f},{ck_history[i]:.2f}")

if __name__ == "__main__":
    main()