if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    import util.early_logs
    import util.unfuck_https_proxy
    import webgui2.server
    webgui2.server.start()
