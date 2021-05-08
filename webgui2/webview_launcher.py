def launch(url, width, height, gui):
    import webview
    window = webview.create_window(title="Arknights Auto Helper", url=url, width=width, height=height, text_select=True)
    webview.start(gui=gui, debug=True)
