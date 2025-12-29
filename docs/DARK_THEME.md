# Documentação de Manutenção - Tema Escuro

Esta documentação descreve o sistema de tema escuro implementado no BrewStation, incluindo arquitetura, manutenção e extensão.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Estrutura de Arquivos](#estrutura-de-arquivos)
- [Manutenção](#manutenção)
- [Extensão do Tema](#extensão-do-tema)
- [Troubleshooting](#troubleshooting)

## 🎨 Visão Geral

O sistema de tema escuro permite que os usuários alternem entre tema claro (padrão) e tema escuro. A preferência é salva no banco de dados e aplicada automaticamente em todas as páginas da aplicação.

### Características

- ✅ Alternância em tempo real (sem necessidade de recarregar a página)
- ✅ Preferência salva no banco de dados por usuário
- ✅ Fallback para localStorage quando usuário não está autenticado
- ✅ Aplicação global em todos os componentes Bootstrap
- ✅ Suporte a componentes customizados

## 🏗️ Arquitetura

### Componentes Principais

1. **Modelo de Dados** (`src/model/user.py`)
   - Campo `modo_escuro` (Boolean) no modelo User

2. **Backend**
   - Serviço: `src/services/profile_service.py`
   - API: `src/controller/api.py` - Rota `/api/auth/update_theme`

3. **Frontend**
   - Template base: `src/templates/base.html`
   - Página de perfil: `src/templates/profile.html`
   - CSS: Estilos inline no `base.html`
   - JavaScript: Função `toggleTheme()` global

### Fluxo de Funcionamento

```
Usuário alterna tema
    ↓
JavaScript atualiza data-theme no <body>
    ↓
CSS aplica estilos do tema escuro
    ↓
API salva preferência no banco de dados
    ↓
Próxima visita carrega tema salvo
```

## 📁 Estrutura de Arquivos

### Arquivos Modificados/Criados

```
src/
├── model/
│   └── user.py                    # Campo modo_escuro adicionado
├── services/
│   └── profile_service.py         # Função para salvar tema
├── controller/
│   └── api.py                     # Rota /api/auth/update_theme
└── templates/
    ├── base.html                  # CSS e JavaScript do tema
    └── profile.html               # Toggle de tema na interface
```

### Localização dos Estilos

Os estilos CSS do tema escuro estão localizados em `src/templates/base.html`, dentro da tag `<style>`, após os estilos padrão. Eles seguem o padrão:

```css
body[data-theme="dark"] .componente {
  /* estilos do tema escuro */
}
```

## 🔧 Manutenção

### Adicionar Estilos para Novos Componentes

Para adicionar suporte ao tema escuro em novos componentes:

1. **Identifique o seletor CSS do componente**

```css
/* Exemplo: componente customizado */
.meu-componente {
  background-color: #fff;
  color: #000;
}
```

2. **Adicione a variante dark no base.html**

```css
body[data-theme="dark"] .meu-componente {
  background-color: #2d2d2d;
  color: #e0e0e0;
}
```

3. **Localização no arquivo**

Os estilos devem ser adicionados em `src/templates/base.html`, dentro da tag `<style>`, após a linha que contém `/* Tema Escuro */`.

### Paleta de Cores Padrão

O tema escuro utiliza uma paleta consistente:

| Elemento | Cor Claro | Cor Escuro |
|----------|-----------|------------|
| Background | `#fff` | `#1a1a1a` |
| Cards | `#fff` | `#2d2d2d` |
| Headers | `#f8f9fa` | `#252525` |
| Bordas | `#dee2e6` | `#404040` |
| Texto Principal | `#212529` | `#e0e0e0` |
| Texto Secundário | `#6c757d` | `#999` |
| Inputs | `#fff` | `#3a3a3a` |
| Hover | `#f8f9fa` | `#3a3a3a` |

### Exemplo de Adição de Estilo

```css
/* Adicionar em src/templates/base.html dentro da seção de tema escuro */

/* Componente customizado */
body[data-theme="dark"] .meu-componente-customizado {
  background-color: #2d2d2d;
  border-color: #404040;
  color: #e0e0e0;
}

body[data-theme="dark"] .meu-componente-customizado:hover {
  background-color: #3a3a3a;
}
```

## 🚀 Extensão do Tema

### Adicionar Novos Temas

Para adicionar novos temas além de claro/escuro:

1. **Adicionar novo valor ao atributo data-theme**

```javascript
// Em base.html, função toggleTheme()
function toggleTheme() {
  const themes = ['light', 'dark', 'blue']; // Adicionar novo tema
  const currentTheme = body.getAttribute('data-theme') || 'light';
  const currentIndex = themes.indexOf(currentTheme);
  const newIndex = (currentIndex + 1) % themes.length;
  const newTheme = themes[newIndex];
  // ... resto do código
}
```

2. **Adicionar estilos CSS**

```css
body[data-theme="blue"] {
  background-color: #e3f2fd;
  color: #1565c0;
}

body[data-theme="blue"] .card {
  background-color: #bbdefb;
  border-color: #90caf9;
}
```

3. **Atualizar modelo de dados** (se necessário)

Se quiser salvar o tema específico no banco:

```python
# Em src/model/user.py
tema_preferido = Column(String(20), default='light')  # 'light', 'dark', 'blue'
```

### Integração com Plugins

Plugins podem adicionar seus próprios estilos de tema escuro:

1. **No template do plugin**, adicione estilos específicos:

```html
<!-- Em plugin/templates/meu_template.html -->
<style>
  body[data-theme="dark"] .plugin-meu-componente {
    background-color: #2d2d2d;
    color: #e0e0e0;
  }
</style>
```

2. **Ou crie um arquivo CSS separado** e inclua no template:

```html
{% block extra_css %}
<link href="{{ url_for('static', filename='plugin/css/dark-theme.css') }}" rel="stylesheet">
{% endblock %}
```

## 🐛 Troubleshooting

### Tema não está sendo aplicado

**Problema**: O tema escuro não está sendo aplicado após alternar.

**Soluções**:

1. Verifique se o atributo `data-theme` está sendo definido no `<body>`:
   ```javascript
   console.log(document.body.getAttribute('data-theme'));
   ```

2. Verifique se os estilos CSS estão carregados:
   ```javascript
   // No console do navegador
   const styles = document.querySelector('style');
   console.log(styles.textContent.includes('data-theme="dark"'));
   ```

3. Limpe o cache do navegador (Ctrl+F5 ou Cmd+Shift+R)

### Preferência não está sendo salva

**Problema**: O tema volta ao padrão após recarregar a página.

**Soluções**:

1. Verifique se o campo `modo_escuro` existe no banco de dados:
   ```sql
   SELECT modo_escuro FROM users WHERE id = 1;
   ```

2. Se o campo não existir, execute a migração:
   ```sql
   ALTER TABLE users ADD COLUMN modo_escuro BOOLEAN DEFAULT FALSE;
   ```

3. Verifique os logs do servidor para erros na API:
   ```bash
   tail -f logs/brewstation.log
   ```

### Estilos não estão sendo aplicados em componentes específicos

**Problema**: Alguns componentes não mudam de cor no tema escuro.

**Solução**:

1. Identifique o seletor CSS do componente usando DevTools
2. Adicione o estilo correspondente em `base.html`:
   ```css
   body[data-theme="dark"] .seletor-do-componente {
     /* estilos */
   }
   ```

### Conflito com estilos de plugins

**Problema**: Estilos de plugins sobrescrevem o tema escuro.

**Solução**:

1. Aumente a especificidade dos estilos do tema escuro:
   ```css
   /* Em vez de */
   body[data-theme="dark"] .componente { }
   
   /* Use */
   body[data-theme="dark"] .container .componente { }
   ```

2. Ou use `!important` (não recomendado, mas pode ser necessário):
   ```css
   body[data-theme="dark"] .componente {
     background-color: #2d2d2d !important;
   }
   ```

## 📝 Migração do Banco de Dados

Se você está atualizando uma instalação existente, execute:

```sql
-- Adicionar coluna modo_escuro
ALTER TABLE users ADD COLUMN modo_escuro BOOLEAN DEFAULT FALSE;

-- Verificar se foi adicionada
SELECT id, username, modo_escuro FROM users LIMIT 5;
```

## 🔍 Verificação de Funcionamento

### Teste Manual

1. Acesse a página de perfil (`/profile`)
2. Vá para a aba "Configurações"
3. Ative o switch "Modo escuro"
4. Verifique se toda a interface muda para tema escuro
5. Recarregue a página (F5)
6. Verifique se o tema escuro permanece ativo

### Teste via API

```bash
# Ativar tema escuro
curl -X POST http://localhost:5000/api/auth/update_theme \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"modo_escuro": true}'

# Verificar perfil do usuário
curl http://localhost:5000/api/auth/profile \
  -H "Cookie: session=..."
```

## 📚 Referências

- [Bootstrap Dark Mode](https://getbootstrap.com/docs/5.3/customize/color-modes/)
- [CSS Custom Properties para Temas](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)
- [Documentação de Configuração](CONFIGURATION.md)
- [Manual do Usuário](MANUAL.md)

---

**Última atualização**: Documentação criada para versão 1.0 do sistema de tema escuro.

