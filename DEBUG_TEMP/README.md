# DEBUG_TEMP Folder

This folder contains temporary scripts used for debugging, validation, and analysis during development.

## Purpose
- Quick validation scripts
- One-off analysis scripts
- Debugging tools
- Investigation scripts

## When to Add Files Here
Any Python script that matches these patterns should go in this folder:
- `check_*.py` - Validation/checking scripts
- `debug_*.py` - Debugging scripts
- `validate_*.py` - Validation scripts
- `test_*.py` - Test scripts (not pytest)
- `analyze_*.py` - One-off analysis
- `investigate_*.py` - Investigation scripts
- `trace_*.py` - Debugging traces
- `audit_*.py` - Audit scripts
- `quick_*.py` - Quick checks
- `final_*.py` - Final validation scripts

## Cleanup
These files are temporary and can be deleted once the issue is resolved. Feel free to clean up old scripts periodically.

## Usage
```bash
# Run a validation script
python DEBUG_TEMP/validate_marksmen_final.py

# Clean up old files
Remove-Item DEBUG_TEMP/*.json
```

*Note: This folder is for development only and should not contain production pipeline code.*
