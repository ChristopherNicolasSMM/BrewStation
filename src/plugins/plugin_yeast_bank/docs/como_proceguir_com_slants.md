Aqui está o documento revisado conforme suas solicitações: sem palavras em CAIXA ALTA nos títulos e sem numeração nos títulos das seções.

---

# 🧫 **Yeast Bank - Manual Técnico e Gestão de Slants**

**Versão:** 2.0
**Responsável:** ____________________
**Data:** ____________________

---

## 📋 **Objetivo**

Este manual estabelece um protocolo padronizado para criação, manutenção e controle de um banco de leveduras cervejeiras utilizando slants (meio sólido inclinado).

**Escopo:** Pequenas cervejarias, brewpubs e laboratórios artesanais que necessitam de rastreabilidade, controle de qualidade e preservação de cepas.

**Entregável:** Documentação base para integração com sistema digital de gestão (aplicativo BrewStation).

---

## 🧪 **Fundamentação científica**

### Estabilidade genética e repiques

Estudos demonstram que populações de leveduras apresentam variabilidade genética mesmo dentro de uma mesma cepa. O repique serial (reutilização sucessiva) pode levar ao *drift genético* e fenotípico, afetando floculação, atenuação e perfil sensorial (Powell & Diacetis, 2007).

**Recomendação prática:** Limitar a 5-8 repiques por linhagem para minimizar riscos de deriva genética. Algumas cepas são mais resilientes que outras, portanto o monitoramento individual é essencial (Bühligen et al., 2013).

### Viabilidade e armazenamento

Slants mantidos sob refrigeração (2-4°C) preservam a viabilidade por 3-6 meses. Após este período, o repique é obrigatório para evitar perda de vitalidade (Jenkins et al., 2003).

> **Nota técnica:** O resfriamento deve ser gradual. Tubos retirados da geladeira precisam atingir temperatura ambiente antes da abertura para evitar condensação e contaminação.

### Heterogeneidade populacional

Nem todas as células de uma população são idênticas. Práticas inconsistentes de colheita podem selecionar subpopulações com características indesejadas (ex: células menos atenuativas) (Powell & Brindley, 2017).

---

## 🧫 **Meios de cultura (slants)**

### Opções de formulação

| Componente | Opção A (Mosto) | Opção B (MEA) | Opção C (YPD) |
|-------------|-----------------|---------------|---------------|
| Base | Mosto 1.040 (1L) | DME 100g | Extrato levedura 10g |
| | | | Peptona 20g |
| | | | Dextrose 20g |
| Ágar | 15g | 15g | 15g |
| Água | - | q.s.p. 1L | q.s.p. 1L |
| pH | 5,2-5,6 | 5,2-5,6 | 6,0-6,5 |

### Preparo passo a passo

| Etapa | Procedimento | Temperatura | Tempo |
|-------|--------------|-------------|-------|
| 1 | Dissolver componentes em água | Ambiente | Até homogeneizar |
| 2 | Ajustar pH (se necessário) | Ambiente | - |
| 3 | Distribuir 8-10mL/tubo | 40-50°C | - |
| 4 | Autoclavar | 121°C/15psi | 15 min |
| 5 | Inclinar tubos a ~30° | 50-60°C | Até solidificar |
| 6 | Resfriar e armazenar | Ambiente | 24h (teste esterilidade) |

---

## 🔬 **Inoculação e crescimento**

### Procedimento asséptico

```
1. Higienizar superfície e mãos
2. Flamejar alça microbiológica até rubor
3. Aguardar resfriamento da alça (3-5 seg)
4. Abrir tubo fonte (cepa matriz)
5. Coletar colônia isolada
6. Abrir tubo destino (slant estéril)
7. Riscar superfície em zigue-zague suave
8. Fechar imediatamente
9. Flamejar alça novamente
```

### Incubação

- **Temperatura:** 25-28°C
- **Período:** 24-48 horas
- **Critério de aceitação:** Crescimento visível e uniforme, sem colorações atípicas

---

## ❄️ **Armazenamento**

### Condições

| Parâmetro | Especificação | Observação |
|-----------|---------------|------------|
| Temperatura | 2-4°C | Geladeira exclusiva |
| Posição | Vertical | Evitar contato com tampa |
| Validade | 3-6 meses | Máximo 6 meses |
| Embalagem | Caixa protegida | Contra luz e variação térmica |

### Sistema de gerações

```
Banco master (G0)
    ↓
1º repique (G1) → Banco de trabalho
    ↓
2º repique (G2) → Banco de trabalho
    ↓
    ... (máximo G5-G8)
    ↓
Descarte e renovação
```

> **Importante:** O banco master (G0) deve permanecer intocado, servindo apenas como fonte para novos repiques (Wyeast Laboratories, 2025).

---

## 🏷️ **Identificação e rastreabilidade**

### Rotulagem padrão

```
┌─────────────────────┐
│ Cepa: US-05         │
│ Cód: US05-2026-03-G2│
│ Inoc: 02/03/2026    │
│ Val: 02/09/2026     │
│ Resp: CNM           │
└─────────────────────┘
```

### Campos obrigatórios

- Nome da cepa
- Código interno único
- Data de inoculação
- Data de validade (6 meses)
- Geração (G0, G1, G2...)
- Responsável

