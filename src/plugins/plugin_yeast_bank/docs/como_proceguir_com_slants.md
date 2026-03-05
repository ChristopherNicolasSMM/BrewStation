# 🧫 Yeast Bank - Manual Técnico e Gestão de Slants

**Versão:** 2.1 (com protocolo econômico)\
**Responsável:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\
**Data:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

------------------------------------------------------------------------

## 📋 Objetivo

Este manual estabelece um protocolo padronizado para criação, manutenção
e controle de um banco de leveduras cervejeiras utilizando **slants
(meio sólido inclinado)**.

**Escopo:** pequenas cervejarias, brewpubs e laboratórios artesanais que
necessitam de rastreabilidade, controle de qualidade e preservação de
cepas.

**Entregável:** documentação base para integração com sistema digital de
gestão (aplicativo **BrewStation**).

------------------------------------------------------------------------

## 🧪 Fundamentação científica

### Estabilidade genética e repiques

Estudos demonstram que populações de leveduras apresentam variabilidade
genética mesmo dentro de uma mesma cepa. O **repique serial**
(reutilização sucessiva) pode levar ao *drift genético* e fenotípico,
afetando floculação, atenuação e perfil sensorial.

**Recomendação prática:** limitar a **5--8 repiques** por linhagem para
minimizar riscos de deriva genética.

------------------------------------------------------------------------

### Viabilidade e armazenamento

Slants mantidos sob **refrigeração (2--4 °C)** preservam a viabilidade
por **3--6 meses**. Após este período o repique é recomendado para
evitar perda de vitalidade.

> **Nota técnica:** tubos retirados da geladeira devem atingir
> temperatura ambiente antes da abertura para evitar condensação e
> contaminação.

------------------------------------------------------------------------

### Heterogeneidade populacional

Nem todas as células de uma população são idênticas. Práticas
inconsistentes de colheita podem selecionar subpopulações com
características indesejadas.

------------------------------------------------------------------------

## 🧫 Meios de cultura (slants)

### Opções de formulação

  Componente   Opção A (Mosto)     Opção B (MEA)   Opção C (YPD)
  ------------ ------------------- --------------- --------------------------
  Base         Mosto 1.040 (1 L)   DME 100 g       Extrato de levedura 10 g
                                                   Peptona 20 g
                                                   Dextrose 20 g
  Ágar         15 g                15 g            15 g
  Água         ---                 q.s.p. 1 L      q.s.p. 1 L
  pH           5.2--5.6            5.2--5.6        6.0--6.5

------------------------------------------------------------------------

### Preparo passo a passo

  Etapa   Procedimento                    Temperatura       Tempo
  ------- ------------------------------- ----------------- ---------------------------
  1       Dissolver componentes em água   Ambiente          Até homogeneizar
  2       Ajustar pH se necessário        Ambiente          ---
  3       Distribuir 8--10 mL por tubo    40--50 °C         ---
  4       Autoclavar                      121 °C / 15 psi   15 min
  5       Inclinar tubos (\~30°)          50--60 °C         Até solidificar
  6       Resfriar e armazenar            Ambiente          24 h (teste esterilidade)

------------------------------------------------------------------------

## 💰 Protocolo econômico de alta performance (Opção D)

Alternativa de **baixo custo e alto desempenho** utilizando insumos
comuns de farmácia e manipulação.

### Formulação base (1 L de mosto 1.040)

  Componente    Função               Fonte                   Dose
  ------------- -------------------- ----------------------- ------
  Mosto 1.040   Nutrientes básicos   Brassagem               1 L
  Ágar          Solidificante        Ágar culinário ou lab   15 g

------------------------------------------------------------------------

### Suplementação (farmácia de manipulação)

  Componente            Função                Dose cápsula   Cápsulas / L
  --------------------- --------------------- -------------- --------------
  Extrato de levedura   Vitaminas B           500 mg         10
  Peptona               Fonte de nitrogênio   500 mg         20
  MnSO₄                 Cofator enzimático    2 mg           1

------------------------------------------------------------------------

