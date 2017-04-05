const path = require('path')

const webpack = require('webpack')

const ENVIRONMENT = process.env.NODE_ENV || 'development'
const PORT = process.env.PORT || 8080


module.exports = {
    devtool: '#eval-source-map',

    entry: './main.ts',
    output: {
        path: path.resolve(__dirname, '../beachfront/static/ui/'),
        publicPath: ENVIRONMENT === 'production' ? '/static/' : `http://localhost:${PORT}/`,
        filename: 'build.js',
    },
    module: {
        rules: [
            {
                test: /\.ts/,
                loader: 'ts-loader',
                exclude: /node_modules/,
                options: {
                    appendTsSuffixTo: [/\.vue$/],
                },
            },
            {
                test: /\.vue$/,
                loader: 'vue-loader',
                options: {
                    esModule: true,
                },
            },
            {
                test: /\.(png|jpg|gif|svg|ttf)$/,
                loader: 'file-loader',
                options: {
                    name: '[name].[ext]?[hash]',
                }
            }
        ]
    },
    resolve: {
        extensions: ['.ts', '.js'],
        alias: {
            'vue$': 'vue/dist/vue.esm.js',
        },
    },

    devServer: {
        noInfo: true,
    },

    performance: {
        hints: false,
    },

    plugins: [
        new webpack.DefinePlugin({
            'process.env.NODE_ENV': JSON.stringify(ENVIRONMENT),
        }),
    ],
}

if (ENVIRONMENT === 'production') {
    // http://vue-loader.vuejs.org/en/workflow/production.html

    module.exports.devtool = '#source-map'

    module.exports.plugins.push(new webpack.optimize.UglifyJsPlugin({
        sourceMap: true,
        compress: {
            warnings: false,
        }
    }))

    module.exports.plugins.push(new webpack.LoaderOptionsPlugin({
        minimize: true,
    }))
}
