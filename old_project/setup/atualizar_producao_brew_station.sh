#########################################################################
#Apenas colar no prompt do terminal para criar o script de atualização
#########################################################################

# Criar script com verificações
cat > atualizar_producao_brew_station << 'EOF'
#!/bin/bash
# Script para atualizar e recarregar automaticamente

echo "🔄 Iniciando atualização..."

# Verificar se a pasta existe
if [ ! -d "./BrewStation" ]; then
    echo "❌ Erro: Pasta BrewStation não encontrada!"
    exit 1
fi

# Navegar para o projeto
cd ./BrewStation

# Verificar se é um repositório git
if [ ! -d ".git" ]; then
    echo "❌ Erro: Não é um repositório Git!"
    exit 1
fi

# Atualizar código
echo "📥 Baixando atualizações..."
git pull origin main

# Verificar se o pull foi bem sucedido
if [ $? -eq 0 ]; then
    echo "✅ Código atualizado com sucesso!"
else
    echo "❌ Erro ao atualizar código!"
    exit 1
fi

# Recarregar aplicação
echo "🔄 Recarregando aplicação..."
if [ -f "/var/www/christophernsmm_pythonanywhere_com_wsgi.py" ]; then
    touch /var/www/christophernsmm_pythonanywhere_com_wsgi.py
    echo "✅ Aplicação recarregada!"
else
    echo "⚠️  Arquivo WSGI não encontrado, tentando encontrar..."
    WSGI_FILE=$(find /var/www -name "*christophernsmm*wsgi.py" | head -1)
    if [ -n "$WSGI_FILE" ]; then
        touch "$WSGI_FILE"
        echo "✅ Aplicação recarregada: $WSGI_FILE"
    else
        echo "❌ Não foi possível encontrar o arquivo WSGI!"
    fi
fi

echo "🎉 Atualização completa!"
EOF

# Dar permissão
chmod +x atualizar_producao_brew_station