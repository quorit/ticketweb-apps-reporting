<template>
   <v-container v-if="ticket_id">
       <div class="text-center">
        <v-icon
             x-large
             color="green"

            >
                mdi-check-bold
            </v-icon>
        </div>
        <v-row>
        <v-col cols="12">
                Ticket #{{ ticket_id }} has been created. An accompanying email should be sent to the email address you supplied.
             </v-col>
        </v-row>

   </v-container>
   <v-container v-else>
      <v-dialog v-model="show_submit_confirm">
              <v-card>
                <v-card-title>
                    Warning!
                </v-card-title>
                <v-card-text>
                    <div>
                       If you reset the form all of your work will be lost. Proceed anyway?
                    </div>
                </v-card-text>

                <v-card-actions>
                  <v-btn @click="show_submit_confirm=false">Cancel</v-btn>
                <v-btn @click="reset_all()">Proceed</v-btn>
                </v-card-actions>
              </v-card>
    </v-dialog>



      <v-row>
         <v-col cols="12">
            <h1>{{ heading }}</h1>
         </v-col>
      </v-row>
      <v-form
         ref="form"
         v-model="form_valid"
         lazy-evaluation
      >
         <slot/>
         <v-row>
            <v-col cols="12">
               <v-btn
                  class="ma-2"
                  @click="submit_ticket"
                  :disabled="processing_request">
                  {{ submit_button_label }}
               </v-btn>
               <v-btn
                  class="ma-2"
                  @click="show_submit_confirm=true"
                  :disabled="processing_request">
                  Reset this form
               </v-btn>

            </v-col>
         </v-row>

            </v-form>
      
      <v-row>
         <v-col cols="12">
            <v-alert type="error" v-if="submit_fail" v-model="submit_fail" dismissible  close-text="Close Alert">
               <ErrorDiv
                 :error_obj="submit_error">

               </ErrorDiv>
            </v-alert>
         </v-col>
      </v-row>

      <div v-if="devel_mode">
            {{ submission_display }}
       </div>
  </v-container>


</template>



<script>
  

const authsystem_network = require ("authsystem_network");
const rt_network = require ("rt_network");


import {FormValidationError} from '../js_extra/web_project_error.js'
import ErrorDiv from './ErrorDiv.vue'


import j5 from 'json5'
const config_data = j5.parse(process.env.VUE_APP_CONFIG_DATA);


const authsystem_path = config_data.vue_app_path_roots.authsystem;
const app_server_path = config_data.vue_app_path_roots.app_server;

class NotDAError extends Error {
    //this is for when a fetch fails and we don't even get a response
    constructor(){
       super("Campus Email included in request but user is not a designated approver.");
       this.name="NotDAError";
    }
}

export default {
   name: 'FormShell',
   components: {
      ErrorDiv
   },
   props: {
        clearFunc: Function,
        submissionData: Object,
        heading: String,
        initData: Object,
        submit_button_label: String,
        formType: String,
        designatedApprover: {
          default: true,
          type: Boolean
        }
   },
   data: function() {


      return {
         response_text: '',         
         form_valid: true,
         processing_request: false,
         submit_fail: false,
         submit_error: null,
         devel_mode: process.env.NODE_ENV === 'development',
         ticket_id: null,
         show_submit_confirm: false
      };
   },
   methods: {
      

      validate_form: function (app_token){
         return (new Promise((resolve,reject)=>{
            if (!this.designatedApprover){
               const err=new NotDAError();
               reject(err);
            }else{
               const validation_result = this.$refs.form.validate();
               if (validation_result){
                  resolve(app_token)  //just passes the app token down the chain.
                                      //Not used by this function which is not really async
               }else{
                  const err= new FormValidationError();
                  reject(err)
               }
            }
         }));
      },

   


      submit_ticket: async function () {
         this.processing_request=true;
         this.submit_fail=false;
         var response_json=null;




         try {
            

            response_json = await authsystem_network.get_app_token(authsystem_path,"reporting")
                            .then(this.validate_form)
                            .then(response => rt_network.submit_data(this.submissionData.json,
                                                           this.submissionData.attachments,
                                                           this.formType,
                                                           response.jwt_token,
                                                           app_server_path));
         } catch(e){
            if (e instanceof authsystem_network.SessionAuthenticationError){
               //this should cover...missing session cookie, expired session
               //anyhitng that would result in an "401 Unauthorized". Don't forget that
               //the language of 'Unauthorized' in HTTP codes is wrong
               //and really refers to authentication problems.
               this.$router.go();
            } else {
               this.submit_error=e;
               this.processing_request=false;
               this.submit_fail=true;
            }
            return;
         }
         this.ticket_id = response_json.id
         this.processing_request=false;
      },
      reset_all: async function(){
        try {
           await authsystem_network.get_app_token(authsystem_path,"reporting"); //don't care what the app_token is
        } catch (e){
           if (e instanceof authsystem_network.SessionAuthenticationError){
               //this should cover...missing session cookie, expired session
               //anyhitng that would result in an "401 Unauthorized". Don't forget that
               //the language of 'Unauthorized' in HTTP codes is wrong
               //and really refers to authentication problems.
               this.$router.go();
           }
           //we don't care about other errors that may result. not relevant
        }
        this.clearFunc();
        this.submit_fail=false;
        this.show_submit_confirm=false;
        this.$refs.form.resetValidation();
      },
   },
   computed:{
      submission_display: function() {
         return this.submissionData;
      }      
      
   },
   watch:{
   }
}
</script>





