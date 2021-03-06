import falcon
import jwt
import json
import re
import time
import os
import ldap
import sys
import requests
import urllib








class BadRequest(Exception):
    def __init__(self,message,status):
       self._message = message
       self.status = status

    def response_body(self):
       result = {
                  'message': self._message
                }
       cause = self.__cause__
       if cause:
          result['exception'] = str(cause)
       return result

    @staticmethod                     # This is like static in java
    def handle(e, req, resp, params): # These paramaters are required even though I'm only using resp and e
        resp.body = json.dumps(e.response_body())
        resp.status = e.status
        resp.content_type = falcon.MEDIA_JSON
    # i believe this function is a static because that allows me to refer to it even
    # when I don't have an object. I am registering the function with add_error_handler
    # and at that time no object is relevant




class BadRequestHeaderTooBig(BadRequest):
    def __init__(self):
         message = "'Authorization' header is too big"
         status = falcon.HTTP_REQUEST_HEADER_FIELDS_TOO_LARGE
         super().__init__(message,status)

class BadRequestHeaderBadFormatJWT(BadRequest):
    def __init__(self):
         message = "'Authorization' header does not have format, 'Bearer <jwt token>'"
         status = falcon.HTTP_BAD_REQUEST
         super().__init__(message,status)

class BadRequestHeaderBadFormatUserId(BadRequest):
    def __init__(self):
        message = "'UserId' header does not have correct format."
        status = falcon.HTTP_BAD_REQUEST
        super().__init__(message,status)


class BadRequestHeaderBadFormatOTP(BadRequest):
    def __init__(self):
        message = "'OTP' header does not have correct format."
        status = falcon.HTTP_BAD_REQUEST
        super().__init__(message,status)



class BadRequestHeaderBadFormatGSSAPI(BadRequest):
    def __init__(self):
         message = "'Authorization' header does not have format, 'Negotiate <token encoding>'"
         status = falcon.HTTP_BAD_REQUEST
         super().__init__(message,status)


class BadRequestExpiredToken(BadRequest):
    def __init__(self):
         message = "Token has expired."
         status = falcon.HTTP_UNAUTHORIZED # really means "unathenticated" in HTTP-speak
         super().__init__(message,status)

class BadRequestUnrecognizedMinion(BadRequest):
    def __init__(self,minion_id):
         message_fmt = "Unrecognized minion, {0}."
         message = message_fmt.format(minion_id)
         status = falcon.HTTP_UNAUTHORIZED # really means "unathenticated" in HTTP-speak
         super().__init__(message,status)

class BadRequestInvalidJWT_Token(BadRequest):
    def __init__(self):
         message = "Token is not valid."
         status = falcon.HTTP_BAD_REQUEST 
         super().__init__(message,status)

class BadRequestInvalidGSS_Token(BadRequest):
    def __init__(self):
         message = "GSS token is not valid."
         status = falcon.HTTP_BAD_REQUEST
         super().__init__(message,status)




class BadRequestRoleNotString(BadRequest):
    def __init__(self):
         message = "'role' field field in token payload is not a string."
         status = falcon.HTTP_BAD_REQUEST
         super().__init__(message,status)


class BadRequestContextNotString(BadRequest):
    def __init__(self):
         message = "'context' field field in token payload is not a string."
         status = falcon.HTTP_BAD_REQUEST
         super().__init__(message,status)


class BadRequestBadRoleName(BadRequest):
    def __init__(self):
         message =  "'role' field in token payload does not match pattern <computer_account_name>$@queensu.ca."
         status = falcon.HTTP_BAD_REQUEST
         super().__init__(message,status)

class BadRequestMissingHeader(BadRequest):
     def __init__(self,header):
          message = "'{0}' header is missing from the request.".format(header)
          status = falcon.HTTP_BAD_REQUEST
          super().__init__(message,status)

