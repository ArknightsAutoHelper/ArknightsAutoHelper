module.exports = {
    chainWebpack: config => {
        config
            .plugin('html')
            .tap(args => {
                args[0].title = "Arknights Auto Helper";
                return args;
            })
    }
}