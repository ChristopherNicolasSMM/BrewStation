from flask import Blueprint, jsonify, request
from flask_login import login_required
from model.brewfather import BrewFatherRecipe
from model.ingredientes import Malte, Lupulo, Levedura, CalculoPreco
from sqlalchemy import func, distinct
from db.database import db

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard/stats', methods=['GET'])
@login_required
def get_dashboard_stats():
    """Retorna estatísticas para o dashboard"""
    try:
        # Total de receitas
        total_receitas = BrewFatherRecipe.query.count()
        
        # Total de ingredientes (maltes + lúpulos + leveduras ativos)
        total_maltes = Malte.query.filter_by(ativo=True).count()
        total_lupulos = Lupulo.query.filter_by(ativo=True).count()
        total_leveduras = Levedura.query.filter_by(ativo=True).count()
        total_ingredientes = total_maltes + total_lupulos + total_leveduras
        
        # Média de preço por litro (apenas cálculos mais recentes por receita)
        subquery_stats = db.session.query(
            CalculoPreco.receita_id,
            func.max(CalculoPreco.data_calculo).label('max_data')
        ).group_by(CalculoPreco.receita_id).subquery()

        calculos_recentes_stats = db.session.query(CalculoPreco).join(
            subquery_stats,
            (CalculoPreco.receita_id == subquery_stats.c.receita_id) & 
            (CalculoPreco.data_calculo == subquery_stats.c.max_data)
        ).all()

        if calculos_recentes_stats:
            # Filtrar apenas cálculos com valor_litro_base válido
            precos_validos = [calc.valor_litro_base for calc in calculos_recentes_stats if calc.valor_litro_base and calc.valor_litro_base > 0]
            if precos_validos:
                media_preco_litro = sum(precos_validos) / len(precos_validos)
            else:
                media_preco_litro = 0
        else:
            media_preco_litro = 0
        
        # Cálculos deste mês
        from datetime import datetime, timedelta
        inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        calculos_mes = CalculoPreco.query.filter(CalculoPreco.data_calculo >= inicio_mes).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_receitas': total_receitas,
                'total_ingredientes': total_ingredientes,
                'media_preco_litro': round(media_preco_litro, 2),
                'calculos_mes': calculos_mes,
                'detalhes_ingredientes': {
                    'maltes': total_maltes,
                    'lupulos': total_lupulos,
                    'leveduras': total_leveduras
                }
            }
        })
        
    except Exception as e:
        print(f"Erro ao buscar estatísticas do dashboard: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/dashboard/calculos-recentes', methods=['GET'])
@login_required
def get_calculos_recentes():
    """Retorna os cálculos mais recentes por receita (distinct)"""
    try:
        filtro = request.args.get('filtro', 'hoje')  # Agora request está definido
        
        # Base query para cálculos mais recentes por receita
        subquery = db.session.query(
            CalculoPreco.receita_id,
            func.max(CalculoPreco.data_calculo).label('max_data')
        )
        
        # Aplicar filtro de data
        from datetime import datetime, timedelta
        
        if filtro == 'hoje':
            hoje = datetime.now().date()
            subquery = subquery.filter(func.date(CalculoPreco.data_calculo) == hoje)
        elif filtro == 'mes':
            inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            subquery = subquery.filter(CalculoPreco.data_calculo >= inicio_mes)
        elif filtro == 'ano':
            inicio_ano = datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            subquery = subquery.filter(CalculoPreco.data_calculo >= inicio_ano)
        # 'todos' não aplica filtro de data
        
        subquery = subquery.group_by(CalculoPreco.receita_id).subquery()
        
        # Query principal
        query = db.session.query(CalculoPreco).join(
            subquery,
            (CalculoPreco.receita_id == subquery.c.receita_id) & 
            (CalculoPreco.data_calculo == subquery.c.max_data)
        )
        
        # Ordenar pelos mais recentes
        calculos_recentes = query.order_by(CalculoPreco.data_calculo.desc()).limit(10).all()
        
        calculos_formatados = []
        for calculo in calculos_recentes:
            receita = BrewFatherRecipe.query.get(calculo.receita_id)
            nome_receita = receita.name if receita else calculo.nome_produto
            
            # Formatar data
            data_formatada = calculo.data_calculo.strftime('%d/%m/%Y %H:%M') if calculo.data_calculo else 'N/A'
            
            calculos_formatados.append({
                'id': calculo.id,
                'nome_produto': nome_receita,
                'quantidade_ml': calculo.quantidade_ml,
                'valor_venda_final': float(calculo.valor_venda_final),
                'valor_litro_base': float(calculo.valor_litro_base) if calculo.valor_litro_base else 0,
                'data_calculo': calculo.data_calculo.isoformat() if calculo.data_calculo else None,
                'data_formatada': data_formatada,
                'tipo_embalagem': calculo.tipo_embalagem
            })
        
        return jsonify({
            'success': True,
            'filtro': filtro,
            'calculos_recentes': calculos_formatados
        })
        
    except Exception as e:
        print(f"Erro ao buscar cálculos recentes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
    
    
@dashboard_bp.route('/dashboard/atividades-recentes', methods=['GET'])
@login_required
def get_atividades_recentes():
    """Retorna as atividades recentes do sistema"""
    try:
        from datetime import datetime, timedelta
        
        atividades = []
        
        # 1. Cálculos recentes (últimas 24 horas)
        um_dia_atras = datetime.now() - timedelta(days=1)
        calculos_recentes = CalculoPreco.query.filter(
            CalculoPreco.data_calculo >= um_dia_atras
        ).order_by(CalculoPreco.data_calculo.desc()).limit(3).all()
        
        for calculo in calculos_recentes:
            tempo = self.calcular_tempo_relativo(calculo.data_calculo)
            atividades.append({
                'tipo': 'calculo',
                'icone': 'bi-calculator',
                'cor': 'primary',
                'titulo': f'Cálculo: {calculo.nome_produto}',
                'descricao': f'R$ {calculo.valor_venda_final:.2f}',
                'tempo': tempo,
                'data': calculo.data_calculo.isoformat()
            })
        
        # 2. Receitas recentes
        receitas_recentes = BrewFatherRecipe.query.order_by(
            BrewFatherRecipe.data_criacao.desc()
        ).limit(2).all()
        
        for receita in receitas_recentes:
            tempo = self.calcular_tempo_relativo(receita.data_criacao)
            atividades.append({
                'tipo': 'receita',
                'icone': 'bi-journal-text',
                'cor': 'success',
                'titulo': f'Receita: {receita.name}',
                'descricao': f'{receita.style}' if receita.style else 'Nova receita',
                'tempo': tempo,
                'data': receita.data_criacao.isoformat() if receita.data_criacao else None
            })
        
        # Ordenar todas as atividades por data (mais recente primeiro)
        atividades.sort(key=lambda x: x['data'] if x['data'] else '', reverse=True)
        atividades = atividades[:5]  # Limitar para 5 atividades
        
        return jsonify({
            'success': True,
            'atividades': atividades
        })
        
    except Exception as e:
        print(f"Erro ao buscar atividades recentes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def calcular_tempo_relativo(self, data):
    """Calcula o tempo relativo (há x minutos/horas)"""
    from datetime import datetime
    if not data:
        return "Há algum tempo"
    
    agora = datetime.now()
    diferenca = agora - data
    
    minutos = diferenca.total_seconds() / 60
    horas = minutos / 60
    dias = horas / 24
    
    if minutos < 1:
        return "Agora mesmo"
    elif minutos < 60:
        return f"Há {int(minutos)} min"
    elif horas < 24:
        return f"Há {int(horas)}h"
    else:
        return f"Há {int(dias)}d"
def calcular_tempo_relativo(data):
    """Calcula o tempo relativo (há x minutos/horas)"""
    from datetime import datetime
    if not data:
        return "Há algum tempo"
    
    agora = datetime.now()
    diferenca = agora - data
    
    minutos = diferenca.total_seconds() / 60
    horas = minutos / 60
    dias = horas / 24
    
    if minutos < 1:
        return "Agora mesmo"
    elif minutos < 60:
        return f"Há {int(minutos)} min"
    elif horas < 24:
        return f"Há {int(horas)}h"
    else:
        return f"Há {int(dias)}d"    
    
    
@dashboard_bp.route('/dashboard/resumo-custos', methods=['GET'])
@login_required
def get_resumo_custos():
    """Retorna dados para o gráfico de resumo de custos"""
    try:
        from datetime import datetime, timedelta
        
        # Últimos 6 meses
        meses = []
        dados = []
        
        for i in range(5, -1, -1):
            mes_atual = datetime.now().replace(day=1) - timedelta(days=30*i)
            mes_nome = mes_atual.strftime('%b/%Y')
            meses.append(mes_nome)
            
            # Calcular custo médio do mês
            inicio_mes = mes_atual.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if i == 0:
                fim_mes = datetime.now()
            else:
                fim_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            calculos_mes = CalculoPreco.query.filter(
                CalculoPreco.data_calculo >= inicio_mes,
                CalculoPreco.data_calculo <= fim_mes
            ).all()
            
            if calculos_mes:
                custo_medio = sum(calc.valor_litro_base for calc in calculos_mes if calc.valor_litro_base) / len(calculos_mes)
                dados.append(round(custo_medio, 2))
            else:
                dados.append(0)
        
        # Distribuição de custos por tipo de ingrediente (exemplo)
        custo_maltes = Malte.query.filter_by(ativo=True).count() * 25  # Preço médio
        custo_lupulos = Lupulo.query.filter_by(ativo=True).count() * 400
        custo_leveduras = Levedura.query.filter_by(ativo=True).count() * 30
        
        distribuicao = {
            'Maltes': custo_maltes,
            'Lúpulos': custo_lupulos,
            'Leveduras': custo_leveduras
        }
        
        return jsonify({
            'success': True,
            'dados_grafico': {
                'meses': meses,
                'custos_medios': dados
            },
            'distribuicao': distribuicao
        })
        
    except Exception as e:
        print(f"Erro ao buscar resumo de custos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500    