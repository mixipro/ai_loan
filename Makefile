# ═══════════════════════════════════════════════════════════
# CaliforniaCFO — Unified Monorepo Makefile
# ═══════════════════════════════════════════════════════════
# Manages both Python backend (uv) and React frontend (npm).
# Single entry point for all common workflows.
#
# Usage:
#   make install    — Install all dependencies (backend + frontend)
#   make dev        — Run backend + frontend in parallel
#   make backend    — Run only backend (port 8000)
#   make frontend   — Run only React frontend (port 5173)
#   make legacy     — Run legacy HTML frontend (file-based)
#   make test       — Run all tests
#   make build      — Production build (frontend)
#   make clean      — Clean caches and build artifacts
#   make typecheck  — TypeScript typecheck (frontend)
#   make lint       — Lint both backend and frontend
# ═══════════════════════════════════════════════════════════

.PHONY: help install backend frontend dev legacy test build clean typecheck lint nvm-check uv-check

# Default target
.DEFAULT_GOAL := help

# Color output
BLUE  := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED   := \033[0;31m
NC    := \033[0m

# ───────────────────────────────────────────────────────────
# HELP
# ───────────────────────────────────────────────────────────
help: ## Show this help message
	@echo ""
	@echo "$(BLUE)CaliforniaCFO — Monorepo Commands$(NC)"
	@echo "==================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Quickstart:$(NC)"
	@echo "  make install   # First time setup"
	@echo "  make dev       # Run backend + frontend"
	@echo ""

# ───────────────────────────────────────────────────────────
# CHECKS
# ───────────────────────────────────────────────────────────
uv-check:
	@command -v uv >/dev/null 2>&1 || { echo "$(RED)uv is not installed. Install: curl -LsSf https://astral.sh/uv/install.sh | sh$(NC)"; exit 1; }

nvm-check:
	@[ -s "$$HOME/.nvm/nvm.sh" ] || { echo "$(RED)nvm not found. Install from https://github.com/nvm-sh/nvm$(NC)"; exit 1; }

# ───────────────────────────────────────────────────────────
# INSTALL
# ───────────────────────────────────────────────────────────
install: install-backend install-frontend ## Install all dependencies (backend + frontend)
	@echo "$(GREEN)✓ All dependencies installed$(NC)"

install-backend: uv-check ## Install Python backend dependencies (uv)
	@echo "$(BLUE)Installing backend dependencies...$(NC)"
	uv sync
	@echo "$(GREEN)✓ Backend dependencies installed$(NC)"

install-frontend: nvm-check ## Install React frontend dependencies (npm)
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	@bash -c 'source $$HOME/.nvm/nvm.sh && nvm use && cd frontend-react && npm install'
	@echo "$(GREEN)✓ Frontend dependencies installed$(NC)"

# ───────────────────────────────────────────────────────────
# RUN
# ───────────────────────────────────────────────────────────
backend: uv-check ## Run backend (FastAPI on :8000)
	@echo "$(BLUE)Starting backend on http://localhost:8000$(NC)"
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend: nvm-check ## Run React frontend (Vite on :5173)
	@echo "$(BLUE)Starting React frontend on http://localhost:5173$(NC)"
	@bash -c 'source $$HOME/.nvm/nvm.sh && nvm use && cd frontend-react && npm run dev'

dev: ## Run backend + React frontend in parallel (requires two terminals or use 'make dev-tmux')
	@echo "$(YELLOW)Run these in TWO separate terminals:$(NC)"
	@echo "  Terminal 1: $(GREEN)make backend$(NC)"
	@echo "  Terminal 2: $(GREEN)make frontend$(NC)"
	@echo ""
	@echo "Or install GNU parallel + tmux for one-command:"
	@echo "  $(GREEN)make dev-tmux$(NC)"

dev-tmux: ## Run backend + frontend in tmux split panes
	@command -v tmux >/dev/null 2>&1 || { echo "$(RED)tmux not installed: sudo apt install tmux$(NC)"; exit 1; }
	tmux new-session -d -s california-cfo 'make backend'
	tmux split-window -h -t california-cfo 'make frontend'
	tmux attach -t california-cfo

legacy: ## Open legacy HTML frontend in browser
	@echo "$(YELLOW)Opening legacy HTML at frontend/index.html$(NC)"
	@xdg-open frontend/index.html 2>/dev/null || open frontend/index.html 2>/dev/null || echo "Manual: open frontend/index.html"

# ───────────────────────────────────────────────────────────
# QUALITY
# ───────────────────────────────────────────────────────────
test: test-backend test-frontend ## Run all tests
	@echo "$(GREEN)✓ All tests passed$(NC)"

test-backend: ## Run Python backend tests
	@echo "$(BLUE)Running backend tests...$(NC)"
	uv run pytest -v

test-frontend: ## Run React frontend tests
	@echo "$(BLUE)Running frontend tests...$(NC)"
	@bash -c 'source $$HOME/.nvm/nvm.sh && nvm use && cd frontend-react && npm test --if-present'

typecheck: ## TypeScript typecheck (frontend)
	@echo "$(BLUE)Running TypeScript typecheck...$(NC)"
	@bash -c 'source $$HOME/.nvm/nvm.sh && nvm use && cd frontend-react && npm run typecheck'

lint: ## Lint both backend and frontend
	@echo "$(BLUE)Linting frontend...$(NC)"
	@bash -c 'source $$HOME/.nvm/nvm.sh && nvm use && cd frontend-react && npm run lint'

# ───────────────────────────────────────────────────────────
# BUILD
# ───────────────────────────────────────────────────────────
build: ## Production build (React frontend)
	@echo "$(BLUE)Building frontend for production...$(NC)"
	@bash -c 'source $$HOME/.nvm/nvm.sh && nvm use && cd frontend-react && npm run build'
	@echo "$(GREEN)✓ Build complete: frontend-react/dist/$(NC)"

preview: ## Preview production build locally
	@echo "$(BLUE)Previewing production build...$(NC)"
	@bash -c 'source $$HOME/.nvm/nvm.sh && nvm use && cd frontend-react && npm run preview'

# ───────────────────────────────────────────────────────────
# CLEAN
# ───────────────────────────────────────────────────────────
clean: clean-backend clean-frontend ## Clean all caches and artifacts
	@echo "$(GREEN)✓ Cleaned all artifacts$(NC)"

clean-backend: ## Clean Python cache
	@echo "$(BLUE)Cleaning Python cache...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .ruff_cache 2>/dev/null || true

clean-frontend: ## Clean frontend caches and build
	@echo "$(BLUE)Cleaning frontend artifacts...$(NC)"
	rm -rf frontend-react/dist 2>/dev/null || true
	rm -rf frontend-react/node_modules/.vite 2>/dev/null || true

clean-deep: clean ## Deep clean: removes node_modules and .venv
	@echo "$(RED)Deep cleaning (removes node_modules + .venv)...$(NC)"
	rm -rf frontend-react/node_modules 2>/dev/null || true
	rm -rf .venv 2>/dev/null || true

# ───────────────────────────────────────────────────────────
# UTILITIES
# ───────────────────────────────────────────────────────────
status: ## Show project status
	@echo "$(BLUE)CaliforniaCFO — Project Status$(NC)"
	@echo "================================"
	@echo "uv:        $$(uv --version 2>/dev/null || echo 'NOT INSTALLED')"
	@bash -c 'source $$HOME/.nvm/nvm.sh 2>/dev/null && echo "node:      $$(node --version)" && echo "npm:       $$(npm --version)"'
	@echo "Backend:   $$([ -d .venv ] && echo 'Configured' || echo 'Not configured (run: make install)')"
	@echo "Frontend:  $$([ -d frontend-react/node_modules ] && echo 'Configured' || echo 'Not configured (run: make install)')"