---

## ✅ **Controle de qualidade**

### Inspeção visual (mensal)

| Achado | Interpretação | Ação |
|--------|---------------|------|
| Manchas verdes/pretas | Contaminação fúngica | Descarte imediato |
| Crescimento filamentoso | Contaminação | Descarte imediato |
| Coloração atípica | Estresse/degradação | Descarte imediato |
| Ressecamento/rachaduras | Desidratação | Descarte |
| Aspecto cremoso uniforme | Saudável | Mantém |

### Teste funcional (trimestral)

```
Dia 1: Inocular em 10mL mosto 1.020
     ↓
Dia 2: Avaliar (24h)
     ↓
    ├─ Formação de krausen? → Sim → Ok
    ├─ Aroma normal? → Sim → Ok
    └─ Sedimentação adequada? → Sim → Ok
    
Falha em qualquer critério → Descartar lote
```

---

## 📊 **Sistema kanban (aplicativo)**

### Colunas do fluxo

| Coluna | Descrição | Ação |
|--------|-----------|------|
| 🟢 Ativas | Cepas em uso regular | Monitoramento padrão |
| 🟡 Próximas do vencimento | ≤ 60 dias para validade | Programar repique |
| 🔵 Em teste | Novas cepas em avaliação | Quarentena |
| 🟣 Repique programado | Aguardando transferência | Executar |
| 🔴 Descarte | Expiradas/contaminadas | Eliminar |

### Cartão digital (estrutura JSON)

```json
{
  "id": "US05-2026-03-G2",
  "cepa": "US-05",
  "geracao": 2,
  "data_inoculacao": "2026-03-02",
  "data_validade": "2026-09-02",
  "ultima_checagem": "2026-04-01",
  "resultado": "aprovado",
  "status": "ativo",
  "local_fisico": "Gaveta 2 / Caixa B",
  "observacoes": ""
}
```

---

## 📈 **Planilha de controle**

| ID | Cepa | G | Inoculação | Validade | Última checagem | Status | Local |
|----|------|---|------------|----------|-----------------|--------|-------|
| US05-01 | US-05 | 1 | 02/03/26 | 02/09/26 | 01/04/26 | 🟢 Ativo | G2-B |
| WLP001-01 | California | 2 | 15/02/26 | 15/08/26 | 01/04/26 | 🟡 Próximo | G1-A |
| S04-01 | SafAle | 0 | 10/01/26 | 10/07/26 | 01/04/26 | 🔴 Descarte | - |

---

## 🧰 **Boas práticas adicionais**

### Infraestrutura

- ✅ Geladeira **exclusiva** para culturas (sem alimentos)
- ✅ Superfície de trabalho higienizável
- ✅ Próximo a chama ou fluxo laminar
- ✅ Kit de alças descartáveis ou de nicromo
- ✅ Caixa organizadora para tubos

### Procedimentos

- ✅ Manter registro físico e digital
- ✅ Nunca abrir slant fora de ambiente controlado
- ✅ Nunca congelar slants
- ✅ Descartar imediatamente qualquer tubo suspeito
- ✅ Autoclave ou panela de pressão para esterilização

---

## 🚀 **Expansão do sistema**

Para maior segurança e escalabilidade:

| Nível | Técnica | Armazenamento | Complexidade |
|-------|---------|----------------|--------------|
| Básico | Slants | 2-4°C | Baixa |
| Intermediário | Glicerol 15% | -20°C | Média |
| Avançado | Criopreservação | -80°C | Alta |
| Profissional | Liofilização | Ambiente | Muito alta |

**Recomendação futura:** Implementar banco em glicerol 15% a -80°C como backup de segurança.

---

## 📚 **Referências científicas**

1. Powell, C.D., & Diacetis, A.N. (2007). Long term serial repitching and the genetic and phenotypic stability of brewer's yeast. *Journal of the Institute of Brewing*, 113(1), 67-74.

2. Bühligen, F., et al. (2013). Sustainability of industrial yeast serial repitching practice studied by gene expression and correlation analysis. *Journal of Biotechnology*, 168(4), 718-728.

3. Powell, C.D., & Brindley, S. (2017). Variation within brewing yeast populations. ASBC Annual Meeting.

4. Wyeast Laboratories. (2025). Yeast Harvesting & Repitching. Professional Resources.

5. Jenkins, D.M., et al. (2003). Impact of serial repitching on lager brewing yeast quality. *Journal of the American Society of Brewing Chemists*, 61(1), 1-7.

---

## 📝 **Anexos**

### Anexo A – Checklist diário

- [ ] Verificar temperatura da geladeira (2-4°C)
- [ ] Inspecionar visualmente tubos ativos
- [ ] Registrar qualquer alteração
- [ ] Atualizar planilha de controle

### Anexo B – Checklist trimestral

- [ ] Executar teste funcional em amostragem
- [ ] Revisar prazos de validade
- [ ] Programar repiques necessários
- [ ] Limpeza e organização do acervo

### Anexo C – Etiquetas para impressão

```
┌────────────────────┐
│ Cepa: __________   │
│ G: __  Inoc: __/__ │
│ Val: __/__  Resp:_ │
└────────────────────┘
```

