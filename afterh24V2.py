import numpy as np
from scipy.optimize import minimize, Bounds, fsolve, differential_evolution
import matplotlib.pyplot as plt
from warnings import simplefilter
simplefilter("ignore", RuntimeWarning)

CONFIG = {
    'DEPÓSITO': {
        'nível_mín': 0.0,  # Alterado de 2.0 para 0.0
        'nível_máx': 9.0,  # Alterado de 7.0 para 9.0
        'nível_inicial': 4.0,
        'area': 185.0
    },
    'BOMBA': {
        'eficiência': 0.65,
        'altura_máx': 260,
        'curva_a': 0.002
    },
    'TUBULAÇÕES': {
        'diâmetro': 0.3,
        'atrito': 0.02,
        'comprimento': 5000
    },
    'TEMPO': {
        'horizonte': 24,
        'passo': 0.25
    }
}

TARIFAS = [
    (0, 0.0713), (2, 0.0651), (4, 0.0593), (6, 0.0778),
    (8, 0.0851), (10, 0.0923), (12, 0.0968), (14, 0.10094),
    (16, 0.10132), (18, 0.10230), (20, 0.10189), (22, 0.10132), (24, 0.0713)
]

def calcular_vazao(nivel_deposito):
    def eq(Q):
        perda = (32 * CONFIG['TUBULAÇÕES']['atrito'] * CONFIG['TUBULAÇÕES']['comprimento'] * (Q/3600)**2) / \
                (CONFIG['TUBULAÇÕES']['diâmetro']**5 * 9.81 * np.pi**2)
        H = CONFIG['BOMBA']['altura_máx'] - CONFIG['BOMBA']['curva_a'] * Q**2
        return H - (nivel_deposito + perda)
    try:
        Q = fsolve(eq, 150)[0]
        return max(0, Q)
    except:
        return 0

def demanda_vc_max(t):
    return (-1.19333e-7*t**7 - 4.90754e-5*t**6 + 3.733e-3*t**5 - 0.09621*t**4 + 1.03965*t**3 - 3.8645*t**2 - 1.0124*t + 75.393)

def demanda_vc_min(t):
    return (1.19333e-7*t**7 - 6.54846e-5*t**6 + 4.1432e-3*t**5 - 0.100585*t**4 + 1.05577*t**3 - 3.85966*t**2 - 1.32657*t + 75.393)

def demanda_residencial(t):
    return -0.004*t**3 + 0.09*t**2 + 0.1335*t + 20