class BadRequestUnsupportedMechanism(BadRequest):
     def __init__(self):
          message = "GSSAPI Error: Unsupported mechanism requested."
          status = falcon.HTTP_BAD_REQUEST
          super().__init__(message,status)

class BadRequestBadQueryString(BadRequest):
     def __init__(self):
          message = "Unsupported query string for this route."
          status = falcon.HTTP_BAD_REQUEST
          super().__init__(message,status)

class BadRequestContextMismatch(BadRequest):
    def __init__(self):
        message = "Mismatching contexts."
        status = falcon.HTTP_BAD_REQUEST
        super().__init__(message,status)


class BadRequestLDAPAuthFail(BadRequest):
    def __init__(self):
        message = "LDAP authentication fail."
        status = falcon.HTTP_UNAUTHORIZED
        # really means unauthenticated in HTTP-speak.
        super().__init__(message,status)


class BadRequestSecretFileIOFail(BadRequest):
    def __init__(self):
        message = "Could not open OTP secret file for user."
        status = falcon.HTTP_INTERNAL_SERVER_ERROR
        super().__init__(message,status)


class BadRequestInvalidOTP(BadRequest):
    def __init__(self):
        message = "Invalid OTP code."
        status = falcon.HTTP_UNAUTHORIZED
        # really means unauthenticated in HTTP-speak.
        super().__init__(message,status)

class BadRequestUnknownContext(BadRequest):
    def __init__(self, context):
        message = "Uknown application context, {0}".format(context)
        status = falcon.HTTP_BAD_REQUEST
        # really means unauthenticated in HTTP-speak.
        super().__init__(message,status)

class BadRequestUserNotFound(BadRequest):
    def __init__(self, user_id):
        message = "Failed to find user '{0}' in LDAP db.".format(user_id)
        status = falcon.HTTP_BAD_REQUEST
        # really means unauthenticated in HTTP-speak.
        super().__init__(message,status)

class BadRequestNoContentReceived(BadRequest):
    def __init__(self):
        message = "No content received in request."
        status = falcon.HTTP_BAD_REQUEST
        # really means unauthenticated in HTTP-speak.
        super().__init__(message,status)



def _get_user_id_from_jwt_data(req):
    receive = requests.get(_config_data["pub_key_url"])
    if receive.status_code != 200:
            raise Exception("Failed commmunication with token server")
    pub_key=receive.text

    req_auth_hdr = req.get_header('Authorization')
    if not req_auth_hdr:
        raise BadRequestMissingHeader('Authorization')
    if len(req_auth_hdr) > 2048:
        raise BadRequestHeaderTooBig()
    re_pattern = r"^Bearer [-a-zA-Z0-9._]+$"
    if not re.search(re_pattern,req_auth_hdr):
        raise BadRequestHeaderBadFormatJWT()
    req_token = req_auth_hdr[len("Bearer "):]
    try:
        req_decoded = jwt.decode(
                req_token,pub_key,
                algorithms=['RS256'],
                options={"require": ["user_id","exp"]})
    except jwt.exceptions.ExpiredSignatureError as e:
        raise BadRequestExpiredToken()
    except jwt.exceptions.InvalidTokenError as e:
        # note that if the exp part of the claim has expired an exception will be thrown
        # (That test is built in)
        raise BadRequestInvalidJWT_Token() from e
    user_id = req_decoded['user_id']
    if not isinstance(user_id,str):
        raise BadRequestRoleNotString()
    return user_id



def create_token(secret,user_id, duration):

     exp_time = int(time.time()) + 60 * duration
     exp_time_english = time.ctime(exp_time)
     jwt_payload = {
         'user_id': user_id,
         'exp': exp_time
     }
     headers = {
        'alg': "HS256",
        'typ': "JWT"
     }
     jwt_token = jwt.encode(jwt_payload, secret, algorithm='HS256')
     return jwt_token



def create_response_body_user_data(display_name,mail):
    return {
            "display_name": display_name,
            "mail": mail
        }




