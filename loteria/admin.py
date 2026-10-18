# No topo, adicione a nova função ao import:
from decimal import Decimal

# (Mantenha os outros imports que já estão lá)
from django.contrib import admin, messages
from django.utils.html import format_html

from .models import Bolao, Cota, JogoGerado, PerfilMembro
from .services import (calcular_orcamento_bolao, conferir_sorteio_caixa,
                       salvar_fechamento_no_banco)

# 1. Ação Personalizada
# Dentro do arquivo loteria/admin.py

# loteria/admin.py

@admin.action(description="Gerar Jogos de Fechamento (Automático)")
def gerar_jogos_bolao(modeladmin, request, queryset):
    for bolao in queryset:
        try:
            # 1. Trava Financeira
            financeiro = calcular_orcamento_bolao(bolao.id, preco_aposta=Decimal('5.00'))
            orcamento_jogos = financeiro['quantidade_jogos']
            
            if orcamento_jogos < 1:
                modeladmin.message_user(
                    request, 
                    f"Bolão '{bolao.nome}' ignorado: Sem saldo pago suficiente para gerar ao menos 1 jogo.", 
                    level=messages.WARNING
                )
                continue

            # 2. Trava de Dezenas Base
            if not bolao.dezenas_base:
                modeladmin.message_user(
                    request, 
                    f"Bolão '{bolao.nome}' ignorado: O campo 'Dezenas Base' está vazio. Preencha os números antes de gerar.", 
                    level=messages.WARNING
                )
                continue

            # --- 3. NOVA TRAVA DE SEGURANÇA (CONTRA DUPLICAÇÃO) ---
            # Verifica se a tabela JogoGerado já tem registros ligados a este bolão
            if bolao.jogos.exists():
                qtd_existente = bolao.jogos.count()
                modeladmin.message_user(
                    request, 
                    f"Bloqueio de Segurança: O bolão '{bolao.nome}' já possui {qtd_existente} jogos gerados. "
                    f"Se deseja recriar os bilhetes, vá na aba 'Jogos gerados', apague os antigos e tente novamente.", 
                    level=messages.ERROR
                )
                continue # Pula para o próximo bolão sem fazer nada
            # ------------------------------------------------------

            # 4. Conversão Inteligente: De String para Lista de Inteiros
            try:
                dezenas_escolhidas = [int(numero.strip()) for numero in bolao.dezenas_base.split(',')]
            except ValueError:
                modeladmin.message_user(
                    request, 
                    f"Bolão '{bolao.nome}' ignorado: Erro ao ler dezenas. Use apenas números e vírgulas (Ex: 4, 12, 17).", 
                    level=messages.ERROR
                )
                continue

            # 5. Geração dos jogos usando as dezenas vindas do banco
            qtd_gerada = salvar_fechamento_no_banco(bolao.id, dezenas_escolhidas, orcamento_jogos)
            
            msg_sucesso = (
                f"Bolão '{bolao.nome}': {qtd_gerada} jogos gerados com sucesso! | "
                f"Cotas Pagas: {financeiro['cotas_pagas']} | "
                f"Arrecadado: R$ {financeiro['total_arrecadado']} | "
                f"Troco em Caixa: R$ {financeiro['troco']}"
            )
            modeladmin.message_user(request, msg_sucesso, level=messages.SUCCESS)
            
        except Exception as e:
            modeladmin.message_user(request, f"Erro ao processar o bolão '{bolao.nome}': {str(e)}", level=messages.ERROR)
            
            
@admin.action(description="Conferir Resultados (Via API Caixa)")
def conferir_jogos_bolao(modeladmin, request, queryset):
    for bolao in queryset:
        try:
            resultado = conferir_sorteio_caixa(bolao.id)
            
            dezenas_str = ", ".join(resultado['sorteio'])
            
            # Monta a mensagem de sucesso com o placar do bolão
            msg = (
                f"Sorteio {resultado['concurso']} verificado! Dezenas: {dezenas_str}. | "
                f"Premiações do Grupo -> Senas: {resultado['relatorio']['sena']}, "
                f"Quinas: {resultado['relatorio']['quina']}, "
                f"Quadras: {resultado['relatorio']['quadra']}."
            )
            
            # Se ganhou algo, manda a mensagem em verde (sucesso), senão amarelo (aviso de que não rolou dessa vez)
            teve_premio = any(qtd > 0 for qtd in resultado['relatorio'].values())
            nivel_msg = messages.SUCCESS if teve_premio else messages.WARNING
            
            modeladmin.message_user(request, msg, level=nivel_msg)
            
        except Exception as e:
            modeladmin.message_user(request, f"Erro ao conferir bolão '{bolao.nome}': {str(e)}", level=messages.ERROR)
            
