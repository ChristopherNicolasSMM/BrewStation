# Governança: Ownership & Drift (não quebrar customizações)

O Maker só edita o que ele gerou.

## Conceitos
- owner: maker | manual | mixed
- managed_by_maker: true/false
- drift: quando o arquivo/bloco foi alterado manualmente

## Como o Maker marca artefatos
### 1) Manifest
Cada plugin-alvo gerado terá:
`src/plugins/<plugin_dir>/.maker/manifest.json`

Contém:
- project_id
- lista de artefatos gerados (screens, tables, routes, templates)
- hash/assinatura

### 2) Guarded blocks
Em arquivos gerados parcialmente:
- blocos BEGIN/END com project_id + hash

Exemplo:
# --- MAKER:BEGIN object=screen:list_customers project_id=12 hash=... ---
... gerado ...
# --- MAKER:END object=screen:list_customers ---

## Regras
- Se não houver manifest/blocos: artefato é “manual” (Maker não edita).
- Se houver drift (hash diferente): Maker entra em “readonly” e pede ação.

## Ações para drift
- Rebuild seguro (atualiza somente blocos gerados)
- Detach (remover managed_by_maker; Maker para de tocar)
- Copy/Clone (cria cópia gerada, mantém original manual)
- Force takeover (sobrescreve; exige confirmação forte)