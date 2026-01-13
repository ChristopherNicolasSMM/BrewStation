# Sistema de Dependências de Plugins

## Visão Geral

O sistema de plugins do BrewStation suporta dependências entre plugins com verificação de versão e status. Ao instalar um plugin, o sistema verifica automaticamente se todas as dependências estão instaladas e ativas.

## Formato de Dependências no install.json

As dependências podem ser especificadas de duas formas no arquivo `install.json`:

### Formato 1: String Simples

Especifica apenas o nome do plugin (sem verificação de versão):

```json
{
  "dependencies": [
    "device_manager",
    "plugin_mash_control"
  ]
}
```

### Formato 2: Objeto com Versão

Especifica o nome do plugin e a versão requerida:

```json
{
  "dependencies": [
    {
      "name": "device_manager",
      "version": "1.0.0"
    },
    {
      "name": "plugin_mash_control"
    }
  ]
}
```

**Nota:** Se `version` não for especificado, qualquer versão será aceita.

## Verificação de Dependências

Durante a instalação de um plugin, o sistema verifica:

1. **Existência**: O plugin de dependência existe no sistema?
2. **Instalação**: O plugin de dependência está instalado?
3. **Ativação**: O plugin de dependência está ativo?
4. **Versão**: Se uma versão for especificada, a versão instalada corresponde?

### Requisitos para Instalação

Para que um plugin possa ser instalado, **todas** as suas dependências devem:

- ✅ Estar encontradas no sistema
- ✅ Estar instaladas
- ✅ Estar ativas
- ✅ Ter versão compatível (se versão for especificada)

## Mensagens de Erro

Quando há problemas com dependências, o sistema retorna uma mensagem detalhada:

```
Não foi possível instalar o plugin 'plugin_mash_control' devido a problemas com dependências:

❌ device_manager: INSTALADO MAS INATIVO
   Plugin encontrado: plugin_device_manager
   Versão instalada: 1.0.0

Todas as dependências devem estar INSTALADAS e ATIVAS para continuar a instalação.
```

### Status Possíveis

- **✅ OK**: Dependência encontrada, instalada e ativa
- **❌ NÃO ENCONTRADO**: Plugin não existe no sistema
- **❌ NÃO INSTALADO**: Plugin existe mas não está instalado
- **❌ INSTALADO MAS INATIVO**: Plugin instalado mas não está ativo
- **❌ VERSÃO INCOMPATÍVEL**: Versão instalada não corresponde à requerida

## Exemplos de Uso

### Exemplo 1: Dependência Simples

```json
{
  "name": "meu_plugin",
  "dependencies": [
    "device_manager"
  ]
}
```

### Exemplo 2: Dependência com Versão Específica

```json
{
  "name": "meu_plugin",
  "dependencies": [
    {
      "name": "device_manager",
      "version": "1.0.0"
    }
  ]
}
```

### Exemplo 3: Múltiplas Dependências

```json
{
  "name": "plugin_avancado",
  "dependencies": [
    {
      "name": "device_manager",
      "version": "1.0.0"
    },
    "plugin_mash_control"
  ]
}
```

## Comandos CLI

### Instalar Plugin

```bash
flask plugin install plugin_name
```

Se houver problemas com dependências, a mensagem detalhada será exibida:

```
❌ Não foi possível instalar o plugin 'plugin_mash_control' devido a problemas com dependências:

❌ device_manager: INSTALADO MAS INATIVO
   Plugin encontrado: plugin_device_manager
   Versão instalada: 1.0.0

Todas as dependências devem estar INSTALADAS e ATIVAS para continuar a instalação.

Ação sugerida:
1. Instale todas as dependências faltantes
2. Ative todas as dependências instaladas mas inativas
3. Tente instalar o plugin novamente
```

### Verificar Status de Dependências

```bash
flask plugin info plugin_name
```

Mostra informações do plugin, incluindo dependências.

## Fluxo de Instalação

```
1. Usuário tenta instalar plugin
   ↓
2. Sistema verifica dependências
   ↓
3. Para cada dependência:
   a. Busca plugin no sistema
   b. Verifica se está instalado
   c. Verifica se está ativo
   d. Verifica versão (se especificada)
   ↓
4. Se todas OK:
   → Instala plugin
   ↓
5. Se alguma falhar:
   → Retorna erro detalhado
   → Aborta instalação
```

## Comparação de Versões

O sistema compara versões usando semântica de versionamento (ex: `1.0.0`, `1.2.3`).

**Formato suportado:**
- `MAJOR.MINOR.PATCH` (ex: `1.0.0`)
- `MAJOR.MINOR` (ex: `1.0`)
- Números inteiros (ex: `1`)

**Atualmente:**
- Requer versão exata (pode ser expandido no futuro para suportar `>=`, `<=`, etc.)

## Boas Práticas

1. **Especifique versões quando possível:**
   - Garante compatibilidade
   - Evita problemas com atualizações

2. **Mantenha dependências mínimas:**
   - Menos dependências = menos pontos de falha
   - Instalação mais rápida

3. **Documente dependências:**
   - Explique por que cada dependência é necessária
   - Documente versões mínimas/máximas suportadas

4. **Teste instalação:**
   - Teste com dependências instaladas/ativas
   - Teste com dependências faltantes
   - Teste com versões incompatíveis

## Troubleshooting

### Erro: "NÃO ENCONTRADO"

**Causa:** Plugin de dependência não existe no sistema.

**Solução:**
1. Verifique se o nome da dependência está correto
2. Certifique-se de que o plugin de dependência está no diretório `src/plugins/`
3. Use `flask plugin list` para ver plugins disponíveis

### Erro: "NÃO INSTALADO"

**Causa:** Plugin existe mas não está instalado.

**Solução:**
```bash
flask plugin install nome_da_dependencia
```

### Erro: "INSTALADO MAS INATIVO"

**Causa:** Plugin instalado mas não está ativo.

**Solução:**
```bash
flask plugin activate nome_da_dependencia
```

### Erro: "VERSÃO INCOMPATÍVEL"

**Causa:** Versão instalada não corresponde à requerida.

**Solução:**
1. Atualize o plugin de dependência para a versão requerida
2. Ou ajuste a versão requerida no `install.json` do seu plugin

## Limitações Atuais

1. **Comparação de versões:**
   - Atualmente requer versão exata
   - Suporte a operadores (`>=`, `<=`, `~>`) pode ser adicionado no futuro

2. **Dependências transitivas:**
   - Dependências de dependências não são verificadas automaticamente
   - Você deve garantir que todas as dependências diretas e indiretas estejam instaladas

3. **Resolução automática:**
   - O sistema não instala/ativa dependências automaticamente
   - Você deve fazer isso manualmente antes de instalar o plugin

## Exemplo Completo

### Plugin A (dependência)

```json
{
  "name": "device_manager",
  "version": "1.0.0",
  "dependencies": []
}
```

### Plugin B (depende de A)

```json
{
  "name": "plugin_mash_control",
  "version": "1.0.0",
  "dependencies": [
    {
      "name": "device_manager",
      "version": "1.0.0"
    }
  ]
}
```

### Fluxo de Instalação

```bash
# 1. Instalar dependência
flask plugin install device_manager
flask plugin activate device_manager

# 2. Instalar plugin que depende
flask plugin install plugin_mash_control
# ✅ Sucesso! Dependência verificada e OK
```

Se a dependência não estiver ativa:

```bash
flask plugin install plugin_mash_control
# ❌ Erro: device_manager está INSTALADO MAS INATIVO

flask plugin activate device_manager
flask plugin install plugin_mash_control
# ✅ Agora funciona!
```
