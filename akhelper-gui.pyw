if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    import webgui2.server
    webgui2.server.start()
