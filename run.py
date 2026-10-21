import sys
if __name__ == "__main__":
    if '--cli' in sys.argv:
        sys.argv.remove('--cli')
        from app.cli import main
        sys.exit(main())
    elif '--acceptance-test' in sys.argv:
        from app.acceptance import main
        sys.exit(main([a for a in sys.argv[1:] if a != '--acceptance-test']))
    elif '--self-test' in sys.argv:
        from app.diagnostics import main
        sys.exit(main([a for a in sys.argv[1:] if a != '--self-test']))
    else:
        from app.main import main
        sys.exit(main())
