import requests
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, Float, JSON
from sqlalchemy.sql import func
from db.database import db

class BrewFatherSync(db.Model):
    """Modelo para controle de sincronização com BrewFather"""
    __tablename__ = 'brewfather_sync'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sync_type = Column(String(50), nullable=False)  # recipes, batches, inventory
    last_sync = Column(DateTime, nullable=True)
    items_count = Column(Integer, default=0)
    status = Column(String(20), default='pending')  # pending, success, error
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class BrewFatherRecipe(db.Model):
    """Modelo para receitas do BrewFather"""
    __tablename__ = 'brewfather_recipes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    brewfather_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    style = Column(String(100), nullable=True)
    abv = Column(Float, default=0)
    ibu = Column(Float, default=0)
    color = Column(Float, default=0)
    batch_size = Column(Float, default=0)
    efficiency = Column(Float, default=0)
    original_gravity = Column(Float, default=0)
    final_gravity = Column(Float, default=0)
    ingredients = Column(JSON)  # Maltes, lúpulos, leveduras
    notes = Column(Text, nullable=True)
    rating = Column(Float, default=0)
    brew_count = Column(Integer, default=0)
    last_brewed = Column(DateTime, nullable=True)
    created_date = Column(DateTime, nullable=True)
    raw_data = Column(JSON)  # Dados completos da API
    is_active = Column(Boolean, default=True)
    synchronized_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class BrewFatherBatch(db.Model):
    """Modelo para lotes do BrewFather"""
    __tablename__ = 'brewfather_batches'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    brewfather_id = Column(String(100), unique=True, nullable=False, index=True)
    recipe_id = Column(String(100), nullable=True)
    recipe_name = Column(String(200), nullable=False)
    batch_no = Column(Integer, default=0)
    status = Column(String(50), nullable=True)  # Planning, Brewing, Fermenting, Completed
    brew_date = Column(DateTime, nullable=True)
    estimated_og = Column(Float, default=0)
    measured_og = Column(Float, default=0)
    estimated_fg = Column(Float, default=0)
    measured_fg = Column(Float, default=0)
    estimated_abv = Column(Float, default=0)
    measured_abv = Column(Float, default=0)
    estimated_ibu = Column(Float, default=0)
    measured_ibu = Column(Float, default=0)
    estimated_color = Column(Float, default=0)
    measured_color = Column(Float, default=0)
    batch_size = Column(Float, default=0)
    efficiency = Column(Float, default=0)
    notes = Column(Text, nullable=True)
    rating = Column(Float, default=0)
    raw_data = Column(JSON)
    synchronized_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class BrewFatherInventory(db.Model):
    """Modelo para estoque do BrewFather"""
    __tablename__ = 'brewfather_inventory'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    brewfather_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)  # fermentable, hop, yeast, misc
    category = Column(String(100), nullable=True)
    quantity = Column(Float, default=0)
    unit = Column(String(20), nullable=True)  # kg, g, pkg, etc
    price = Column(Float, default=0)
    supplier = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    raw_data = Column(JSON)
    synchronized_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class BrewFatherAPI:
    """Classe para integração com a API do BrewFather"""
    
    BASE_URL = "https://api.brewfather.app/v2"
    
    def __init__(self, user_id=None, api_key=None):
        self.user_id = user_id
        self.api_key = api_key
        self.session = requests.Session()
        
        if user_id and api_key:
            self.session.auth = (user_id, api_key)
    
    def _make_request(self, endpoint, params=None):
        """Faz requisição para a API do BrewFather"""
        if not self.user_id or not self.api_key:
            raise ValueError("User ID e API Key são necessários")
        
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição para {endpoint}: {e}")
            return None
    
    def test_connection(self):
        """Testa a conexão com a API"""
        try:
            data = self._make_request("recipes")
            return data is not None
        except:
            return False
    
    def get_recipes(self, page=1, per_page=50):
        """Obtém receitas do BrewFather"""
        params = {
            'page': page,
            'limit': per_page,
            'order_by': 'name'
        }
        return self._make_request("recipes", params)
    
    def get_recipe(self, recipe_id):
        """Obtém uma receita específica"""
        return self._make_request(f"recipes/{recipe_id}")
    
    def get_batches(self, page=1, per_page=50, status=None):
        """Obtém lotes do BrewFather"""
        params = {
            'page': page,
            'limit': per_page,
            'sort': '-brewDate'
        }
        if status:
            params['status'] = status
        return self._make_request("batches", params)
    
    def get_batch(self, batch_id):
        """Obtém um lote específico"""
        return self._make_request(f"batches/{batch_id}")
    
    def get_inventory(self, page=1, per_page=50):
        """Obtém estoque do BrewFather"""
        params = {
            'page': page,
            'limit': per_page,
            'sort': 'name'
        }
        return self._make_request("inventory", params)
    
    def get_fermentables(self):
        """Obtém fermentáveis do estoque"""
        inventory = self.get_inventory(per_page=50)
        if inventory:
            return [item for item in inventory if item.get('type') == 'fermentable']
        return []
    
    def get_hops(self):
        """Obtém lúpulos do estoque"""
        inventory = self.get_inventory(per_page=50)
        if inventory:
            return [item for item in inventory if item.get('type') == 'hop']
        return []
    
    def get_yeasts(self):
        """Obtém leveduras do estoque"""
        inventory = self.get_inventory(per_page=50)
        if inventory:
            return [item for item in inventory if item.get('type') == 'yeast']
        return []

