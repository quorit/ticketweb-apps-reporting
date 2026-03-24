import Vue from 'vue'
import Vuex from 'vuex'

const rt_network = require("rt_network");

Vue.use(Vuex)

import j5 from 'json5'
const config_data = j5.parse(process.env.VUE_APP_CONFIG_DATA);

const shared_data_path = config_data.vue_app_path_roots.shared_data;

export default new Vuex.Store({
  state: {
    init_data: null,    //this will be an object after beeing loaded
    user_data: null
  },
  mutations: {
    set_init_data(state,init_data){
      state.init_data = init_data;
    },
    set_user_data(state,user_data){
      state.user_data = user_data;
    }
  },
  
  actions: {
    async set_init_data(context){

      const init_data = await rt_network.fetch_init_data(shared_data_path);
      return await new Promise((resolve) => {
        context.commit('set_init_data', init_data);
        resolve(true);
      });
    }

  },
  modules: {
  }
})