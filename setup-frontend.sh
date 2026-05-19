#!/bin/bash
# ═══════════════════════════════════════════════════════════
# CaliforniaCFO — Frontend Setup Script
# ═══════════════════════════════════════════════════════════
# Idempotent installer for React frontend.
# Run from project root: bash setup-frontend.sh
#
# Stack:
#   - Vite 6 (latest)
#   - React 18
#   - TypeScript 5
#   - Tailwind CSS 3
#   - shadcn/ui (Radix-based)
#   - React Router 6
#   - TanStack Query (server state)
#   - Recharts (charts)
#   - Axios (HTTP client)
# ═══════════════════════════════════════════════════════════

set -e  # Exit on any error

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  CaliforniaCFO — React Frontend Setup                    ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# ───────────────────────────────────────────────────────────
# Step 1: Verify nvm + Node
# ───────────────────────────────────────────────────────────
echo -e "${BLUE}[1/8] Checking environment...${NC}"

if [ ! -s "$HOME/.nvm/nvm.sh" ]; then
    echo -e "${RED}✗ nvm not installed${NC}"
    echo "Install: curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash"
    exit 1
fi

# Load nvm
source "$HOME/.nvm/nvm.sh"

# Use Node 20 (from .nvmrc or install if missing)
if ! nvm use 20 >/dev/null 2>&1; then
    echo -e "${YELLOW}Installing Node 20 LTS...${NC}"
    nvm install 20
    nvm use 20
fi

NODE_VERSION=$(node --version)
NPM_VERSION=$(npm --version)
echo -e "${GREEN}✓ Node ${NODE_VERSION}, npm ${NPM_VERSION}${NC}"

# ───────────────────────────────────────────────────────────
# Step 2: Create Vite project
# ───────────────────────────────────────────────────────────
if [ -d "frontend-react" ]; then
    echo -e "${YELLOW}⚠ frontend-react/ already exists${NC}"
    read -p "Delete and recreate? [y/N] " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf frontend-react
    else
        echo -e "${YELLOW}Skipping Vite init (existing folder)${NC}"
    fi
fi

if [ ! -d "frontend-react" ]; then
    echo -e "${BLUE}[2/8] Creating Vite React+TS project...${NC}"
    npm create vite@latest frontend-react -- --template react-ts -y
    echo -e "${GREEN}✓ Vite project created${NC}"
fi

cd frontend-react

# ───────────────────────────────────────────────────────────
# Step 3: Pin Node version
# ───────────────────────────────────────────────────────────
echo -e "${BLUE}[3/8] Pinning Node version...${NC}"
echo "20" > .nvmrc
echo -e "${GREEN}✓ .nvmrc → Node 20${NC}"

# ───────────────────────────────────────────────────────────
# Step 4: Install base dependencies
# ───────────────────────────────────────────────────────────
echo -e "${BLUE}[4/8] Installing base dependencies...${NC}"
npm install

# ───────────────────────────────────────────────────────────
# Step 5: Add runtime dependencies
# ───────────────────────────────────────────────────────────
echo -e "${BLUE}[5/8] Installing runtime dependencies...${NC}"

# React ecosystem
npm install react-router-dom @tanstack/react-query axios

# UI/styling
npm install -D tailwindcss@^3.4.0 postcss autoprefixer
npm install class-variance-authority clsx tailwind-merge lucide-react

# Forms
npm install react-hook-form @hookform/resolvers zod

# Charts
npm install recharts

# Animations & utilities
npm install tailwindcss-animate

echo -e "${GREEN}✓ Runtime dependencies installed${NC}"

# ───────────────────────────────────────────────────────────
# Step 6: Init Tailwind
# ───────────────────────────────────────────────────────────
echo -e "${BLUE}[6/8] Initializing Tailwind CSS...${NC}"
npx tailwindcss init -p

# Configure tailwind.config.js
cat > tailwind.config.js << 'TAILWIND_EOF'
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
TAILWIND_EOF

echo -e "${GREEN}✓ Tailwind configured${NC}"

# ───────────────────────────────────────────────────────────
# Step 7: Create base CSS with shadcn variables
# ───────────────────────────────────────────────────────────
echo -e "${BLUE}[7/8] Setting up base CSS...${NC}"

cat > src/index.css << 'CSS_EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 221.2 83.2% 53.3%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 217.2 91.2% 59.8%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 224.3 76.3% 48%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
    font-feature-settings: "rlig" 1, "calt" 1;
  }
}
CSS_EOF

echo -e "${GREEN}✓ Base CSS configured${NC}"

# ───────────────────────────────────────────────────────────
# Step 8: Configure path aliases (@/ → src/)
# ───────────────────────────────────────────────────────────
echo -e "${BLUE}[8/8] Configuring TypeScript path aliases...${NC}"

# Install vite types for path
npm install -D @types/node

# Update tsconfig.json with paths
cat > tsconfig.json << 'TSCONFIG_EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src", "vite.config.ts"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
TSCONFIG_EOF

# Update vite.config.ts with path alias + proxy to backend
cat > vite.config.ts << 'VITE_EOF'
import path from "path"
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
VITE_EOF

echo -e "${GREEN}✓ Path aliases configured${NC}"

# ───────────────────────────────────────────────────────────
# Add scripts to package.json
# ───────────────────────────────────────────────────────────
echo -e "${BLUE}Adding npm scripts...${NC}"

# Use Node to update package.json
node << 'NODE_EOF'
const fs = require('fs');
const pkg = JSON.parse(fs.readFileSync('package.json', 'utf-8'));
pkg.scripts = {
  ...pkg.scripts,
  "dev": "vite",
  "build": "tsc -b && vite build",
  "preview": "vite preview",
  "typecheck": "tsc --noEmit",
  "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
};
pkg.engines = { "node": ">=20.0.0" };
fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2));
console.log("✓ package.json updated");
NODE_EOF

# ───────────────────────────────────────────────────────────
# Done
# ───────────────────────────────────────────────────────────
cd ..

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ React frontend setup complete!                         ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Add shadcn/ui components:"
echo "     ${YELLOW}cd frontend-react && npx shadcn@latest init${NC}"
echo ""
echo "  2. Start development:"
echo "     ${YELLOW}make backend${NC}    # Terminal 1 (port 8000)"
echo "     ${YELLOW}make frontend${NC}   # Terminal 2 (port 5173)"
echo ""
echo "  3. Open in browser:"
echo "     ${YELLOW}http://localhost:5173${NC}"
echo ""