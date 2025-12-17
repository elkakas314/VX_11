# Rotación de Secretos y Migración a GitHub Secrets

## Pasos Inmediatos (Local)

### 1. Backup tokens.env
```bash
cp tokens.env tokens.env.backup.$(date +%s)
```

### 2. Crear .env.local (no tracked)
```bash
cat tokens.env > .env.local
chmod 600 .env.local
```

### 3. Remover tokens.env del índice de Git
```bash
git rm --cached tokens.env
git add .gitignore
git commit -m "chore: remove tokens.env from tracking, use .env.local"
git push origin feature/ui/operator-advanced
```

### 4. Verificar que .env.local no se commitea
```bash
git status  # tokens.env debe estar ignorado
```

## Migración a GitHub Secrets

Una vez que tengas el repo privado VX_11:

### 1. Obtener valores de tokens.env
```bash
cat .env.local | grep -E "^[A-Z_]+=" | cut -d= -f1,2
```

### 2. Crear GitHub Secrets (usar gh CLI)
```bash
gh secret set VX11_GATEWAY_TOKEN --body "<tu-token-aqui>" --repo elkakas314/VX_11
gh secret set DEEPSEEK_API_KEY --body "<tu-key-aqui>" --repo elkakas314/VX_11
gh secret set HUGGINGFACEHUB_API_TOKEN --body "<tu-token-aqui>" --repo elkakas314/VX_11
gh secret set VX11_OPERATOR_TOKEN --body "<tu-token-aqui>" --repo elkakas314/VX_11
```

### 3. Rotar credenciales en proveedores
- **DeepSeek**: Ir a https://platform.deepseek.com → regenerar API key
- **HuggingFace**: Ir a https://huggingface.co/settings/tokens → crear token nuevo
- **VX11 interno**: Usar script tools/store_token_locally.sh

## Configuración CI/CD (GitHub Actions)

En `.github/workflows/ci.yml`:
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Create .env.local from secrets
        run: |
          echo "VX11_GATEWAY_TOKEN=${{ secrets.VX11_GATEWAY_TOKEN }}" >> .env.local
          echo "DEEPSEEK_API_KEY=${{ secrets.DEEPSEEK_API_KEY }}" >> .env.local
      - name: Run tests
        run: pytest tests/ -v
```

## Verificación Local

```bash
# Confirmar que tokens están siendo cargados desde .env.local
python -c "from config.tokens import load_tokens; load_tokens(); print('✓ Tokens loaded')"
```

## Auditoría Periódica

```bash
# Verificar que tokens.env no está en ningún commit reciente
git log -p --all -- tokens.env | head -100

# Si tokens.env aparece, purgar historia:
git filter-branch --tree-filter 'rm -f tokens.env' -- --all
git push --force-with-lease origin --all
```

## Checklist
- [ ] Backup tokens.env creado
- [ ] .env.local creado y en .gitignore
- [ ] tokens.env removido del índice
- [ ] Commit y push ejecutados
- [ ] GitHub Secrets creados (si VX_11 repo existe)
- [ ] CI workflow configurado
- [ ] Credenciales rotadas en proveedores
