def normalize_pgserver(server: str):
    server = server.lower()
    if server == 'na':
        server = 'us'
    if server not in ('us', 'jp'):
        raise ValueError('unexpected server:', server)
    return server.upper()