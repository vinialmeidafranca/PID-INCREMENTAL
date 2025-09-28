import time #delay de tempo 
import msvcrt #leitura de teclado em tempo real no Windows

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
    max_limite = 200 # <----- O máximo foi alterado para ter margem para subir e descer, de acordo com o comando
    A0 = 0.0
    A1 = 0.0
    A2 = 0.0
    Kp = 0.0
    Ki = 0.0
    Kd = 0.0
    Rk = Ck = Ek = Rp = Cp = Mp = Ep = Rpp = Cpp = Epp = Mk_manual = Mk_auto = E_cte = aux = 0.0
    Mk = 100.0
    modo_manual = False
    modo_anterior_manual = False
    primeira = True # <-----essa váriavel é apenas para que a primeira vez que o código rodar, Mk inicie em 100
    
    # armazenar o histórico de valores 
    k_history = []
    mk_history = []

    print("===============INICIALIZACAO================\n")

    try:
        T = int(input("Digite o periodo de amostragem em segundos: "))
        K = int(input("Digite o numero de amostras: "))
        E_cte = float(input("Digite o erro constante: "))

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
                # Ek = Ck - Rk
                Ek = -E_cte # <----- Acao Direta, o valor é invertido
            elif acao == 2:
                # Ek = Rk + Ck
                Ek = E_cte

            if primeira: # <----- Primeira vez que o código roda, inicia em 100 que é nosso 50%
                Mp = Mk # para começar em 50% -> bias; Mk inicializado em 100
                Mk = (A0 * Ek) + (A1 * Ep) + (A2 * Epp) + Mp
                Mp = Mk 
                primeira = False
            else:
                # CÁLCULO DA CORREÇÃO ATUAL
                Mk = (A0 * Ek) + (A1 * Ep) + (A2 * Epp) + Mp
                Mk_auto = Mk # <----- Guarda sempre o valor corrigido de Mk auto
                #print (f"MK: {Mk}A0 = {A0} Ek: {Ek} A1: {A1} Ep: {Ep} A2: {A2} Epp: {Epp} Mp: {Mp} MK - MP: {Mk-Mp}") #<--- só pra verificar o funcionamento
                aux = Mk - Mp # <----- Essa auxiliar ajuda a verificar o padrão para a ser seguido ao mudar de auto/manual

            # Logica anti reset wind up
            if Mk > max_limite:
                Mk = float(max_limite)
            elif Mk < min_limite:
                Mk = float(min_limite)
        else:
            try:
                Mk_manual = float(input("Digite o valor da correcao manual: "))

                if primeira: # <----- Primeira vez que o código roda, inicia em 100 que é nosso 50%
                    Mp = Mk # para começar em 50% -> bias; Mk inicializado em 100
                    Mk = (A0 * Ek) + (A1 * Ep) + (A2 * Epp) + Mp
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
                    
                    elif acao == 1:#<-----bumpless acao direta
                        if Mk_manual > Mk_auto:# <----- Para não ocorrer o bump e ocorrer de forma linear. 
                            Mk = Mk_auto
                            while Mk_manual > Mk:
                                Mk = Mk - aux
                                print(f"Direta - Amostra {k}/ Erro constante: {E_cte} / Mk = {Mk} (MODO: {'MANUAL' if modo_manual else 'AUTOMATICO'})")
                        else :
                            Mk = Mk_auto
                            while Mk_manual < Mk:
                                Mk = (A0 * Ek) + (A1 * Ep) + (A2 * Epp) + Mp
                                Mp = Mk 
                                Epp = Ep 
                                Ep = Ek 
                                print(f"Direta - Amostra {k}/ Erro constante: {E_cte} / Mk = {Mk} (MODO: {'MANUAL' if modo_manual else 'AUTOMATICO'})")

                Mk = Mk_manual
                
            except ValueError:
                print("Entrada invalida. Usando o ultimo valor.")
                
        # Adiciona os valores nas listas (equivalente ao push_back)
        k_history.append(k)
        mk_history.append(Mk)

        print(f"Amostra {k}/ Erro constante: {E_cte} / Mk = {Mk} (MODO: {'MANUAL' if modo_manual else 'AUTOMATICO'})")
        
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
    print("k,Mk")
    for i in range(len(k_history)):
        print(f"{k_history[i]},{mk_history[i]:.2f}")

if __name__ == "__main__":
    main()