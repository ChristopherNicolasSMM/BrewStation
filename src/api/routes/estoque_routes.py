from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from model.estoque import MovimentacaoEstoque, EstoqueIngrediente, CustoProducao
from model.ingredientes import Malte, Lupulo, Levedura  # Corrigido os imports
from model.brewfather import BrewFatherBatch
from model.envase import Embalagem, Envase
from db.database import db
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import logging

logger = logging.getLogger(__name__)

estoque_bp = Blueprint('estoque', __name__)

def to_decimal(value, default='0'):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)

# ===== MOVIMENTAÇÕES DE ESTOQUE =====
@estoque_bp.route('/estoque/movimentacoes')
@login_required
def get_movimentacoes():
    """Lista todas as movimentações de estoque"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        ingrediente_id = request.args.get('ingrediente_id')
        tipo_ingrediente = request.args.get('tipo_ingrediente')  # malte, lupulo, levedura
        
        query = MovimentacaoEstoque.query
        
        if ingrediente_id and tipo_ingrediente:
            query = query.filter_by(ingrediente_id=ingrediente_id)
            
        movimentacoes = query.order_by(MovimentacaoEstoque.data_movimentacao.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'movimentacoes': [mov.to_dict() for mov in movimentacoes.items],
            'total': movimentacoes.total,
            'pages': movimentacoes.pages,
            'current_page': page
        })
    except Exception as e:
        logger.error(f"Erro ao buscar movimentações: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@estoque_bp.route('/estoque/movimentacoes', methods=['POST'])
@login_required
def criar_movimentacao():
    """Cria uma nova movimentação de estoque"""
    try:
        data = request.get_json()

        quantidade = to_decimal(data.get('quantidade', 0))
        custo_unitario = data.get('custo_unitario')
        custo_unitario_decimal = to_decimal(custo_unitario, '0') if custo_unitario not in (None, '') else None
        
        movimentacao = MovimentacaoEstoque(
            ingrediente_id=data['ingrediente_id'],
            tipo_ingrediente=data['tipo_ingrediente'],  # Adicionado
            tipo_movimentacao=data['tipo_movimentacao'],
            quantidade=quantidade,
            unidade_medida=data['unidade_medida'],
            custo_unitario=custo_unitario_decimal,
            lote_fornecedor=data.get('lote_fornecedor'),
            data_validade=datetime.fromisoformat(data['data_validade']) if data.get('data_validade') else None,
            observacoes=data.get('observacoes'),
            usuario_id=current_user.id
        )
        
        # Calcular custo total
        movimentacao.calcular_custo_total()
        
        db.session.add(movimentacao)
        
        # Atualizar estoque do ingrediente
        estoque = EstoqueIngrediente.query.filter_by(
            ingrediente_id=data['ingrediente_id'],
            tipo_ingrediente=data['tipo_ingrediente']
        ).first()
        
        if not estoque:
            estoque = EstoqueIngrediente(
                ingrediente_id=data['ingrediente_id'],
                tipo_ingrediente=data['tipo_ingrediente'],
                unidade_medida=data['unidade_medida'],
                estoque_minimo=0  # Valor padrão
            )
            db.session.add(estoque)
        
        estoque.atualizar_estoque(movimentacao)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'movimentacao': movimentacao.to_dict(),
            'estoque_atualizado': estoque.to_dict(),
            'message': 'Movimentação registrada com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar movimentação: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@estoque_bp.route('/estoque/atual')
@login_required
def get_estoque_atual():
    """Retorna o estoque atual de todos os ingredientes"""
    try:
        filtro_tipo = request.args.get('tipo')
        filtro_status = request.args.get('status')
        filtro_nome = request.args.get('nome', '').strip().lower()
        
        query = EstoqueIngrediente.query
        
        if filtro_tipo:
            query = query.filter(EstoqueIngrediente.tipo_ingrediente == filtro_tipo)
            
        if filtro_status:
            if filtro_status == 'critico':
                query = query.filter(EstoqueIngrediente.quantidade_atual <= EstoqueIngrediente.estoque_minimo)
            elif filtro_status == 'baixo':
                query = query.filter(
                    EstoqueIngrediente.quantidade_atual > EstoqueIngrediente.estoque_minimo,
                    EstoqueIngrediente.quantidade_atual <= (EstoqueIngrediente.estoque_minimo * 1.5)
                )
            elif filtro_status == 'ok':
                query = query.filter(EstoqueIngrediente.quantidade_atual > (EstoqueIngrediente.estoque_minimo * 1.5))
            elif filtro_status == 'esgotado':
                query = query.filter(EstoqueIngrediente.quantidade_atual <= 0)
        
        estoque = query.order_by(EstoqueIngrediente.tipo_ingrediente, EstoqueIngrediente.ingrediente_id).all()
        
        estoque_completo = []
        for item in estoque:
            item_dict = item.to_dict()
            if filtro_nome:
                nome = (item_dict.get('ingrediente_nome') or '').lower()
                if filtro_nome not in nome:
                    continue
            estoque_completo.append(item_dict)
        
        return jsonify({
            'success': True,
            'estoque': estoque_completo,
            'total_itens': len(estoque_completo),
            'valor_total_estoque': sum(float(item.get('valor_total_estoque', 0)) for item in estoque_completo)
        })
    except Exception as e:
        logger.error(f"Erro ao buscar estoque atual: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def buscar_ingrediente_por_id(ingrediente_id):
    """Busca informações do ingrediente pelo ID em todas as tabelas"""
    try:
        # Tentar encontrar em Maltes
        malte = Malte.query.get(ingrediente_id)
        if malte:
            return {
                'ingrediente_nome': malte.nome,
                'ingrediente_tipo': 'malte',
                'fabricante': malte.fabricante,
                'tipo': malte.tipo
            }
        
        # Tentar encontrar em Lúpulos
        lupulo = Lupulo.query.get(ingrediente_id)
        if lupulo:
            return {
                'ingrediente_nome': lupulo.nome,
                'ingrediente_tipo': 'lupulo',
                'fabricante': lupulo.fabricante,
                'formato': lupulo.formato
            }
        
        # Tentar encontrar em Leveduras
        levedura = Levedura.query.get(ingrediente_id)
        if levedura:
            return {
                'ingrediente_nome': levedura.nome,
                'ingrediente_tipo': 'levedura',
                'fabricante': levedura.fabricante,
                'formato': levedura.formato
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Erro ao buscar ingrediente {ingrediente_id}: {e}")
        return None

# ===== CUSTOS DE PRODUÇÃO =====
@estoque_bp.route('/estoque/calcular-custo/<int:lote_id>')
@login_required
def calcular_custo_producao(lote_id):
    """Calcula o custo de produção para um lote específico"""
    try:
        lote = BrewFatherBatch.query.get_or_404(lote_id)
        
        # Buscar custo existente ou criar novo
        custo = CustoProducao.query.filter_by(lote_id=lote_id).first()
        if not custo:
            custo = CustoProducao(lote_id=lote_id)
        
        # Calcular custo de ingredientes (simplificado)
        # Aqui você implementaria a lógica específica baseada na receita
        custo_ingredientes = 0
        
        # Calcular custo de embalagens baseado nos envases
        envases = Envase.query.filter_by(lote_id=lote_id).all()
        custo_embalagens = 0
        for envase in envases:
            for item in envase.itens_envase:
                if item.embalagem and item.embalagem.valor_unidade:
                    custo_embalagens += float(item.embalagem.valor_unidade) * item.quantidade
        
        custo.custo_ingredientes = custo_ingredientes
        custo.custo_embalagens = custo_embalagens
        custo.quantidade_produzida = lote.batch_size
        custo.margem_lucro = 100  # 100% de margem como padrão
        
        custo.calcular_custos()
        
        if not custo.id:
            db.session.add(custo)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'custo': custo.to_dict(),
            'message': 'Custo calculado com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao calcular custo: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@estoque_bp.route('/estoque/custos-producao')
@login_required
def get_custos_producao():
    """Lista todos os custos de produção"""
    try:
        custos = CustoProducao.query.join(BrewFatherBatch).order_by(CustoProducao.data_calculo.desc()).all()
        return jsonify({
            'success': True,
            'custos': [custo.to_dict() for custo in custos]
        })
    except Exception as e:
        logger.error(f"Erro ao buscar custos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@estoque_bp.route('/estoque/custos-producao/<int:custo_id>', methods=['PUT'])
@login_required
def atualizar_custo_producao(custo_id):
    """Atualiza manualmente um custo de produção"""
    try:
        custo = CustoProducao.query.get_or_404(custo_id)
        data = request.get_json() or {}

        campos_float = [
            'custo_ingredientes', 'custo_embalagens', 'custo_operacional',
            'custo_mao_obra', 'custo_depreciacao', 'custo_total',
            'preco_venda_sugerido', 'custo_por_litro'
        ]

        for campo in campos_float:
            if campo in data and data[campo] is not None:
                setattr(custo, campo, float(data[campo]))

        if 'quantidade_produzida' in data and data['quantidade_produzida'] is not None:
            custo.quantidade_produzida = float(data['quantidade_produzida'])

        if 'margem_lucro' in data and data['margem_lucro'] is not None:
            custo.margem_lucro = float(data['margem_lucro'])

        custo.calcular_custos()
        db.session.commit()

        return jsonify({
            'success': True,
            'custo': custo.to_dict(),
            'message': 'Custo atualizado com sucesso!'
        })
    except Exception as e:
        logger.error(f"Erro ao atualizar custo de produção: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== RELATÓRIOS E ESTATÍSTICAS =====
@estoque_bp.route('/estoque/relatorios/resumo')
@login_required
def get_relatorio_resumo():
    """Retorna resumo do estoque para dashboard"""
    try:
        # Contar ingredientes ativos de cada tipo
        total_maltes = Malte.query.filter_by(ativo=True).count()
        total_lupulos = Lupulo.query.filter_by(ativo=True).count()
        total_leveduras = Levedura.query.filter_by(ativo=True).count()
        total_ingredientes = total_maltes + total_lupulos + total_leveduras
        
        estoque_total = EstoqueIngrediente.query.all()
        
        # Estatísticas
        itens_estoque_baixo = sum(1 for item in estoque_total if item.status_estoque in ['critico', 'baixo'])
        itens_esgotados = sum(1 for item in estoque_total if item.status_estoque == 'esgotado')
        valor_total_estoque = sum(float(item.valor_total_estoque) for item in estoque_total)
        
        # Movimentações recentes (últimos 30 dias)
        data_limite = datetime.utcnow() - timedelta(days=30)
        movimentacoes_recentes = MovimentacaoEstoque.query.filter(
            MovimentacaoEstoque.data_movimentacao >= data_limite
        ).count()
        
        return jsonify({
            'success': True,
            'resumo': {
                'total_ingredientes': total_ingredientes,
                'total_maltes': total_maltes,
                'total_lupulos': total_lupulos,
                'total_leveduras': total_leveduras,
                'itens_estoque_baixo': itens_estoque_baixo,
                'itens_esgotados': itens_esgotados,
                'valor_total_estoque': valor_total_estoque,
                'movimentacoes_30_dias': movimentacoes_recentes
            }
        })
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@estoque_bp.route('/estoque/relatorios/valor-estoque')
@login_required
def get_relatorio_valor_estoque():
    """Retorna valor do estoque por tipo de ingrediente"""
    try:
        # Buscar estoque e agrupar por tipo manualmente
        estoque_total = EstoqueIngrediente.query.all()
        
        valor_por_tipo = {
            'malte': 0,
            'lupulo': 0,
            'levedura': 0
        }
        
        for item in estoque_total:
            ingrediente_info = buscar_ingrediente_por_id(item.ingrediente_id)
            if ingrediente_info:
                tipo = ingrediente_info.get('ingrediente_tipo')
                if tipo in valor_por_tipo:
                    valor_por_tipo[tipo] += float(item.valor_total_estoque)
        
        dados = [{'tipo': tipo, 'valor_total': valor} for tipo, valor in valor_por_tipo.items()]
        
        return jsonify({
            'success': True,
            'dados': dados
        })
    except Exception as e:
        logger.error(f"Erro ao gerar relatório de valor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== PÁGINA PRINCIPAL =====
@estoque_bp.route('/estoque')
@login_required
def pagina_estoque():
    """Página principal do módulo de estoque"""
    return render_template('estoque.html')

# ===== DADOS PARA FORMULÁRIOS =====
@estoque_bp.route('/estoque/dados-formulario')
@login_required
def get_dados_formulario_estoque():
    """Retorna dados necessários para os formulários de estoque"""
    try:
        maltes = Malte.query.filter_by(ativo=True).order_by(Malte.nome).all()
        lupulos = Lupulo.query.filter_by(ativo=True).order_by(Lupulo.nome).all()
        leveduras = Levedura.query.filter_by(ativo=True).order_by(Levedura.nome).all()
        lotes = BrewFatherBatch.query.filter(BrewFatherBatch.status.in_(['Completed', 'Conditioning'])).order_by(BrewFatherBatch.brew_date.desc()).all()
        
        # Combinar todos os ingredientes
        ingredientes = []
        
        for malte in maltes:
            ingredientes.append({
                'id': malte.id,
                'nome': malte.nome,
                'tipo': 'malte',
                'fabricante': malte.fabricante,
                'unidade_medida': 'kg'
            })
            
        for lupulo in lupulos:
            ingredientes.append({
                'id': lupulo.id,
                'nome': lupulo.nome,
                'tipo': 'lupulo',
                'fabricante': lupulo.fabricante,
                'unidade_medida': 'g'
            })
            
        for levedura in leveduras:
            ingredientes.append({
                'id': levedura.id,
                'nome': levedura.nome,
                'tipo': 'levedura',
                'fabricante': levedura.fabricante,
                'unidade_medida': 'un'
            })
        
        return jsonify({
            'success': True,
            'ingredientes': ingredientes,
            'lotes': [{
                'id': lote.id,
                'nome': f"{lote.recipe_name} - Lote {lote.batch_no}",
                'batch_size': lote.batch_size
            } for lote in lotes]
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar dados do formulário: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500