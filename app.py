import asyncio
import json
from websockets.server import serve

async def simulator_handler(websocket):
    """
    Gerencia a conexão WebSocket e a simulação PID.
    Recebe os parâmetros do cliente, executa a simulação passo a passo
    e envia os dados de volta em tempo real.
    """
    try:
        # Recebe os dados iniciais do cliente
        initial_message = await websocket.recv()
        state = json.loads(initial_message)
        print(f"Parâmetros iniciais recebidos: {state}")

        # Task para ouvir mensagens do cliente em tempo real
        async def listen_for_updates():
            async for message in websocket:
                try:
                    update_data = json.loads(message)
                    state.update(update_data)
                    print(f"Parâmetros atualizados em tempo real: {update_data}")
                except json.JSONDecodeError:
                    print(f"Mensagem inválida recebida: {message}")

        # Inicia a tarefa de escuta em segundo plano
        listener_task = asyncio.create_task(listen_for_updates())

        # Inicialização das variáveis para o cálculo PID incremental
        Mk = 0.0
        Mp = 0.0
        Ek = 0.0
        Ep = 0.0
        Epp = 0.0
        modo_anterior_manual = False
        
        print("Simulação iniciada...")
        
        # Loop de simulação passo a passo
        for amostra in range(state.get("quantidade_amostras")):
            if state.get("modo").upper() == "MANUAL":
                # No modo manual, a saída é o valor da correção manual
                Mk = state.get("correcao_manual")
                modo_anterior_manual = True
                
            elif state.get("modo").upper() == "AUTO":
                # Se o modo mudou de manual para automático, a saída anterior é a correção manual
                if modo_anterior_manual:
                    Mp = state.get("correcao_manual")
                    modo_anterior_manual = False
                
                # Atualiza os erros com base no erro constante
                Epp = Ep
                Ep = Ek
                Ek = state.get("erro_constante")

                # CÁLCULO DA CORREÇÃO ATUAL
                kp = state.get("kp", 0.0)
                ki = state.get("ki", 0.0)
                kd = state.get("kd", 0.0)
                tempo_amostragem = state.get("tempo_amostragem", 1.0)
                
                # Recalcula as constantes do controlador PID incremental
                A0 = kp * (1.0 + (tempo_amostragem / ki if ki != 0 else 0) + (kd / tempo_amostragem if tempo_amostragem != 0 else 0))
                A1 = -kp * (1.0 + 2.0 * (kd / tempo_amostragem if tempo_amostragem != 0 else 0))
                A2 = kp * (kd / tempo_amostragem if tempo_amostragem != 0 else 0)

                Mk = (A0 * Ek) + (A1 * Ep) + (A2 * Epp) + Mp
                
                # Lógica anti-reset windup
                if Mk > state.get("maximo_saida"):
                    Mk = float(state.get("maximo_saida"))
                elif Mk < state.get("minimo_saida"):
                    Mk = float(state.get("minimo_saida"))

            # Envia o ponto de dados atual para o cliente
            data = {"k": amostra, "mk": Mk}
            await websocket.send(json.dumps(data))

            # Atualiza as variáveis para a próxima amostra
            Mp = Mk
            
            # Pausa para simular o tempo de amostragem
            await asyncio.sleep(state.get("tempo_amostragem"))

    except Exception as e:
        print(f"Erro na simulação ou na conexão: {e}")
    finally:
        listener_task.cancel()
        print("Conexão fechada.")

async def main():
    """
    Função principal para iniciar o servidor WebSocket.
    """
    async with serve(simulator_handler, "localhost", 8765):
        print("Servidor WebSocket iniciado em ws://localhost:8765")
        await asyncio.Future()  # Executa para sempre

if __name__ == "__main__":
    asyncio.run(main())