def _canonicalise_userid(userid):
    userid_local = userid.lower()
    re_pattern = r"^[0-9a-z]+$"
    if re.search(re_pattern,userid_local):
        return userid_local
    re_pattern = r"^ad(\.queensu.ca){0,1}\\[0-9a-z]+$"
    if re.search(re_pattern,userid_local):
        return userid_local.split("\\")[1]
    re_pattern = r"^[0-9a-z]+@ad\.queensu\.ca$"
    if re.search(re_pattern,userid_local):
        return userid_local.split("@")[0]
     



if sys.base_prefix != sys.prefix:
    etc_path = sys.prefix + "/etc"
else:
    etc_path = "/etc"




def _get_config_data_all():
    print(etc_path)
    ldap_file = os.path.join(etc_path,"ticketweb/applications/reporting/config.json")

    f = open(ldap_file,"r")
    ldap_data = json.load(f)
    f.close()
    return ldap_data


_config_data = _get_config_data_all()


def _get_rt_api_token():
    api_token_exec = _config_data["rt"]["api_token_exec"]
    api_token = os.popen(api_token_exec).read()
    return api_token


_rt_api_token = _get_rt_api_token()




def _get_pw():
    password_exec = _config_data["ldap"]["password_exec"]
    pw = os.popen(password_exec).read()
    return pw


_service_account_pw = _get_pw()




def _get_ldap_handle():
        ldap_data = _config_data["ldap"]
        url = ldap_data["url"]
        ldap_handle  = ldap.initialize(url)
        service_account_dn = ldap_data["dn"]
        ldap_handle.simple_bind_s(service_account_dn,_service_account_pw)
        return ldap_handle


def _get_user_data(attributes,req):
    user_dn = _get_user_id_from_jwt_data(req)
    ldap_handle = _get_ldap_handle()
    ldap_handle.set_option(ldap.OPT_REFERRALS, 0)
    ldap_search_result = ldap_handle.search_s(user_dn,ldap.SCOPE_SUBTREE,"objectclass=*",attributes)
    if not user_dn:
            raise BadRequestUserNotFound(user_dn)
    result_attributes = ldap_search_result[0][1]
    result_dict = {}

    for attribute in attributes:
        result_dict[attribute]=result_attributes[attribute][0].decode(encoding='utf-8', errors='strict')
    return result_dict






class UserData ():

    def on_get(self,req,resp):
        user_data = _get_user_data(["displayName","mail"],req)
        response_body = create_response_body_user_data(user_data["displayName"],user_data["mail"])
        print(response_body)
        resp.text=json.dumps(response_body)
        resp.content_type = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_OK



class SubmitTicket():
    def __init__(self,report_type):
        self.report_type=report_type





    def on_post(self,resp,user_data,subject,due_date,ticket_content):
        rt_path_base = _config_data["rt"]["path_base"]
        auth_string = "Token " + _rt_api_token

        headers = {
            "Authorization": auth_string
        }
        mail = user_data["mail"]

        mail_enc = urllib.parse.quote(mail)
        rt_path= rt_path_base + "REST/2.0/"
        print (rt_path + "user/" + mail_enc)
        receive = requests.get(rt_path + "user/" + mail_enc,headers=headers)
        
        current_user_name = None

        if receive.status_code == 200:
            current_user_name = mail_enc
        elif receive.status_code == 404:
            receive = requests.get(rt_path + "user/" + user_data["sAMAccountName"],headers=headers)
            if receive.status_code == 200:
                current_user_name = user_data["sAMAccountName"]
            elif receive.status_code != 404:
                raise Exception("Failed RT communication")
        else:
            raise Exception("Failed RT communication")
            # this will result in a 500 error for the user
            # which is appropriate if this happens
        
        user_fields = {
            "RealName": user_data["displayName"],
            "Name": user_data["sAMAccountName"],
            "EmailAddress": mail
        }
        
        headers = {
            "Authorization": auth_string,
            "content-type": "application/json"
        }

        if not current_user_name:
            receive = requests.post(rt_path + "user",headers=headers,json=user_fields)
        else:
            url = rt_path+"user/"+current_user_name
            receive = requests.put(url,
                                   headers=headers,
                                   json=user_fields)
        


        if receive.status_code not in [200,201]:
            print (receive.status_code)
            raise Exception("Failed RT commmunication")


        
        

        internal_req_content = {
            "Requestor": mail,
            "Subject": subject,
            "Queue": _config_data["rt"]["queue"],
            "CustomFields": {
                "RequestType": self.report_type
            },
            "Content": ticket_content,
            "ContentType": "text/html"

        }
        if due_date:
            internal_req_content["Due"] = due_date

        receive = requests.post(rt_path + "ticket",
                                headers=headers,
                                json=internal_req_content)


        if receive.status_code != 201:
            raise Exception("Failed RT commmunication")
        resp.text=receive.text
        resp.content_type = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_OK

