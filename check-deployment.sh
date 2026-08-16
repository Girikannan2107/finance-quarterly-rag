#!/bin/bash
# Quick deployment verification script for Finance RAG

echo "=================================="
echo "Finance RAG - Deployment Checker"
echo "=================================="
echo ""

# Check 1: Git status
echo "✓ Checking Git status..."
if [ -d .git ]; then
    echo "  ✓ Git repository found"
    git status --short | head -5
else
    echo "  ✗ Not a Git repository - run: git init"
fi
echo ""

# Check 2: Requirements file
echo "✓ Checking requirements.txt..."
if [ -f requirements.txt ]; then
    echo "  ✓ requirements.txt found"
    echo "  Dependencies:"
    grep -E "^[a-zA-Z]" requirements.txt | sed 's/^/    - /'
else
    echo "  ✗ requirements.txt not found"
fi
echo ""

# Check 3: Streamlit configuration
echo "✓ Checking Streamlit Cloud config..."
if [ -f .streamlit/config.toml ]; then
    echo "  ✓ .streamlit/config.toml found"
else
    echo "  ✗ .streamlit/config.toml not found"
fi

if [ -f .streamlit/secrets.toml ]; then
    echo "  ✓ .streamlit/secrets.toml found (local reference)"
else
    echo "  ✗ .streamlit/secrets.toml not found"
fi
echo ""

# Check 4: Main app file
echo "✓ Checking application files..."
if [ -f streamlit_app.py ]; then
    echo "  ✓ streamlit_app.py found"
else
    echo "  ✗ streamlit_app.py not found"
fi

if [ -f app/rag_pipeline.py ]; then
    echo "  ✓ RAG pipeline module found"
else
    echo "  ✗ RAG pipeline module not found"
fi
echo ""

# Check 5: .gitignore
echo "✓ Checking .gitignore..."
if grep -q ".env" .gitignore; then
    echo "  ✓ .env is ignored"
else
    echo "  ✗ .env not in .gitignore"
fi

if grep -q "chroma_db/" .gitignore; then
    echo "  ✓ chroma_db/ is ignored (data won't be committed)"
else
    echo "  ✗ chroma_db/ not in .gitignore"
fi
echo ""

# Check 6: Documentation
echo "✓ Checking documentation..."
[ -f DEPLOYMENT.md ] && echo "  ✓ DEPLOYMENT.md found" || echo "  ✗ DEPLOYMENT.md not found"
[ -f README.md ] && echo "  ✓ README.md found" || echo "  ✗ README.md not found"
[ -f FINAL_REPORT.md ] && echo "  ✓ FINAL_REPORT.md found" || echo "  ✗ FINAL_REPORT.md not found"
echo ""

# Check 7: Tests
echo "✓ Checking tests..."
if [ -d tests ]; then
    test_count=$(ls tests/test_*.py 2>/dev/null | wc -l)
    echo "  ✓ Tests directory found ($test_count test files)"
else
    echo "  ✗ Tests directory not found"
fi
echo ""

# Check 8: API keys
echo "✓ Checking for API keys..."
if [ -f .env ]; then
    if grep -q "OPENAI_API_KEY" .env; then
        echo "  ✓ OPENAI_API_KEY found in .env"
    else
        echo "  ✗ OPENAI_API_KEY not in .env"
    fi
    if grep -q "GROQ_API_KEY" .env; then
        echo "  ✓ GROQ_API_KEY found in .env"
    else
        echo "  ✗ GROQ_API_KEY not in .env"
    fi
else
    echo "  ⓘ No .env file (will use environment or Streamlit secrets)"
fi
echo ""

# Summary
echo "=================================="
echo "DEPLOYMENT READINESS SUMMARY"
echo "=================================="
echo ""
echo "To deploy to Streamlit Cloud:"
echo ""
echo "1. Push to GitHub:"
echo "   $ git add ."
echo "   $ git commit -m 'Ready for deployment'"
echo "   $ git push origin main"
echo ""
echo "2. Go to https://share.streamlit.io"
echo "   - Click 'New app'"
echo "   - Select repository: Girikannan2107/finance-quarterly-rag"
echo "   - Main file: streamlit_app.py"
echo "   - Click 'Deploy'"
echo ""
echo "3. Add secrets in Streamlit Cloud dashboard:"
echo "   - OPENAI_API_KEY"
echo "   - GROQ_API_KEY"
echo ""
echo "4. Upload PDFs and test with:"
echo "   'What was the total income each quarter?'"
echo ""
echo "For more details, see: DEPLOYMENT.md"
echo ""
