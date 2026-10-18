import itertools

def gerar_jogos_fechamento(dezenas_base, max_jogos, max_sobreposicao=3):
    """
    Gera jogos da Mega-Sena a partir de um pool de dezenas, 
    eliminando jogos muito parecidos para otimizar o custo.
    
    :param dezenas_base: list[int] - O pool de números escolhidos pelo grupo (ex: 12 números).
    :param max_jogos: int - O limite de jogos que o caixa do bolão permite pagar.
    :param max_sobreposicao: int - Quantos números repetidos toleramos entre dois bilhetes.
    """
    # 1. Garante que as dezenas estejam limpas e ordenadas
    dezenas_base = sorted(list(set(dezenas_base)))
    
    # 2. Gera a matriz completa de combinações (Desdobramento Total)
    # Se passarmos 12 dezenas, isso gera 924 combinações de 6.
    todas_combinacoes = list(itertools.combinations(dezenas_base, 6))
    
    jogos_selecionados = []
    
    for combinacao in todas_combinacoes:
        # Se o algoritmo já encontrou a quantidade de jogos que o bolão pode pagar, encerra.
        if len(jogos_selecionados) >= max_jogos:
            break
            
        # 3. Filtro de Dispersão Matemática
        pode_adicionar = True
        
        for jogo_salvo in jogos_selecionados:
            # Transformamos as tuplas em Sets (conjuntos) para usar a interseção
            # Isso é computacionalmente muito rápido no Python
            intersecao = len(set(combinacao).intersection(set(jogo_salvo)))
            
            # Se a interseção for maior que nosso limite (ex: 4 ou mais números iguais),
            # descartamos a combinação. Não vale a pena gastar R$ 5,00 em um bilhete quase idêntico.
            if intersecao > max_sobreposicao:
                pode_adicionar = False
                break # Interrompe a checagem desse jogo, pois já falhou na regra
        
        # Se passou por todos os jogos já salvos e não engatilhou a sobreposição, é um bom jogo.
        if pode_adicionar:
            jogos_selecionados.append(combinacao)
            
    return jogos_selecionados

# --- Testando a Lógica ---
if __name__ == "__main__":
    # Exemplo: O grupo escolheu 12 dezenas preferidas
    pool_dezenas = [4, 12, 17, 23, 31, 38, 42, 45, 49, 53, 58, 60]
    
    # O bolão arrecadou dinheiro suficiente para apenas 15 jogos
    orcamento_jogos = 15
    
    meus_jogos = gerar_jogos_fechamento(pool_dezenas, orcamento_jogos, max_sobreposicao=3)
    
    print(f"Total de jogos gerados de forma otimizada: {len(meus_jogos)}")
    for i, jogo in enumerate(meus_jogos, 1):
        print(f"Jogo {i:02d}: {jogo}")