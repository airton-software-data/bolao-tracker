# loteria/views.py
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import PerfilMembro # Certifique-se de importar o seu modelo de Perfil
import json
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import Bolao, Cota
# Exemplo de como usar no seu código:
from .services import gerar_pix_dinamico  # <-- Importe a função no topo
from .services import calcular_orcamento_bolao, salvar_fechamento_no_banco


# loteria/views.py

@login_required
def relatorio_bolao(request, bolao_id):
    """Gera uma página otimizada para impressão em A4/PDF do Bolão"""
    # Trava de segurança: Apenas o dono do sistema pode imprimir o relatório
    if not request.user.is_superuser:
        raise PermissionDenied("Apenas administradores podem gerar relatórios.")

    bolao = get_object_or_404(Bolao, id=bolao_id)
    cotas_pagas = bolao.cotas.filter(pago=True).select_related('membro__usuario')
    jogos = bolao.jogos.all().order_by('-premiado', '-acertos')
    
    # Calcula o total arrecadado no backend para facilitar a exibição
    total_arrecadado = len(cotas_pagas) * bolao.valor_cota

    contexto = {
        'bolao': bolao,
        'cotas_pagas': cotas_pagas,
        'jogos': jogos,
        'total_arrecadado': total_arrecadado,
    }
    
    return render(request, 'loteria/relatorio.html', contexto)

@login_required
def home(request):
    if request.user.is_superuser:
        # Administradores veem todos os bolões na lista
        boloes = Bolao.objects.all().order_by('-data_sorteio')
        
        # --- LÓGICA DO DASHBOARD ---
        # 1. Pega os bolões anotando a quantidade de cotas pagas em cada um
        boloes_com_cotas = Bolao.objects.annotate(
            qtd_pagas=Count('cotas', filter=Q(cotas__pago=True))
        ).order_by('data_sorteio') # Ordena do mais antigo para o mais novo
        
        # 2. Pega apenas os últimos 6 bolões para o gráfico não ficar esmagado
        ultimos_boloes = list(boloes_com_cotas)[-6:]
        
        # 3. Monta as listas de Rótulos (Nomes) e Valores (Dinheiro = qtd * valor da cota)
        labels = [b.nome for b in ultimos_boloes]
        valores = [float(b.qtd_pagas * b.valor_cota) for b in ultimos_boloes]
        
        contexto = {
            'boloes': boloes, 
            'eh_admin': True,
            'labels_json': json.dumps(labels),   # Converte para formato seguro de Javascript
            'valores_json': json.dumps(valores),
        }
        return render(request, 'loteria/home.html', contexto)
        
    else:
        # Visão do Usuário Comum
        minhas_cotas = Cota.objects.filter(membro__usuario=request.user).select_related('bolao').order_by('-bolao__data_sorteio')
        return render(request, 'loteria/home.html', {'minhas_cotas': minhas_cotas, 'eh_admin': False})


# Na sua função detalhe_bolao, altere este trecho:
@login_required
def detalhe_bolao(request, bolao_id):
    bolao = get_object_or_404(Bolao, id=bolao_id)
    
    cota_usuario = Cota.objects.filter(membro__usuario=request.user, bolao=bolao).first()
    
    pix_copia_cola = None
    qr_code_b64 = None
    
    # Se a cota existir e NÃO estiver paga, gera o PIX dinâmico
    if cota_usuario and not cota_usuario.pago:
        pix_copia_cola, qr_code_b64 = gerar_pix_dinamico(
            chave_pix="seu-email-ou-telefone", # Substitua pela sua chave
            nome="Airton P Lopes",             # Nome sem acentos
            cidade="SAO PAULO",                # Sem acentos
            valor=bolao.valor_cota,            # O valor puxa dinamicamente do bolão!
            txid=f"B{bolao.id}C{cota_usuario.id}" # Identificador único do pagamento
        )
        
    cotas_pagas = bolao.cotas.filter(pago=True).select_related('membro__usuario')
    jogos = bolao.jogos.all().order_by('-premiado', '-acertos')
    
    contexto = {
        'bolao': bolao,
        'cotas_pagas': cotas_pagas,
        'jogos': jogos,
        'cota_usuario': cota_usuario,
        'pix_copia_cola': pix_copia_cola, # <-- Adicione aqui
        'qr_code_b64': qr_code_b64,       # <-- Adicione aqui
    }
    
    return render(request, 'loteria/detalhe_bolao.html', contexto)




