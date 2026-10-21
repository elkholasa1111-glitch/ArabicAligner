import sys


def dispatch():
    if '--cli' in sys.argv:
        sys.argv.remove('--cli')
        from app.cli import main
        return main()
    if '--acceptance-test' in sys.argv:
        from app.acceptance import main
        return main([a for a in sys.argv[1:] if a != '--acceptance-test'])
    if '--self-test' in sys.argv:
        from app.diagnostics import main
        return main([a for a in sys.argv[1:] if a != '--self-test'])
    from app.main import main
    return main()


if __name__ == '__main__':
    noninteractive = any(flag in sys.argv for flag in ('--cli', '--acceptance-test', '--self-test'))
    try:
        result = dispatch()
    except Exception:
        # Noninteractive entry points must return a failure status rather than
        # leave a windowed PyInstaller traceback dialog waiting for a person.
        if noninteractive:
            import traceback
            traceback.print_exc()
            sys.exit(1)
        raise
    sys.exit(result)
