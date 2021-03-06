# coding: utf-8
# ###########################################################################
#
#    Author: Luis Felipe Mileo
#            Fernando Marcato Rodrigues
#            Daniel Sadamo Hirayama
#    Copyright 2015 KMEE - www.kmee.com.br
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from ..cnab import Cnab
from cnab240.tipos import Arquivo
from decimal import Decimal
from openerp.addons.l10n_br_base.tools.misc import punctuation_rm
import datetime
import re
import string
import unicodedata
import time


class Cnab240(Cnab):
    """

    """

    def __init__(self):
        super(Cnab, self).__init__()

    @staticmethod
    def get_bank(bank):
        if bank == '341':
            from .bancos.itau import Itau240
            return Itau240
        elif bank == '237':
            from .bancos.bradesco import Bradesco240
            return Bradesco240
        elif bank == '104':
            from .bancos.cef import Cef240
            return Cef240
        elif bank == '033':
            from .bancos.santander import Santander240
            return Santander240
        elif bank == '756':
            from .bancos.sicoob import Sicoob240
            return Sicoob240
        elif bank == '001':
            from .bancos.banco_brasil import BancoBrasil240
            return BancoBrasil240
        elif bank == '0851':
            from .bancos.cecred import Cecred240
            return Cecred240
        else:
            return Cnab240

    @property
    def inscricao_tipo(self):
        # TODO: Implementar codigo para PIS/PASEP
        if self.order.company_id.partner_id.is_company:
            return 2
        else:
            return 1

    def _prepare_header(self):
        """

        :param:
        :return:
        """
        return {
            'controle_banco': int(self.order.mode.bank_id.bank_bic),
            'arquivo_data_de_geracao': self.data_hoje(),
            'arquivo_hora_de_geracao': self.hora_agora(),
            # TODO: Número sequencial de arquivo
            'arquivo_sequencia': int(self.get_file_numeration()),
            'cedente_inscricao_tipo': self.inscricao_tipo,
            'cedente_inscricao_numero': int(punctuation_rm(
                self.order.company_id.cnpj_cpf)),
            'cedente_agencia': int(
                self.order.mode.bank_id.bra_number),
            'cedente_conta': int(self.order.mode.bank_id.acc_number),
            'cedente_conta_dv': (self.order.mode.bank_id.acc_number_dig),
            'cedente_agencia_dv': self.order.mode.bank_id.bra_number_dig,
            'cedente_nome': self.order.company_id.legal_name,
            # DV ag e conta
            'cedente_dv_ag_cc': (self.order.mode.bank_id.bra_acc_dig),
            'arquivo_codigo': 1,  # Remessa/Retorno
            'servico_operacao': u'R',
            'nome_banco': unicode(self.order.mode.bank_id.bank_name),
        }

    def get_file_numeration(self):
        numero = self.order.get_next_number()
        if not numero:
            numero = 1
        return numero

    def format_date(self, srt_date):
        return int(datetime.datetime.strptime(
            srt_date, '%Y-%m-%d').strftime('%d%m%Y'))

    def nosso_numero(self, format):
        pass

    def cep(self, format):
        sulfixo = format[-3:]
        prefixo = format[:5]
        return prefixo, sulfixo

    def sacado_inscricao_tipo(self, partner_id):
        # TODO: Implementar codigo para PIS/PASEP
        if partner_id.is_company:
            return 2
        else:
            return 1

    def rmchar(self, format):
        return re.sub('[%s]' % re.escape(string.punctuation), '',
                      format or '')

    def _prepare_segmento(self, line):
        """
        :param line:
        :return:
        """
        prefixo, sulfixo = self.cep(line.partner_id.zip)

        aceite = u'N'
        if not self.order.mode.boleto_aceite == 'S':
            aceite = u'A'

        # Código agencia do cedente
        # cedente_agencia = cedente_agencia

        # Dígito verificador da agência do cedente
        # cedente_agencia_conta_dv = cedente_agencia_dv

        # Código da conta corrente do cedente
        # cedente_conta = cedente_conta

        # Dígito verificador da conta corrente do cedente
        # cedente_conta_dv = cedente_conta_dv

        # Dígito verificador de agencia e conta
        # Era cedente_agencia_conta_dv agora é cedente_dv_ag_cc

        return {
            'controle_banco': int(self.order.mode.bank_id.bank_bic),
            'cedente_agencia': int(self.order.mode.bank_id.bra_number),
            'cedente_conta': int(self.order.mode.bank_id.acc_number),
            'cedente_conta_dv': self.order.mode.bank_id.acc_number_dig,
            'cedente_agencia_dv': self.order.mode.bank_id.bra_number_dig,
            'cedente_nome': self.order.company_id.legal_name,
            'cedente_conta': int(self.order.mode.bank_id.acc_number),
            # DV ag e cc
            'cedente_dv_ag_cc': (self.order.mode.bank_id.bra_acc_dig),
            'identificacao_titulo': u'0000000',  # TODO
            'identificacao_titulo_banco': u'0000000',  # TODO
            'identificacao_titulo_empresa': line.move_line_id.move_id.name,
            'numero_documento': line.name,
            'vencimento_titulo': self.format_date(
                line.ml_maturity_date),
            'valor_titulo': Decimal(str(line.amount_currency)).quantize(
                Decimal('1.00')),
            # TODO: Código adotado para identificar o título de cobrança.
            # 8 é Nota de cŕedito comercial
            'especie_titulo': int(self.order.mode.boleto_especie),
            'aceite_titulo': aceite,
            'data_emissao_titulo': self.format_date(
                line.ml_date_created),
            # Taxa de juros do Odoo padrão mensal: 2. Campo 27.3P
            # CEF/FEBRABAN e Itaú não tem.
            'codigo_juros': 2,
            'juros_mora_data': self.format_date(
                line.ml_maturity_date),
            'juros_mora_taxa':  Decimal(
                str(self.order.mode.late_payment_interest)).quantize(
                    Decimal('1.00')),
            # Multa padrão em percentual no Odoo, valor '2'
            'codigo_multa': '2',
            'data_multa': self.format_date(
                line.ml_maturity_date),
            'juros_multa':  Decimal(
                str(self.order.mode.late_payment_fee)).quantize(
                    Decimal('1.00')),
            # TODO Remover taxa dia - deixar apenas taxa normal
            'juros_mora_taxa_dia': Decimal('0.00'),
            'valor_abatimento': Decimal('0.00'),
            'sacado_inscricao_tipo': int(
                self.sacado_inscricao_tipo(line.partner_id)),
            'sacado_inscricao_numero': int(
                self.rmchar(line.partner_id.cnpj_cpf)),
            'sacado_nome': line.partner_id.legal_name,
            'sacado_endereco': (
                line.partner_id.street + ' ' + line.partner_id.number),
            'sacado_bairro': line.partner_id.district,
            'sacado_cep': int(prefixo),
            'sacado_cep_sufixo': int(sulfixo),
            'sacado_cidade': line.partner_id.l10n_br_city_id.name,
            'sacado_uf': line.partner_id.state_id.code,
            'codigo_protesto': int(self.order.mode.boleto_protesto),
            'prazo_protesto': int(self.order.mode.boleto_protesto_prazo),
            'codigo_baixa': 2,
            'prazo_baixa': 0,  # De 5 a 120 dias.
            'controlecob_data_gravacao': self.data_hoje(),
            'cobranca_carteira': int(self.order.mode.boleto_carteira[:2]),
        }

    def remessa(self, order):
        """

        :param order:
        :return:
        """
        cobrancasimples_valor_titulos = 0

        self.order = order
        header = self._prepare_header()
        self.arquivo = Arquivo(self.bank, **header)
        for line in order.line_ids:
            seg = self._prepare_segmento(line)
            self.arquivo.incluir_cobranca(header, **seg)
            self.arquivo.lotes[0].header.servico_servico = 1
            # TODO: tratar soma de tipos de cobranca
            cobrancasimples_valor_titulos += line.amount_currency
            self.arquivo.lotes[0].trailer.cobrancasimples_valor_titulos = \
                Decimal(cobrancasimples_valor_titulos).quantize(
                    Decimal('1.00'))

        remessa = unicode(self.arquivo)
        return unicodedata.normalize(
            'NFKD', remessa).encode('ascii', 'ignore')

    def data_hoje(self):
        return (int(time.strftime("%d%m%Y")))

    def hora_agora(self):
        return (int(time.strftime("%H%M%S")))