def gerar_jogos_automatizados(bolao_id, dezenas_escolhidas):
    # 1. O sistema descobre quanto dinheiro tem e quantos jogos pode fazer
    financeiro = calcular_orcamento_bolao(bolao_id, preco_aposta=Decimal('5.00'))
    orcamento_jogos = financeiro['quantidade_jogos']
    
    # Trava de segurança: impede rodar o algoritmo se não houver dinheiro para 1 jogo
    if orcamento_jogos < 1:
        raise ValueError("Não há cotas pagas suficientes para gerar ao menos um jogo.")
        
    # 2. Chama a função que já criamos para gerar e salvar no banco
    qtd_gerada = salvar_fechamento_no_banco(bolao_id, dezenas_escolhidas, orcamento_jogos)
    
    return qtd_gerada, financeiro

def view_gerar_jogos(request, bolao_id):
    bolao = get_object_or_404(Bolao, id=bolao_id)
    
    if request.method == 'POST':
        # Aqui você pegaria as dezenas e o orçamento que vieram do HTML/Formulário
        dezenas_escolhidas = [4, 12, 17, 23, 31, 38, 42, 45, 49, 53, 58, 60]
        orcamento = 15
        
        # Chama a função de serviço (Business Logic)
        quantidade_criada = salvar_fechamento_no_banco(bolao.id, dezenas_escolhidas, orcamento)
        
        messages.success(request, f"{quantidade_criada} jogos gerados com sucesso para o bolão {bolao.nome}!")
        return redirect('admin:loteria_bolao_change', bolao.id) # Redireciona de volta
        
    return render(request, 'loteria/gerar_jogos.html', {'bolao': bolao})

def minha_view(request, bolao_id):
    bolao = get_object_or_404(Bolao, id=bolao_id)
    cota_usuario = Cota.objects.filter(membro__usuario=request.user, bolao=bolao).first()
    # use cota_usuario
    
def cadastro(request):
    """Tela pública para novos usuários se registrarem"""
    # Se o usuário já estiver logado, manda pra home
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            # Cria automaticamente o perfil vazio para amarrar a chave PIX depois
            PerfilMembro.objects.get_or_create(usuario=usuario)
            # Loga o usuário automaticamente após criar a conta
            login(request, usuario)
            return redirect('home')
    else:
        form = UserCreationForm()
        
    return render(request, 'loteria/cadastro.html', {'form': form})

@login_required
def perfil(request):
    """Tela restrita para o usuário configurar sua Chave PIX"""
    # Busca o perfil do usuário logado (ou cria um se por algum motivo não existir)
    perfil_usuario, created = PerfilMembro.objects.get_or_create(usuario=request.user)
    
    if request.method == 'POST':
        nova_chave = request.POST.get('chave_pix', '')
        perfil_usuario.chave_pix = nova_chave
        perfil_usuario.save()
        # Envia uma mensagem de sucesso para a tela
        messages.success(request, "Chave PIX atualizada com sucesso!")
        return redirect('perfil')
        
    return render(request, 'loteria/perfil.html', {'perfil': perfil_usuario})


def erro_403(request, exception=None):
    # Opcional: Pegar a mensagem de erro que mandamos ("Você não comprou uma cota...")
    mensagem = str(exception) if exception else "Você não tem permissão para acessar esta página."
    
    return render(request, 'loteria/403.html', {'mensagem': mensagem}, status=403)