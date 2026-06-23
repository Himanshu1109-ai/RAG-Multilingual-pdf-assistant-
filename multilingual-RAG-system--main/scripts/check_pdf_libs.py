import importlib

for name in ('PyPDF2','pypdf'):
    try:
        m = importlib.import_module(name)
        version = getattr(m, '__version__', 'unknown')
        print(f'{name}: OK ({version})')
    except Exception as e:
        print(f'{name}: FAIL ({e})')