class OtimizadorBomba:
    def __init__(self, modo='max', n_ciclos=3):
        self.modo = modo
        self.n_ciclos = n_ciclos
        self.tempo = np.arange(0, CONFIG['TEMPO']['horizonte'], CONFIG['TEMPO']['passo'])

    def simular(self, horarios, duracoes, mostrar_penalizacao=False):
        try:
            bomba = np.zeros_like(self.tempo)
            for h, d in zip(horarios, duracoes):
                bomba += ((self.tempo >= h) & (self.tempo < h + d)).astype(float)

            nivel = np.zeros_like(self.tempo)
            potencia = np.zeros_like(self.tempo)
            custo = np.zeros_like(self.tempo)
            nivel[0] = CONFIG['DEPÓSITO']['nível_inicial']

            horas_violadas = set()

            for i in range(1, len(self.tempo)):
                t = self.tempo[i]
                demanda_total = (demanda_vc_max(t) if self.modo == 'max' else demanda_vc_min(t)) + demanda_residencial(t)

                if bomba[i] > 0.5:
                    Q = calcular_vazao(nivel[i - 1])
                    fornecido = min(Q, demanda_residencial(t))
                    direto = fornecido
                    para_tanque = Q - direto

                    H = CONFIG['BOMBA']['altura_máx'] - CONFIG['BOMBA']['curva_a'] * Q ** 2
                    potencia[i] = (1000 * 9.81 * (Q / 3600) * H) / (1000 * CONFIG['BOMBA']['eficiência'])
                else:
                    Q = 0
                    direto = 0
                    para_tanque = 0
                    potencia[i] = 0

                retirada = demanda_total - direto
                nivel[i] = nivel[i - 1] + (para_tanque - retirada) * CONFIG['TEMPO']['passo'] / CONFIG['DEPÓSITO']['area']

                if nivel[i] < 2 or nivel[i] > 7:
                    horas_violadas.add(int(t))  # Hora inteira

                custo[i] = custo[i - 1] + potencia[i] * np.interp(t % 24, *zip(*TARIFAS)) * CONFIG['TEMPO']['passo']

            # Penalização acumulativa em blocos consecutivos
            horas_ordenadas = sorted(horas_violadas)
            penalizacao_base = 5
            penalidade_total = 0
            bloco = []

            for h in horas_ordenadas:
                if not bloco or h == bloco[-1] + 1:
                    bloco.append(h)
                else:
                    penalidade_total += sum(penalizacao_base * (i + 1) for i in range(len(bloco)))
                    bloco = [h]
            if bloco:
                penalidade_total += sum(penalizacao_base * (i + 1) for i in range(len(bloco)))

            if mostrar_penalizacao and penalidade_total > 0:
                print(f"⚠ Penalização acumulada: €{penalidade_total:.2f} (Horas violadas: {horas_ordenadas})")

            custo += penalidade_total

            return {
                'tempo': self.tempo,
                'nivel': nivel,
                'potencia': potencia,
                'custo': custo,
                'bomba': bomba,
                'modo': self.modo
            }

        except Exception as e:
            print(f"Erro na simulação: {e}")
            return None

    def func_objetivo(self, x):
        sim = self.simular(x[:self.n_ciclos], x[self.n_ciclos:])
        if sim is None:
            return float('inf')
        custo_total = sim['custo'][-1]

        nivel_min = np.min(sim['nivel'])
        nivel_max = np.max(sim['nivel'])

        if nivel_min < CONFIG['DEPÓSITO']['nível_mín']:
            custo_total += 1000 * (CONFIG['DEPÓSITO']['nível_mín'] - nivel_min)**2
        if nivel_max > CONFIG['DEPÓSITO']['nível_máx']:
            custo_total += 1000 * (nivel_max - CONFIG['DEPÓSITO']['nível_máx'])**2

        diferenca_nivel = sim['nivel'][-1] - sim['nivel'][0]
        custo_total += 1000 * (diferenca_nivel)**2
        return custo_total

    def otimizar(self):
        passo = CONFIG['TEMPO']['passo']
        bounds = Bounds(
            [0]*self.n_ciclos + [0.5]*self.n_ciclos,
            [24-passo]*self.n_ciclos + [8]*self.n_ciclos
        )

        try:
            resultado = differential_evolution(
                self.func_objetivo,
                bounds=list(zip(bounds.lb, bounds.ub)),
                maxiter=300,
                popsize=25,
                tol=0.01,
                polish=True
            )
            if resultado.success:
                solucao = self.simular(resultado.x[:self.n_ciclos], resultado.x[self.n_ciclos:], mostrar_penalizacao=True)
                if solucao is not None:
                    return solucao
        except Exception as e:
            print(f"Erro na otimização: {e}")
        return None


def plotar_resultados(resultados):
    if resultados is None:
        print("❌ Nenhum resultado válido para mostrar.")
        return

    fig, axs = plt.subplots(4, 1, figsize=(12, 10), sharex=True)

    axs[0].step(resultados['tempo'], resultados['bomba'], where='post', color='blue')
    axs[0].set_ylabel('Estado Bomba')
    axs[0].grid(True)

    axs[1].plot(resultados['tempo'], resultados['nivel'], color='green')
    axs[1].axhline(2.0, color='r', linestyle='--')
    axs[1].axhline(7.0, color='r', linestyle='--')
    axs[1].set_ylabel('Nível (m)')
    axs[1].grid(True)

    axs[2].plot(resultados['tempo'], resultados['potencia'], color='orange')
    axs[2].set_ylabel('Potência (kW)')
    axs[2].grid(True)

    axs[3].plot(resultados['tempo'], resultados['custo'], color='purple')
    axs[3].set_ylabel('Custo (€)')
    axs[3].set_xlabel('Tempo (h)')
    axs[3].grid(True)

    plt.suptitle(f"Resultados - Cenário {resultados['modo'].upper()}")
    plt.tight_layout()
    plt.show()


def main():
    for modo in ['max', 'min']:
        print(f"\n=== OTIMIZAÇÃO - Cenário {modo.upper()} ===")
        for ciclos in [2, 3]:
            print(f"\n>> Tentando com {ciclos} ciclos...")
            otimizador = OtimizadorBomba(modo=modo, n_ciclos=ciclos)
            resultado = otimizador.otimizar()
            if resultado:
                print(f"✔ Solução encontrada com custo €{resultado['custo'][-1]:.2f}")
                plotar_resultados(resultado)
            else:
                print("❌ Nenhuma solução válida encontrada.")


if __name__ == "__main__":
    main()
