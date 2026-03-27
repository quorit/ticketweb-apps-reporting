import Vue from 'vue'
import VueRouter from 'vue-router'
import TicketInfo from '../views/TicketInfo.vue'
import ReportingForm from '../views/Reporting.vue'
import RptSupport from '../views/RptSupport.vue'
import ErrorPage from '../views/ErrorPage.vue'

const authsystem_network = require ("authsystem_network");
import {get_error_params} from '../js_extra/web_project_error.js'
import store from '../store'





Vue.use(VueRouter)



const routes = [
	{
        path: '/ticket_info/:id',
        component: TicketInfo,
        name: 'ticket_info',
        props: (route) => { 
            return {
                id: route.params.id
            }; 
        }    
	},
    {
        path: '/forms/:type(admissions|student)',
        component: ReportingForm,
        name: "reporting_request_forms"
    },
    {
        path: '/forms/:type(rptsupport)',
        component: RptSupport,
        name: "reporting_support_form"
    },
    {
        path: '/error/:error_type/:status_code?',
        component: ErrorPage,
        name: 'error_page',
        // eslint-disable-next-line no-unused-vars
        props: true
    }

];



function scrollBehavior (to, from, savedPosition){
    if (savedPosition){
        return savedPosition;
    }else{
        return {x:0, y:0};
    }
}

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes,
  scrollBehavior
});


function generateRandomSequence(length = 43) {
    const charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~';
    let seq = '';
    const randomValues = new Uint32Array(length);
    window.crypto.getRandomValues(randomValues);
    
    for (let i = 0; i < length; i++) {
        seq += charset[randomValues[i] % charset.length];
    }
    return seq;
}


async function generateCodeChallenge(verifier) {
  // 1. Encode the verifier string into a byte array (Uint8Array)
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);

  // 2. Calculate the SHA-256 hash
  // This returns an ArrayBuffer
  const digest = await window.crypto.subtle.digest('SHA-256', data);

  // 3. Convert the ArrayBuffer to a Base64 string
  // Note: btoa() expects a "binary string", so we convert the bytes first
  const base64String = btoa(String.fromCharCode(...new Uint8Array(digest)));

  // 4. Convert Base64 to Base64URL format (standard for PKCE)
  // - Replace + with -
  // - Replace / with _
  // - Strip the = padding
  return base64String
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}









const config_data = JSON.parse(process.env.VUE_APP_CONFIG_DATA);