### Suplementação mineral

  Componente   Função               Dose     Origem
  ------------ -------------------- -------- ----------
  MgSO₄        Cofator enzimático   0.5 g    Farmácia
  CaCl₂        Parede celular       0.02 g   Farmácia
  Vitamina C   Antioxidante         0.05 g   Farmácia

------------------------------------------------------------------------

### Suplementação de zinco

  Componente   Produto         Dose
  ------------ --------------- --------
  Zinco        BioZinc gotas   0.5 mL

------------------------------------------------------------------------

### Protocolo resumido

1.  Preparar mosto 1.040\
2.  Adicionar cápsulas manipuladas\
3.  Adicionar sais minerais\
4.  Ferver 5--10 min\
5.  Adicionar vitamina C\
6.  Adicionar zinco\
7.  Ajustar pH (5.2--5.6)\
8.  Adicionar ágar\
9.  Distribuir em tubos\
10. Autoclavar\
11. Inclinar tubos\
12. Testar esterilidade (24 h)

------------------------------------------------------------------------

## 🔬 Inoculação

    1. Higienizar superfície
    2. Flamejar alça
    3. Aguardar resfriar
    4. Abrir tubo fonte
    5. Coletar colônia
    6. Inocular slant
    7. Fechar tubo
    8. Flamejar alça novamente

------------------------------------------------------------------------

## ❄️ Armazenamento

  Parâmetro     Especificação
  ------------- ---------------
  Temperatura   2--4 °C
  Posição       Vertical
  Validade      3--6 meses

------------------------------------------------------------------------

### Sistema de gerações

    G0 → Banco master
    G1 → Trabalho
    G2 → Trabalho
    ...
    G5–G8 → limite recomendado

------------------------------------------------------------------------

## 🏷️ Identificação

    ┌─────────────────────┐
    │ Cepa: US‑05         │
    │ Cód: US05‑2026‑03‑G2│
    │ Inoc: 02/03/2026    │
    │ Val: 02/09/2026     │
    │ Resp: CNM           │
    └─────────────────────┘

------------------------------------------------------------------------

## ✅ Controle de qualidade

  Achado                 Ação
  ---------------------- -----------
  Manchas verdes         Descartar
  Filamentos             Descartar
  Cor anormal            Descartar
  Crescimento uniforme   Manter

------------------------------------------------------------------------

## 📊 Kanban (BrewStation)

  Coluna        Função
  ------------- --------------------
  🟢 Ativas     Cepas em uso
  🟡 Próximas   Repique necessário
  🔵 Teste      Quarentena
  🟣 Repique    Transferência
  🔴 Descarte   Eliminar

------------------------------------------------------------------------

## 📈 Estrutura de registro (JSON)

``` json
{
  "id": "US05-2026-03-G2",
  "cepa": "US-05",
  "geracao": 2,
  "data_inoculacao": "2026-03-02",
  "data_validade": "2026-09-02",
  "status": "ativo"
}
```

------------------------------------------------------------------------

## 🧰 Boas práticas

-   Geladeira exclusiva
-   Registro digital e físico
-   Nunca congelar slants
-   Descartar tubos suspeitos
-   Esterilizar equipamentos

------------------------------------------------------------------------

## 🚀 Evolução do banco

  Nível           Técnica           Armazenamento
  --------------- ----------------- ---------------
  Básico          Slants            4 °C
  Intermediário   Glicerol          −20 °C
  Avançado        Criopreservação   −80 °C
  Profissional    Liofilização      Ambiente

------------------------------------------------------------------------

## 📚 Referências

Powell & Diacetis --- Journal of the Institute of Brewing\
Bühligen et al. --- Journal of Biotechnology\
Powell & Brindley --- ASBC Meeting\
Wyeast Laboratories --- Professional Resources\
Jenkins et al. --- Journal of the ASBC

------------------------------------------------------------------------

## 📝 Anexos

### Checklist diário

-   Verificar temperatura
-   Inspecionar tubos
-   Atualizar registros

### Etiqueta padrão

    ┌────────────────────┐
    │ Cepa: ______       │
    │ G: __ Inoc: __/__  │
    │ Val: __/__ Resp:_  │
    └────────────────────┘
