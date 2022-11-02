if __name__ == '__main__':
    import sys
    from package import app
    
    args = sys.argv
    if len(args) == 2 and args[1] == "setup":
        sys.exit(app.run(setup=True))
    elif len(args) == 1:
        sys.exit(app.run())