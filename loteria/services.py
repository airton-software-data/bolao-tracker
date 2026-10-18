import requests # <-- Adicione isso no topo do arquivo junto com os outros imports
# loteria/services.py
import itertools
from .models import Bolao, JogoGerado

from decimal import Decimal
from .models import Bolao
# loteria/services.py
import qrcode
import base64
from io import BytesIO

# --- Outras funções que já existem (calcular_orcamento_bolao, conferir_sorteio_caixa...) ---

def calcular_crc16_pix(payload):
    """Calcula o dígito verificador exigido pelo Banco Central"""
    crc = 0xFFFF
    for char in payload:
        crc ^= ord(char) << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return f"{crc:04X}"

def gerar_pix_dinamico(chave_pix, nome, cidade, valor, txid="BOLAO"):
    """Gera a string PIX Copia e Cola e a imagem do QR Code"""
    valor_str = f"{float(valor):.2f}"
    
    # Padrão EMV (BR Code)
    tam_chave = f"{len(chave_pix):02d}"
    tam_payload_26 = f"{len(chave_pix) + 22:02d}"
    tam_valor = f"{len(valor_str):02d}"
    tam_nome = f"{len(nome):02d}"
    tam_cidade = f"{len(cidade):02d}"
    tam_txid_62 = f"{len(txid) + 4:02d}"
    tam_txid = f"{len(txid):02d}"

    payload = (
        "000201"
        f"26{tam_payload_26}0014br.gov.bcb.pix01{tam_chave}{chave_pix}"
        "52040000"
        "5303986"
        f"54{tam_valor}{valor_str}"
        "5802BR"
        f"59{tam_nome}{nome}"
        f"60{tam_cidade}{cidade}"
        f"62{tam_txid_62}05{tam_txid}{txid}"
        "6304"
    )
    
    # 1. PIX Copia e Cola final
    pix_copia_cola = payload + calcular_crc16_pix(payload)
    
    # 2. Gera a imagem do QR Code sem precisar salvar arquivo no servidor (Base64)
    qr = qrcode.make(pix_copia_cola)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_code_b64 = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    return pix_copia_cola, qr_code_b64

