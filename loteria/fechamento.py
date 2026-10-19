import itertools
import random

def aplicar_filtros_estatisticos(jogo):
    """
    Aplica modelos de probabilidade para eliminar outliers (jogos estatisticamente raros),
    otimizando o investimento financeiro do bolão.
    """
    # 1. Filtro de Par/Ímpar (Descarta extremos como 6 pares ou 6 ímpares)
    pares = sum(1 for n in jogo if n % 2 == 0)
    impares = 6 - pares
    if pares == 6 or impares == 6 or pares == 5 or impares == 5:
        return False

    # 2. Medida de Tendência Central: Soma das Dezenas
    # A curva Gaussiana dos sorteios reais da Mega-Sena concentra-se entre 120 e 240
    soma = sum(jogo)
    if soma < 120 or soma > 240:
        return False

    # 3. Dispersão de Sequências (Evitar anomalias como 1, 2, 3, 4)
    consecutivos = 1
    max_consecutivos = 1
    for i in range(1, 6):
        if jogo[i] == jogo[i-1] + 1:
            consecutivos += 1
            if consecutivos > max_consecutivos:
                max_consecutivos = consecutivos
        else:
            consecutivos = 1
    
    if max_consecutivos >= 4: # Descarta se tiver 4 ou mais números colados
        return False

    return True

def gerar_jogos_fechamento(dezenas_base, max_jogos, max_sobreposicao=3):
    """
    Gera jogos da Mega-Sena otimizados estatisticamente e matematicamente.
    """
    # 1. Sanitização
    dezenas_base = sorted(list(set(dezenas_base)))
    
    # Prevenção contra estouro de memória no servidor (limite seguro de ~25 dezenas)
    if len(dezenas_base) > 30:
        raise ValueError("O pool máximo permitido por segurança computacional é de 30 dezenas.")

    # 2. Desdobramento com mitigação de viés de amostragem
    todas_combinacoes = list(itertools.combinations(dezenas_base, 6))
    random.shuffle(todas_combinacoes) # Garante que dezenas altas e baixas tenham a mesma chance
    
    jogos_selecionados = []
    # Usamos uma lista auxiliar com os sets já pré-calculados para não castigar a CPU
    jogos_selecionados_sets = [] 

    for combinacao in todas_combinacoes:
        if len(jogos_selecionados) >= max_jogos:
            break
            
        # 3. Passa pela validação estatística primeiro (operação muito mais leve)
        if not aplicar_filtros_estatisticos(combinacao):
            continue
            
        # 4. Filtro de Dispersão Matemática (Sobreposição)
        combinacao_set = set(combinacao)
        pode_adicionar = True
        
        for jogo_salvo_set in jogos_selecionados_sets:
            # Avalia a interseção usando a memória pré-calculada
            if len(combinacao_set.intersection(jogo_salvo_set)) > max_sobreposicao:
                pode_adicionar = False
                break
        
        if pode_adicionar:
            jogos_selecionados.append(combinacao)
            jogos_selecionados_sets.append(combinacao_set)
            
    # Retorna os jogos ordenados internamente para ficar organizado no bilhete impresso
    return [sorted(list(jogo)) for jogo in jogos_selecionados]

# --- Testando a Nova Lógica ---
if __name__ == "__main__":
    # Pool de 15 dezenas (geraria 5.005 combinações brutas)
    pool_dezenas = [4, 8, 12, 17, 21, 23, 29, 31, 38, 42, 45, 49, 51, 53, 58]
    orcamento_jogos = 20
    
    meus_jogos = gerar_jogos_fechamento(pool_dezenas, orcamento_jogos, max_sobreposicao=3)
    
    print(f"Total de jogos gerados pós-filtros estatísticos: {len(meus_jogos)}\n")
    for i, jogo in enumerate(meus_jogos, 1):
        soma_jogo = sum(jogo)
        print(f"Jogo {i:02d}: {jogo} (Soma: {soma_jogo})")