router.beforeEach(async (to,from,next) => {
    const authsystem_path = config_data.vue_app_path_roots.authsystem;
    const portal_type = config_data.login_portal_info.portal_type;
    const login_portal_info = config_data.login_portal_info.data;
    // Remove the leading slash from the route path if it exists to avoid //
    const routePath = to.path.startsWith('/') 
        ? to.path.substring(1) 
        : to.path;
    // Normally this will be the equivalent of
    // const redirect_uri = window.location.origin + window.location.pathname;
    // but we are relying on data from vue, not the browser, to construct redirect_uri for fear that
    // the browser url may not be accurate.
    const redirect_uri = window.location.origin + process.env.BASE_URL + routePath;

    async function next_login(){

        var login_url;
        
        
        if (portal_type == "ticketweb"){
            const server_root = login_portal_info.server_root;
            const params = new URLSearchParams({
                redirect_uri: redirect_uri
            });
            login_url = `${server_root}frontend/?${params.toString()}`;
        }else{
            //microsoft login portal
            const verifier = generateRandomSequence();
            const state = generateRandomSequence();
            sessionStorage.setItem('oauth_state', state);
            sessionStorage.setItem('pkce_verifier', verifier);
            const challenge = await generateCodeChallenge(verifier);
            const client_id = login_portal_info.client_id;
            const tenant_id = login_portal_info.tenant_id;
            const params = new URLSearchParams({
                client_id: client_id,
                response_type: 'code',
                redirect_uri: redirect_uri,
                scope: 'openid profile email User.Read',
                response_mode: 'query',
                code_challenge: challenge,
                code_challenge_method: 'S256',
                state: state,
                prompt: 'login'
            });
            login_url = `https://login.microsoftonline.com/${tenant_id}/oauth2/v2.0/authorize?${params.toString()}`;

        }
        location.replace(login_url)

    
    }

    
class StateMismatchError extends Error {
    constructor(state,returned_state) {
        const message = `Url query state ${returned_state} doesn't match stored state ${state}. `
        super(message);

    }
}



    if((to.name == 'reporting_request_forms' || to.name == 'reporting_support_form')){
        try{
            var id_token = null;
            if (portal_type == "ticketweb"){
                id_token=(to.query)["id_token"];

            }else{
                
                const code = (to.query)["code"];
                const state = window.sessionStorage.getItem('oauth_state');
                const returned_state = (to.query)["state"];
                const verifier = window.sessionStorage.getItem('pkce_verifier');
                try{
                    if (code && state && returned_state && verifier) {
                        const lastCode = window.sessionStorage.getItem('last_consumed_code');
                        if (code === lastCode) {
                            console.log("Blocking re-consumption of code:", code);
                            // Do nothing. Re-consumption can be flagged by ms as an attack
                        } else {
                            try{
                                if (state !== returned_state) {
                                    console.warn("State mismatch in OAuth flow. Potential CSRF attack. Expected:", state, "Received:", returned_state);
                                    throw new StateMismatchError(state,returned_state);
                                }
                                const tenant_id = login_portal_info.tenant_id;
                                const client_id = login_portal_info.client_id;
                                id_token = await authsystem_network.getIdToken_ms(code,redirect_uri,client_id,tenant_id,verifier);
                            } finally {
                                // Store the last consumed code to prevent reuse, even if getIdToken_ms throws an error
                                // We don't want to allow reuse of the code even if there was an error during token exchange,
                                // because the error could be due to a network issue or a temporary problem with the auth server, 
                                // and allowing reuse of the code in that case could still be a security risk.
                                window.sessionStorage.setItem('last_consumed_code', code);
                            }   
                        }
                    }
                } finally {
                    // Clear the PKCE verifier and state from sessionStorage to prevent reuse
                    window.sessionStorage.removeItem('pkce_verifier');
                    window.sessionStorage.removeItem('oauth_state');
                }
            
            }

            var json_data;
            if(id_token){
                json_data = await authsystem_network.get_app_token(authsystem_path,"reporting",id_token)
            }else{
                json_data = await authsystem_network.get_app_token(authsystem_path,"reporting");
            }
            const user_data=json_data.user_data;
            console.log(store.commit);
            store.commit('set_user_data',user_data);
            //Note that I am re-fetching the user data every time we go to a new page (other than login or error).
            //This is because in another window the user could log out and log in as someone else.
            //and if this app were any more involved, there would be links going from one route to another
            //*within* the app (the app does not reload when you navigate *within the app* links).
            //If that were to happen the user data would remain unchanged even if the user logged in as someone else.
            
            //If not for this problem we could load the user data in App.vue when the app (re)loads or
            //on login, if the user wasn't logged in when the app reloads.
            //The app reloads whenever the user navigates to a page in the website or when the
            //user manually changes the url in the url bar.
            //However that's not good enough because in a vue app a route change does not always imply an
            //app reload, and the user *can* change without an app reload, because a log our and login can occur
            //in a different tab/windows and the session cookies do not pertain to specific
            //browser window or tab.

            //In the case of *this* particular app, there are no in-app links, so it's impossible
            //to go to from one page to another without reloading the app, but we are not assuming
            //that the app will always be limited in this way.
        } catch (e) {
            if (e instanceof authsystem_network.SessionAuthenticationError
                || e instanceof StateMismatchError
            ){
                //this should cover...missing session cookie, expired session
                //anyhitng that would result in an "401 Unauthorized". Don't forget that
                //the language of 'Unauthorized' in HTTP codes is wrong
                //and really refers to authentication problems.
                //This also covers the case where the state does not match the returned state.
                next_login();
                return;
            }else{
                console.log("Failed to acquire app token with error: " + e);

                const error_params=get_error_params(e);
                next( {                    
                    name: "error_page",
                    params: error_params
                });
                return;
            }

        }
    }
    next();
 });


export default router
