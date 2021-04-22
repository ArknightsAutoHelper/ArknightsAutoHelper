def launch(url):
    import sys
    print(list(sys.modules))
    import webview
    window = webview.create_window(title="Arknights Auto Helper", url=url, width=980, height=820, text_select=True)
    webview.start(debug=True)
