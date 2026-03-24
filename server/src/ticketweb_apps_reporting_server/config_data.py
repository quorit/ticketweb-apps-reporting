import sys
import pyjson5 as json
import os

if sys.base_prefix != sys.prefix:
    _etc_path = sys.prefix + "/etc"
else:
    _etc_path = "/etc"




def _get_config_data_all():
    ldap_file = os.path.join(_etc_path,"ticketweb/applications/reporting/app-server-config.json5")

    f = open(ldap_file,"r")
    ldap_data = json.load(f)
    f.close()
    return ldap_data


config_data = _get_config_data_all()