def get_req_content(req):
    if req.content_length == 0:
        raise BadRequestNoContentReceived()
    req_content = json.load(req.stream)
    return req_content
    #need more tests. is content too large? does it actually parse


def _get_due_date(req_content):
    if "due_date" not in req_content:
        return None
    return time.strftime("%Y-%m-%d %H:%M:%S" ,
                         time.gmtime(time.mktime(time.strptime(req_content["due_date"] + " 23:59:59",
                                     "%Y-%m-%d %H:%M:%S"))))
    # need to throw bad requestrs if the due date is unparseable.


def _get_subject(req_content):
    return req_content["subject"]




def _get_ticket_content_rptsupport(req_content):
    return req_content["content_data"]
    #content_data should really be json data and this function should turn it into html


def _get_ticket_content_admissions(req_content):
    return req_content["content_data"]
    #content_data should really be json data and this function should turn it into html

def _get_ticket_content_student(req_content):
    return req_content["content_data"]
    #content_data should really be json data and this function should turn it into html


def _get_user_data_submit_ticket(req):
    return _get_user_data(["displayName","mail","sAMAccountName"],req)


class SubmitTicketRptSupport(SubmitTicket):
    def __init__(self):
        super().__init__("rptsupport")

    def on_post(self,req,resp):
        user_data = _get_user_data_submit_ticket(req)
        subject = "Data support request"
        #For other form types this comes out of the request
        req_content = get_req_content(req)
        due_date = _get_due_date(req_content)
        ticket_content = _get_ticket_content_rptsupport(req_content)
        super().on_post(resp,user_data,subject,due_date,ticket_content)

class SubmitTicketRptSupport(SubmitTicket):
    def __init__(self):
        super().__init__("rptsupport")

    def on_post(self,req,resp):
        user_data = _get_user_data_submit_ticket(req)
        subject = "Data support request"
        #For other form types this comes out of the request
        req_content = get_req_content(req)
        due_date = _get_due_date(req_content)
        ticket_content = _get_ticket_content_rptsupport(req_content)
        super().on_post(resp,user_data,subject,due_date,ticket_content)

class SubmitTicketStudent(SubmitTicket):
    def __init__(self):
        super().__init__("student")

    def on_post(self,req,resp):
        user_data = _get_user_data_submit_ticket(req)
        #For other form types this comes out of the request
        req_content = get_req_content(req)
        subject = _get_subject(req_content)
        due_date = _get_due_date(req_content)
        ticket_content = _get_ticket_content_student(req_content)
        super().on_post(resp,user_data,subject,due_date,ticket_content)

class SubmitTicketAdmissions(SubmitTicket):
    def __init__(self):
        super().__init__("admissions")

    def on_post(self,req,resp):
        user_data = _get_user_data_submit_ticket(req)
        #For other form types this comes out of the request
        req_content = get_req_content(req)
        subject = _get_subject(req_content)
        due_date = _get_due_date(req_content)
        ticket_content = _get_ticket_content_admissions(req_content)
        super().on_post(resp,user_data,subject,due_date,ticket_content)
