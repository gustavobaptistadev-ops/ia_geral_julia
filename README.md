# LifelineOne IA

Estrutura inicial do backend em FastAPI para o projeto LifelineOne IA.

## Como executar

1. Crie um ambiente virtual:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Inicie o servidor:
   ```bash
   uvicorn main:app --reload
   ```

## Endpoints iniciais

- GET /
- GET /api/v1/health
