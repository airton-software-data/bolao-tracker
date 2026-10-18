from django.db import models
from django.contrib.auth.models import User

class PerfilMembro(models.Model):
    # Conecta o perfil ao sistema de login nativo do Django
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    chave_pix = models.CharField(max_length=100, blank=True, null=True, help_text="Para receber a divisão do prêmio")
    telefone = models.CharField(max_length=20, blank=True, null=True)
    # ---  ESTA LINHA CHAVE PIX PARA RECEBER O PREMIO ---
    chave_pix = models.CharField(max_length=150, blank=True, null=True, help_text="Chave PIX para recebimento de prêmios")

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.username

    class Meta:
        verbose_name = "Perfil de Participante"
        verbose_name_plural = "Perfis de Participantes"
# Dentro do arquivo loteria/models.py, atualize a classe Bolao:

class Bolao(models.Model):
    TIPO_CHOICES = [
        ('MEGA', 'Mega-Sena'),
        ('QUINA', 'Quina'),
    ]
    nome = models.CharField(max_length=100, help_text="Ex: Bolão da Virada 2026")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    
    # --- NOVO CAMPO ADICIONADO AQUI ---
    dezenas_base = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text="Digite as dezenas escolhidas separadas por vírgula. Ex: 4, 12, 17, 23, 31, 38, 42, 45, 49, 53, 58, 60"
    )
    # ----------------------------------

    data_sorteio = models.DateField()
    concurso_alvo = models.CharField(max_length=10, blank=True, null=True)
    valor_cota = models.DecimalField(max_digits=10, decimal_places=2)
    encerrado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nome} - {self.tipo}"
    
    class Meta:
        verbose_name = "Bolão"
        verbose_name_plural = "Bolões"
    
class Cota(models.Model):
    # Aqui controlamos quem pagou e quem está fora do rateio
    bolao = models.ForeignKey(Bolao, on_delete=models.CASCADE, related_name='cotas')
    membro = models.ForeignKey(PerfilMembro, on_delete=models.CASCADE)
    pago = models.BooleanField(default=False)
    data_pagamento = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        status = "PAGO" if self.pago else "PENDENTE"
        return f"{self.membro.usuario.username} - {self.bolao.nome} ({status})"

class JogoGerado(models.Model):
    bolao = models.ForeignKey(Bolao, on_delete=models.CASCADE, related_name='jogos')
    dezenas = models.CharField(max_length=100) 
    acertos = models.IntegerField(default=0)
    premiado = models.BooleanField(default=False)

    def __str__(self):
        return f"Jogo {self.id} - {self.dezenas}"
    
    class Meta:
        verbose_name = "Bilhete Gerado"
        verbose_name_plural = "Bilhetes Gerados"

    # --- ADICIONE ESTAS 3 LINHAS NO FINAL DA CLASSE ---
    @property
    def dezenas_lista(self):
        # Transforma a string "04,12,17" em uma lista real ['04', '12', '17']
        return self.dezenas.split(',')

    def __str__(self):
        return f"Jogo {self.id} - {self.dezenas}"
