# Quick Start Guide - Optimized POC

## TL;DR - Fastest Way to Run POC

```bash
# For quick validation (1-3 minutes)
python basic_usage.py --mode quick

# For full demo, run in parallel (3-8 minutes)
python basic_usage.py --mode parallel
```

## What Changed

✅ **Reduced max_steps**: From 8-15 to 3-5 steps per test  
✅ **Added timeouts**: No more 15-minute hangs  
✅ **Parallel execution**: Run tests concurrently  
✅ **Better error handling**: Graceful failure recovery  

## Execution Modes

| Mode | Time | Description | Use Case |
|------|------|-------------|----------|
| `quick` | 1-3 min | Basic example only | Quick validation |
| `parallel` | 3-8 min | All tests concurrent | Full demo, fastest |
| `sequential` | 8-15 min | One test at a time | Safe execution |

## Before You Run

1. Ensure `.env` file is configured
2. Browser session should be working
3. API keys are set up

## Expected Output

### Quick Mode
- 1 test scenario
- 4 exploration steps
- Basic functionality validation

### Parallel/Sequential Mode
- 8-15 test scenarios total
- Multiple website tests
- Playwright script generation
- Performance metrics

## If Problems Occur

1. **Still too slow?** Try reducing max_steps further in the code
2. **Timeouts?** Check browser session and network
3. **Errors?** Check logs for specific failures
4. **API issues?** Verify environment variables

The optimized script is now much more practical for demonstrations!