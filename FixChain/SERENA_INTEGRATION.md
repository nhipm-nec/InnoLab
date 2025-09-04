# Serena Integration in FixChain

This document describes the integration of Serena toolkit into FixChain for enhanced bug fixing capabilities.

## Overview

FixChain now supports three types of fixers:
- **LLMFixer**: Original LLM-based batch fixing using Gemini AI
- **SerenaFixer**: Precision editing using Serena toolkit with Gemini AI assistance  
- **HybridFixer**: Combines both approaches for optimal results (recommended)

## New Features

### 🎯 Precision Bug Fixing
- Serena toolkit integration for symbol-level and line-level code editing
- Reduced token usage by targeting specific code sections
- Higher accuracy for simple security fixes

### 🔄 Enhanced Scan → Fix → Rescan Loop
- Automatic iteration up to 5 times (configurable via `MAX_ITERATIONS`)
- Stops when all bugs are fixed or no progress is made
- Better progress tracking and logging

### 🤖 AI-Generated Git Commits
- Automatic git commits after successful fixes
- AI-generated commit messages following conventional commit format
- Tracks which fixer was used for each fix

### 🧠 Hybrid Approach
- Phase 1: Serena precision fixes for simple issues
- Phase 2: LLM batch fixes for complex issues
- Combines benefits of both approaches

## Installation

1. Install additional dependencies:
```bash
pip install -r requirements_serena.txt
```

2. Ensure environment variables are set in `.env`:
```bash
GEMINI_API_KEY=your_gemini_api_key
PROJECT_KEY=your_project_key
MAX_ITERATIONS=5
```

## Usage

### Basic Commands

**Using Hybrid Fixer (Recommended):**
```bash
python3 run/run_demo.py --scanners bearer --fixers hybrid --project ../projects/Flask_App --mode cloud
```

**Using Serena Only:**
```bash
python3 run/run_demo.py --scanners bearer --fixers serena --project ../projects/Flask_App --mode cloud
```

**Using LLM Only:**
```bash
python3 run/run_demo.py --scanners bearer --fixers llm --project ../projects/Flask_App --mode cloud
```

### Multiple Scanners and Fixers

**Multiple scanners:**
```bash
python3 run/run_demo.py --scanners bearer,sonar --fixers hybrid --project ../projects/Flask_App
```

**Multiple fixers:**
```bash
python3 run/run_demo.py --scanners bearer --fixers serena,llm --project ../projects/Flask_App
```

### With RAG Support

```bash
python3 run/run_demo.py --scanners bearer --fixers hybrid --project ../projects/Flask_App --insert_rag --mode cloud
```

## Architecture

### SerenaFixer Class
- **Location**: `modules/fix/serena.py`
- **Purpose**: Precision editing with Gemini AI analysis
- **Features**:
  - Automatic Serena toolkit installation from GitHub
  - Gemini AI bug analysis and fix strategy generation
  - Basic fix patterns for common security issues
  - Fallback to simple fixes when Serena is unavailable

### HybridFixer Class  
- **Location**: `modules/fix/hybrid.py`
- **Purpose**: Combines Serena and LLM approaches
- **Features**:
  - Two-phase fixing approach
  - Git integration with auto-commits
  - AI-generated commit messages
  - Comprehensive result tracking

### Enhanced ExecutionService
- **Location**: `run/run_demo.py`
- **Improvements**:
  - Better iteration logic
  - Progress tracking
  - Early termination conditions
  - Detailed logging

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MAX_ITERATIONS` | Maximum scan-fix-rescan iterations | 5 |
| `GEMINI_API_KEY` | Google Gemini AI API key | Required |
| `PROJECT_KEY` | Project identifier | Required |
| `RAG_DATASET_PATH` | Path to RAG dataset | Optional |

### Fixer Selection

| Fixer | Best For | Token Usage | Accuracy |
|-------|----------|-------------|----------|
| `serena` | Simple security fixes | Low | High |
| `llm` | Complex logic issues | High | Medium |
| `hybrid` | All types of bugs | Medium | High |

## Testing

Run the integration test:
```bash
python3 test_serena_integration.py
```

Expected output:
```
🧪 Testing Serena Integration in FixChain
==================================================
✅ Environment variables check passed
✅ Serena and Hybrid fixers imported successfully
✅ All fixers created successfully
   - SerenaFixer: SerenaFixer
   - HybridFixer: HybridFixer
   - LLMFixer: LLMFixer
✅ Updated demo script help shows hybrid fixer option

🎉 Serena integration test completed!
```

## Expected Workflow

1. **Initial Scan**: Bearer/SonarQ scans find security issues
2. **Analysis**: Dify/Gemini analyzes bugs and creates fix strategy
3. **Phase 1 Fixing**: Serena applies precision fixes
4. **Phase 2 Fixing**: LLM handles remaining complex bugs
5. **Rescan**: Verify fixes were applied correctly
6. **Git Commit**: Auto-commit with AI-generated message
7. **Iteration**: Repeat until all bugs fixed or max iterations reached

## Troubleshooting

### Common Issues

**"Serena toolkit not found"**
- The system will automatically clone and install Serena from GitHub
- Ensure internet connection and git access

**"No bugs were fixed"**
- Check if GEMINI_API_KEY is valid
- Verify project files are accessible
- Review logs for specific error messages

**"Git commit failed"**
- Ensure the project directory is a git repository
- Check git configuration (user.name, user.email)

### Debug Mode

Add verbose logging:
```bash
export LOG_LEVEL=DEBUG
python3 run/run_demo.py --scanners bearer --fixers hybrid --project ../projects/Flask_App
```

## Performance Metrics

The system now tracks:
- **Bugs fixed per iteration**
- **Token usage** (input/output/total)
- **Fix accuracy** (similarity scores)
- **Execution time** per iteration
- **Fixer performance** (Serena vs LLM success rates)

## Next Steps

1. **Test with your project**: Run the hybrid fixer on your codebase
2. **Monitor results**: Check git commits and fix quality
3. **Tune parameters**: Adjust MAX_ITERATIONS based on your needs
4. **Extend Serena integration**: Add more sophisticated fix patterns
5. **Scale up**: Use with larger codebases and multiple projects

## Support

For issues or questions:
1. Check the logs in `logs/innolab_*.log`
2. Run the test script to verify setup
3. Review this documentation for configuration options