# Serviço de Sincronização
class BrewFatherService:
    """Serviço para sincronização com BrewFather"""
    
    @staticmethod
    def get_api_client():
        """Obtém cliente API configurado"""
        from model.config import Configuracao
        
        user_id = Configuracao.get_config('BREWFATHER_USER_ID')
        api_key = Configuracao.get_config('BREWFATHER_API_KEY')
        enabled = Configuracao.get_config('BREWFATHER_ENABLED')
        
        if not enabled or not user_id or not api_key:
            return None
        
        return BrewFatherAPI(user_id, api_key)
    
    @staticmethod
    def sync_recipes():
        """Sincroniza receitas do BrewFather"""
        print("Iniciando sincronização de receitas do BrewFather...")
        api = BrewFatherService.get_api_client()
        print(f"API Client: {api}")
        if not api:
            return {'success': False, 'error': 'BrewFather não configurado'}
        
        try:
            # Criar registro de sincronização
            sync = BrewFatherSync(sync_type='recipes', status='pending')
            db.session.add(sync)
            db.session.flush()
            
            # Buscar lista básica de receitas
            recipes_list = api.get_recipes(per_page=50)
            if not recipes_list:
                sync.status = 'error'
                sync.error_message = 'Nenhum dado recebido da API'
                db.session.commit()
                return {'success': False, 'error': 'Nenhum dado recebido da API'}
            
            count = 0
            error_count = 0
            
            for recipe_summary in recipes_list:
                try:
                    recipe_id = recipe_summary.get('_id')
                    if not recipe_id:
                        continue
                    
                    # BUSCAR DETALHES COMPLETOS DA RECEITA
                    recipe_detail = api.get_recipe(recipe_id)
                    if not recipe_detail:
                        print(f"⚠️  Não foi possível buscar detalhes da receita {recipe_id}")
                        error_count += 1
                        continue
                    
                    # Verificar se já existe
                    existing = BrewFatherRecipe.query.filter_by(
                        brewfather_id=recipe_id
                    ).first()
                
                    if existing:
                        recipe = existing
                    else:
                        recipe = BrewFatherRecipe(brewfather_id=recipe_id)
                        db.session.add(recipe)
                    
                    # ATUALIZAR COM DADOS COMPLETOS DO JSON DE DETALHES
                    recipe.name = recipe_detail.get('name', '')
                    
                    # Estilo - verificar diferentes formatos
                    style_data = recipe_detail.get('style')
                    if isinstance(style_data, dict):
                        recipe.style = style_data.get('name', '')
                    else:
                        recipe.style = str(style_data) if style_data else ''
                    
                    # Dados numéricos - usar valores do JSON detalhado
                    recipe.abv = recipe_detail.get('abv')
                    recipe.ibu = recipe_detail.get('ibu')
                    recipe.color = recipe_detail.get('color')
                    recipe.batch_size = recipe_detail.get('batchSize')
                    recipe.efficiency = recipe_detail.get('efficiency')
                    
                    # Gravidades - usar valores corretos do JSON
                    recipe.original_gravity = recipe_detail.get('og')
                    recipe.final_gravity = recipe_detail.get('fg')
                    
                    # Ingredientes - estruturar corretamente
                    ingredients = {
                        'fermentables': recipe_detail.get('fermentables', []),
                        'hops': recipe_detail.get('hops', []),
                        'yeasts': recipe_detail.get('yeasts', []),
                        'miscs': recipe_detail.get('miscs', [])
                    }
                    recipe.ingredients = ingredients
                    
                    # Datas - converter corretamente
                    created_date = recipe_detail.get('_created')
                    if created_date and isinstance(created_date, dict):
                        try:
                            seconds = created_date.get('_seconds', 0)
                            recipe.created_date = datetime.fromtimestamp(seconds)
                        except:
                            recipe.created_date = None
                    
                    last_brewed = recipe_detail.get('lastBrewed')
                    if last_brewed:
                        try:
                            # Pode ser timestamp ou objeto de data
                            if isinstance(last_brewed, (int, float)):
                                recipe.last_brewed = datetime.fromtimestamp(last_brewed / 1000)
                            elif isinstance(last_brewed, dict):
                                seconds = last_brewed.get('_seconds', 0)
                                recipe.last_brewed = datetime.fromtimestamp(seconds)
                        except Exception as e:
                            print(f"Erro ao converter data: {e}")
                            recipe.last_brewed = None
                    
                    # Outros campos
                    recipe.notes = recipe_detail.get('notes', '')
                    recipe.rating = recipe_detail.get('rating', 0)
                    recipe.brew_count = recipe_detail.get('brewCount', 0)
                    recipe.raw_data = recipe_detail
                    recipe.synchronized_at = datetime.now()
                    
                    count += 1
                    print(f"✅ Receita sincronizada: {recipe.name}")
                    
                except Exception as e:
                    print(f"❌ Erro ao processar receita {recipe_id}: {e}")
                    error_count += 1
                    continue
            
            sync.status = 'success'
            sync.items_count = count
            sync.last_sync = datetime.now()
            db.session.commit()
            
            return {
                'success': True, 
                'count': count,
                'error_count': error_count,
                'message': f'{count} receitas sincronizadas, {error_count} erros'
            }
            
        except Exception as e:
            db.session.rollback()
            if 'sync' in locals():
                sync.status = 'error'
                sync.error_message = str(e)
                db.session.commit()
            print(f"❌ Erro geral na sincronização: {e}")
            return {'success': False, 'error': str(e)}    
    
    
    
    @staticmethod
    def sync_batches():
        """Sincroniza lotes do BrewFather"""
        api = BrewFatherService.get_api_client()
        if not api:
            return {'success': False, 'error': 'BrewFather não configurado'}
        
        try:
            sync = BrewFatherSync(sync_type='batches', status='pending')
            db.session.add(sync)
            db.session.flush()
            
            batches_data = api.get_batches(per_page=50)
            if not batches_data:
                sync.status = 'error'
                sync.error_message = 'Nenhum dado recebido da API'
                db.session.commit()
                return {'success': False, 'error': 'Nenhum dado recebido da API'}
            
            count = 0
            for batch_data in batches_data:
                existing = BrewFatherBatch.query.filter_by(
                    brewfather_id=batch_data.get('_id')
                ).first()
                
                if existing:
                    batch = existing
                else:
                    batch = BrewFatherBatch(brewfather_id=batch_data.get('_id'))
                    db.session.add(batch)
                
                # Atualizar dados
                batch.recipe_id = batch_data.get('recipe', {}).get('_id', '')
                batch.recipe_name = batch_data.get('recipe', {}).get('name', '')
                batch.batch_no = batch_data.get('batchNo', 0)
                batch.status = batch_data.get('status', '')
                
                # Datas
                if batch_data.get('brewDate'):
                    batch.brew_date = datetime.fromtimestamp(batch_data.get('brewDate') / 1000)
                
                # Gravidades e medidas
                batch.estimated_og = batch_data.get('estimatedOg', 0)
                batch.measured_og = batch_data.get('measuredOg', 0)
                batch.estimated_fg = batch_data.get('estimatedFg', 0)
                batch.measured_fg = batch_data.get('measuredFg', 0)
                batch.estimated_abv = batch_data.get('estimatedAbv', 0)
                batch.measured_abv = batch_data.get('measuredAbv', 0)
                batch.estimated_ibu = batch_data.get('estimatedIbu', 0)
                batch.estimated_color = batch_data.get('estimatedColor', 0)
                batch.batch_size = batch_data.get('batchSize', 0)
                batch.efficiency = batch_data.get('efficiency', 0)
                
                batch.notes = batch_data.get('notes', '')
                batch.rating = batch_data.get('rating', 0)
                batch.raw_data = batch_data
                batch.synchronized_at = datetime.now()
                
                count += 1
            
            sync.status = 'success'
            sync.items_count = count
            sync.last_sync = datetime.now()
            db.session.commit()
            
            return {
                'success': True, 
                'count': count,
                'message': f'{count} lotes sincronizados'
            }
            
        except Exception as e:
            db.session.rollback()
            if 'sync' in locals():
                sync.status = 'error'
                sync.error_message = str(e)
                db.session.commit()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def sync_inventory():
        """Sincroniza estoque do BrewFather"""
        api = BrewFatherService.get_api_client()
        if not api:
            return {'success': False, 'error': 'BrewFather não configurado'}
        
        try:
            sync = BrewFatherSync(sync_type='inventory', status='pending')
            db.session.add(sync)
            db.session.flush()
            
            inventory_data = api.get_inventory(per_page=50)
            if not inventory_data:
                sync.status = 'error'
                sync.error_message = 'Nenhum dado recebido da API'
                db.session.commit()
                return {'success': False, 'error': 'Nenhum dado recebido da API'}
            
            count = 0
            for item_data in inventory_data:
                existing = BrewFatherInventory.query.filter_by(
                    brewfather_id=item_data.get('_id')
                ).first()
                
                if existing:
                    item = existing
                else:
                    item = BrewFatherInventory(brewfather_id=item_data.get('_id'))
                    db.session.add(item)
                
                # Atualizar dados
                item.name = item_data.get('name', '')
                item.type = item_data.get('type', '')
                item.category = item_data.get('category', '')
                item.quantity = item_data.get('quantity', 0)
                item.unit = item_data.get('unit', '')
                item.price = item_data.get('price', 0)
                item.supplier = item_data.get('supplier', '')
                item.notes = item_data.get('notes', '')
                item.raw_data = item_data
                item.synchronized_at = datetime.now()
                
                count += 1
            
            sync.status = 'success'
            sync.items_count = count
            sync.last_sync = datetime.now()
            db.session.commit()
            
            return {
                'success': True, 
                'count': count,
                'message': f'{count} itens de estoque sincronizados'
            }
            
        except Exception as e:
            db.session.rollback()
            if 'sync' in locals():
                sync.status = 'error'
                sync.error_message = str(e)
                db.session.commit()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_sync_status():
        """Obtém status das sincronizações"""
        last_syncs = {}
        for sync_type in ['recipes', 'batches', 'inventory']:
            sync = BrewFatherSync.query.filter_by(sync_type=sync_type)\
                .order_by(BrewFatherSync.last_sync.desc())\
                .first()
            if sync:
                last_syncs[sync_type] = {
                    'last_sync': sync.last_sync,
                    'status': sync.status,
                    'count': sync.items_count
                }
        
        return last_syncs