def calcular_orcamento_bolao(bolao_id, preco_aposta=Decimal('5.00')):
    """
    Calcula o valor financeiro disponível baseado apenas nas cotas pagas
    e determina a quantidade máxima de jogos que podem ser gerados.
    
    :param preco_aposta: O custo de um jogo simples (R$ 5,00 para Mega-Sena).
    """
    bolao = Bolao.objects.get(id=bolao_id)
    
    # 1. Filtra as cotas vinculadas a este bolão que estão com status pago=True
    cotas_pagas = bolao.cotas.filter(pago=True)
    quantidade_pagas = cotas_pagas.count()
    
    # 2. Calcula o montante total (Ex: 10 cotas * R$ 20,00 = R$ 200,00)
    total_arrecadado = quantidade_pagas * bolao.valor_cota
    
    # 3. Calcula quantos jogos podemos pagar usando divisão inteira (//)
    # Ex: R$ 200,00 // R$ 5,00 = 40 jogos cravados.
    quantidade_jogos = int(total_arrecadado // preco_aposta)
    
    # 4. Calcula o troco que sobra no caixa (se houver)
    troco = total_arrecadado - (quantidade_jogos * preco_aposta)
    
    return {
        'total_arrecadado': total_arrecadado,
        'cotas_pagas': quantidade_pagas,
        'quantidade_jogos': quantidade_jogos,
        'troco': troco
    }

def gerar_jogos_fechamento(dezenas_base, max_jogos, max_sobreposicao=3):
    """
    Gera as combinações de jogos filtrando para evitar jogos parecidos.
    """
    dezenas_base = sorted(list(set(dezenas_base)))
    todas_combinacoes = list(itertools.combinations(dezenas_base, 6))
    
    jogos_selecionados = []
    
    for combinacao in todas_combinacoes:
        if len(jogos_selecionados) >= max_jogos:
            break
            
        pode_adicionar = True
        for jogo_salvo in jogos_selecionados:
            intersecao = len(set(combinacao).intersection(set(jogo_salvo)))
            if intersecao > max_sobreposicao:
                pode_adicionar = False
                break
                
        if pode_adicionar:
            jogos_selecionados.append(combinacao)
            
    return jogos_selecionados


def salvar_fechamento_no_banco(bolao_id, pool_dezenas, orcamento_jogos):
    """
    Função principal que orquestra a matemática e o banco de dados.
    """
    # 1. Gera os jogos na memória
    jogos_gerados_tuplas = gerar_jogos_fechamento(pool_dezenas, orcamento_jogos, max_sobreposicao=3)
    
    # 2. Salva os jogos no banco
    bolao = Bolao.objects.get(id=bolao_id)
    jogos_para_salvar = []
    
    for tupla_jogo in jogos_gerados_tuplas:
        dezenas_str = ",".join([f"{num:02d}" for num in tupla_jogo])
        jogos_para_salvar.append(
            JogoGerado(bolao=bolao, dezenas=dezenas_str)
        )
    
    # Salva todos de uma vez
    JogoGerado.objects.bulk_create(jogos_para_salvar)
    
    return len(jogos_para_salvar) # Retorna quantos jogos foram criados

# loteria/services.py

def conferir_sorteio_caixa(bolao_id):
    bolao = Bolao.objects.get(id=bolao_id)
    tipo_loteria = 'megasena' if bolao.tipo == 'MEGA' else 'quina'
    
    if bolao.concurso_alvo:
        url = f"https://api.guidi.dev.br/loteria/{tipo_loteria}/{bolao.concurso_alvo}"
    else:
        url = f"https://api.guidi.dev.br/loteria/{tipo_loteria}/ultimo"
        
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status() 
        dados = response.json()
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Erro ao conectar com a API da Loteria: {str(e)}")

    # --- CORREÇÃO AQUI: Busca por 'dezenas' ou 'listaDezenas' ---
    lista_sorteada = dados.get('dezenas') or dados.get('listaDezenas')
    
    # Trava de segurança: se a API mudou completamente de formato, avisa o desenvolvedor
    if not lista_sorteada:
         raise ValueError(f"A API não retornou os números no formato esperado. Dados recebidos: {dados}")

    # Usa a lista encontrada para montar o Set matemático
    sorteio_oficial = set(int(num) for num in lista_sorteada)
    
    # 3. Busca os bilhetes do nosso banco de dados
    jogos_do_bolao = bolao.jogos.all()
    jogos_para_atualizar = []
    
    relatorio = {'sena': 0, 'quina': 0, 'quadra': 0}
    
    # 4. Confere bilhete por bilhete
    for jogo in jogos_do_bolao:
        dezenas_jogo = set(int(num.strip()) for num in jogo.dezenas.split(','))
        acertos = len(sorteio_oficial.intersection(dezenas_jogo))
        jogo.acertos = acertos
        
        if bolao.tipo == 'MEGA' and acertos >= 4:
            jogo.premiado = True
            if acertos == 6: relatorio['sena'] += 1
            elif acertos == 5: relatorio['quina'] += 1
            elif acertos == 4: relatorio['quadra'] += 1
        else:
            jogo.premiado = False
            
        jogos_para_atualizar.append(jogo)
        
    # 5. Salva no banco de dados
    JogoGerado.objects.bulk_update(jogos_para_atualizar, ['acertos', 'premiado'])
    
    # --- CORREÇÃO AQUI TAMBÉM: Retorna a lista_sorteada correta ---
    return {
        'concurso': dados.get('concurso', dados.get('numero')), # Garante que acha o número do concurso
        'sorteio': lista_sorteada,
        'relatorio': relatorio
    }
    
    # 4. Confere bilhete por bilhete em milissegundos
    for jogo in jogos_do_bolao:
        # Pega a nossa string "05,12,33" e transforma em Set
        dezenas_jogo = set(int(num.strip()) for num in jogo.dezenas.split(','))
        
        # A MÁGICA: Interseção descobre quantos números iguais existem nos dois grupos
        acertos = len(sorteio_oficial.intersection(dezenas_jogo))
        jogo.acertos = acertos
        
        # Regra de premiação da Mega-Sena (4, 5 ou 6 acertos)
        if bolao.tipo == 'MEGA' and acertos >= 4:
            jogo.premiado = True
            if acertos == 6: relatorio['sena'] += 1
            elif acertos == 5: relatorio['quina'] += 1
            elif acertos == 4: relatorio['quadra'] += 1
        else:
            jogo.premiado = False
            
        jogos_para_atualizar.append(jogo)
        
    # 5. Salva todos os bilhetes atualizados de uma vez só (alta performance)
    JogoGerado.objects.bulk_update(jogos_para_atualizar, ['acertos', 'premiado'])
    
    return {
        'concurso': dados['concurso'],
        'sorteio': dados['dezenas'],
        'relatorio': relatorio
    }