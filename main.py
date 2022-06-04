if __name__ == '__main__':
    import sys
    from package import app
    
    try:
        args = sys.argv
        if args[1] == "setup":
            sys.exit(app.run(setup=True))
    except IndexError:
        sys.exit(app.run())