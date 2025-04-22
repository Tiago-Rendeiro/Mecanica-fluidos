# Operação Otimizada de Bombagem em Sistemas de Distribuição de Água

## Visão Geral do Projeto
Este projeto Python implementa um sistema de modulação e otimização para operação de bombas em redes de abastecimento de água. O sistema minimiza custos energéticos respeitando restrições hidráulicas e padrões de consumo variáveis.
## 📌 Objetivos

- Minimizar o custo total de operação da bomba ao longo de 24 horas.
- Assegurar níveis seguros no depósito (entre 0 m e 9 m), com nível inicial e final de 4 m.
- Penalizar operações que excedam os limites de segurança (abaixo de 2 m ou acima de 7 m), com um custo de 5 €/hora por hora violada.

## ⚙️ Descrição Técnica

- A simulação considera diferentes curvas de consumo (mínimo/máximo e residencial).
- O funcionamento da bomba é otimizado em ciclos (número definido pelo utilizador).
- A vazão é ajustada dinamicamente com base no nível do depósito.
- Tarifas de energia variam ao longo do dia (definidas em intervalos de 2h).
- A otimização é feita com `differential_evolution` da `scipy.optimize`.

## 📁 Estrutura do Projeto

- `OtimizadorBomba`: classe principal que realiza a simulação e otimização.
- `simular`: simula o comportamento da bomba com base nos parâmetros dados.
- `func_objetivo`: função de custo a minimizar (inclui penalizações).
- `main`: executa otimizações para diferentes modos de consumo.

### Requisitos
- Python 3.11 ou superior
  ```bash
  ## Pré-requisitos e Configuração

### 📦 Bibliotecas Necessárias
Instale as seguintes bibliotecas Python usando o código:

pip install numpy scipy matplotlib

###🚀 Como correr
Executa o script principal:

python after24V2.py

##📊 Resultados
O script gera gráficos com:

-Estado da bomba (ligada/desligada)

-Nível de água no depósito

-Potência consumida

-Custo acumulado


 
  