# 2. Registros dos Modelos
@admin.register(PerfilMembro)
class PerfilMembroAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'telefone', 'chave_pix')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'chave_pix')

# ATUALIZE o registro do BolaoAdmin para incluir as DUAS ações:
@admin.register(Bolao)
class BolaoAdmin(admin.ModelAdmin):
    # 1. Adicionamos a nova coluna 'saldo_caixa' aqui na lista de exibição
    list_display = ('nome', 'tipo', 'data_sorteio', 'valor_cota', 'saldo_caixa', 'encerrado')
    list_filter = ('tipo', 'encerrado')
    search_fields = ('nome',)
    actions = [gerar_jogos_bolao, conferir_jogos_bolao]

    # 2. Criamos a lógica visual da coluna
    @admin.display(description="Saldo em Caixa (Pago)")
    def saldo_caixa(self, obj):
        try:
            # Reutilizamos a inteligência financeira que já está pronta!
            financeiro = calcular_orcamento_bolao(obj.id, preco_aposta=Decimal('5.00'))
            saldo = financeiro['total_arrecadado']
            
            # Se tiver dinheiro em caixa, mostra uma tag verde chamativa
            if saldo > 0:
                return format_html(
                    '<span style="color: #155724; background-color: #d4edda; padding: 4px 8px; border-radius: 4px; font-weight: bold; border: 1px solid #c3e6cb;">💰 R$ {}</span>', 
                    saldo
                )
            
            # Se estiver zerado (ninguém pagou ainda), mostra uma tag cinza
            return format_html(
                '<span style="color: #6c757d; background-color: #e9ecef; padding: 4px 8px; border-radius: 4px; border: 1px solid #ced4da;">R$ 0,00</span>'
            )
            
        except Exception:
            return format_html('<span style="color: red;">Erro ao calcular</span>')
        
        
@admin.register(Cota)
class CotaAdmin(admin.ModelAdmin):
    list_display = ('membro', 'bolao', 'pago', 'data_pagamento')
    list_filter = ('pago', 'bolao')
    list_editable = ('pago',) 
    search_fields = ('membro__usuario__username', 'membro__usuario__first_name')

@admin.register(JogoGerado)
class JogoGeradoAdmin(admin.ModelAdmin):
    # Trocamos 'dezenas' e 'premiado' pelos nossos métodos customizados
    list_display = ('bolao', 'dezenas_formatadas', 'acertos_coloridos', 'premiado')
    list_filter = ('premiado', 'bolao')

    # Cria uma coluna customizada para as dezenas
    @admin.display(description="Dezenas do Bilhete")
    def dezenas_formatadas(self, obj):
        if obj.premiado:
            # Fundo verde claro, texto verde escuro e um troféu para os premiados
            return format_html(
                '<span style="background-color: #d4edda; color: #155724; padding: 4px 8px; border-radius: 5px; font-weight: bold; border: 1px solid #c3e6cb;">🏆 {}</span>',
                obj.dezenas
            )
        # Fundo cinza padrão para os não premiados ou ainda não conferidos
        return format_html(
            '<span style="background-color: #e9ecef; color: #495057; padding: 4px 8px; border-radius: 5px; border: 1px solid #ced4da;">{}</span>',
            obj.dezenas
        )

    # Destaca a coluna de quantidade de acertos também
    @admin.display(description="Acertos", ordering="acertos")
    def acertos_coloridos(self, obj):
        if obj.acertos >= 4: # Quadra, Quina ou Sena
            return format_html('<b style="color: green; font-size: 16px;">{}</b>', obj.acertos)
        elif obj.acertos > 0:
            return format_html('<span style="color: orange;">{}</span>', obj.acertos)
            
        # CORREÇÃO AQUI: Substituímos o 0 fixo pelas chaves {} e passamos a variável obj.acertos
        return format_html('<span style="color: gray;">{}</span>', obj.acertos)