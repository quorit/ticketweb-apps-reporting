<template>
  <v-app>
    <v-app-bar
      app
      :color = "banner_color"
      dark
    >
      <!-- <div class="d-flex align-center">
        <v-img
          alt="Vuetify Logo"
          class="shrink mr-2"
          contain
          src="https://cdn.vuetifyjs.com/images/logos/vuetify-logo-dark.png"
          transition="scale-transition"
          width="40"
        />

        <v-img
          alt="Vuetify Name"
          class="shrink mt-1 hidden-sm-and-down"
          contain
          min-width="100"
          src="https://cdn.vuetifyjs.com/images/logos/vuetify-name-dark.png"
          width="100"
        />
      </div>

      <v-spacer></v-spacer> -->
      <span class="mr-2">
            OUR/UAR Service Ticket Request Forms {{ mode_text }}
      </span>
      <v-spacer/>
      <v-btn v-if="$route.name != 'login' && $route.name != 'error_page'"
                  class="ma-2"
                  @click ="logout()">
                  LOGOUT
               </v-btn>
    </v-app-bar>

    <v-main> 
      <router-view/>
    </v-main>
  </v-app>
</template>

<script>

const authsystem_network = require ("authsystem_network");
import {get_error_params} from './js_extra/web_project_error.js'

const config_data = JSON.parse(process.env.VUE_APP_CONFIG_DATA);

const authsystem_path = config_data.vue_app_path_roots.authsystem;

export default {
  name: 'App',


  data: () =>  
  {
    var banner_color;
    var mode_text;
    mode_text = config_data.banner.mode_text;
    banner_color = config_data.banner.color;
    
    return {
      banner_color: banner_color,
      mode_text: mode_text
      //
    };
  },
  methods: {
    logout: async function(){
      try {
         await authsystem_network.delete_session(authsystem_path,"reporting");      
      } catch (e) {
          this.$router.push( {                    
                    name: "error_page",
                    params: get_error_params(e)
                });
          return;
      }
      
      this.$router.go() //reloads page which should cause cause a re-route to the login page because the session cookie go mauled
    }

  },
  beforeCreate: async function(){
    try { 
      await this.$store.dispatch('set_init_data');
    } catch(e) {
      this.$router.push({
          name: "error_page",
          params: get_error_params(e)
      });            
    }
  }
};
</script>
