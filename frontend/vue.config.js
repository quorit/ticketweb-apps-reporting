// const { defineConfig } = require('@vue/cli-service')
const path = require("path")
const config_data = JSON.parse(process.env.VUE_APP_CONFIG_DATA);





module.exports = {
  transpileDependencies: [
    'vuetify'
  ],
  publicPath: config_data.vue_app_path_roots.frontend,
  outputDir: path.resolve(process.env.VUE_APP_VENV_ROOT,"srv/ticketweb/applications/reporting/frontend"),
  devServer: (process.env.NODE_ENV=='development')?{
    port: config_data.devel_server.port,
    proxy: {
         ['^' + config_data.vue_app_path_roots.shared_data]: {
            target: config_data.devel_server.proxies.shared_data,
            pathRewrite: {
               ['^' + config_data.vue_app_path_roots.shared_data]: '/'
            }
         },

         ['^' + config_data.vue_app_path_roots.authsystem]: {
            target: config_data.devel_server.proxies.authsystem,
            pathRewrite: {
               ['^' + config_data.vue_app_path_roots.authsystem]: '/'
            }
         },


         ['^' + config_data.vue_app_path_roots.app_server]: {
            target: config_data.devel_server.proxies.app_server,
            pathRewrite: {
               ['^' + config_data.vue_app_path_roots.app_server]: '/'
            }
         }


   }
  }:{}
  // options...
}
