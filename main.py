import os
import json
import base64
from dotenv import load_dotenv

from flask import Flask, render_template, request, redirect, url_for, jsonify
from verizon.models.account_device_list_request import AccountDeviceListRequest
from verizon.models.account_device_list_result import AccountDeviceListResult
from verizon.models.account_details import AccountDetails
from verizon.models.account_device_list import AccountDeviceList
from verizon.models.carrier_activate_request import CarrierActivateRequest
from verizon.models.device_id import DeviceId
from verizon.models.device_management_result import DeviceManagementResult
from verizon.models.log_in_request import LogInRequest
from verizon.exceptions.connectivity_management_result_exception import ConnectivityManagementResultException
from apimatic_core.exceptions.auth_validation_exception import AuthValidationException
from verizon.exceptions.api_exception import APIException
from verizon.http.auth.thingspace_oauth import ThingspaceOauthCredentials
from verizon.http.auth.vz_m2m_token import VZM2mTokenCredentials
from verizon.models.log_in_result import LogInResult
from verizon.models.oauth_token import OauthToken
from verizon.configuration import Environment
from verizon.verizon_client import VerizonClient

app = Flask(__name__)

# Load the environment variables from the .env file
load_dotenv()

client_id = os.getenv("VERIZON_CLIENT_ID")
client_secret = os.getenv("VERIZON_CLIENT_SECRET")
uws_username = os.getenv("UWS_USERNAME")
uws_password = os.getenv("UWS_PASSWORD")

# Initialize global variables (you can set these dynamically based on your requirements)
account_name = "0942080249-00001"
service_plan = "98681"
sku_number = "VZW080000460098"
mdn_zip_code = "97035"
device_id = "89148000008306745823"
device_kind = "iccid"

# Route for the home page
@app.route('/')
def index():
    data = {
        "action": "Welcome",
    }
    return render_template('index.html', data=data)

@app.route('/init-verizon-client', methods=['GET'])
def init_verizon_client():
    global client, client_id, client_secret

    data = {
        "action": "Init Verizon Client",
    }

    client = VerizonClient(
        thingspace_oauth_credentials=ThingspaceOauthCredentials(
            oauth_client_id=client_id,
            oauth_client_secret=client_secret,
            oauth_on_token_update=(lambda oauth_token:
                                # Add the callback handler to perform operations like save to DB or file etc.
                                # It will be triggered whenever the token gets updated
                                _save_token_to_database(oauth_token)),
            oauth_token_provider=_oauth_token_provider
        ),
        environment=Environment.PRODUCTION
    )
    return render_template('index.html', data=data)

# Route to generate an access token (Note: access token automatically generated when initializing the client)
@app.route('/generate-access-token', methods=['GET'])
def generate_access_token():
    global client, client_id, client_secret, stored_oauth_token

    data = {
        "action": "Generate Access Token",
    }

    # Token generation logic (replace with actual API call if needed)
    try:
        client = VerizonClient(
            thingspace_oauth_credentials=ThingspaceOauthCredentials(
                oauth_client_id=client_id,
                oauth_client_secret=client_secret,
                oauth_on_token_update=(lambda oauth_token:
                                    # Add the callback handler to perform operations like save to DB or file etc.
                                    # It will be triggered whenever the token gets updated
                                    _save_token_to_database(oauth_token)),
                oauth_token_provider=_oauth_token_provider
            ),
            environment=Environment.PRODUCTION
        )
       
        auth_string = f"{client_id}:{client_secret}"
        # Convert the string to bytes
        auth_bytes = auth_string.encode('utf-8')
        # Base64 encode the byte string
        base64_auth = base64.b64encode(auth_bytes).decode('utf-8')
        
        response = client.oauth_authorization.request_token_thingspace_oauth("Basic " + base64_auth)
        data["items"] = response.body.access_token

        stored_oauth_token = response.body.access_token
        
        print('-------------STATUS CODE--------------')
        print(response.status_code)
        print('-------------ACCESS TOKEN--------------')
        print(response.body.access_token)
        print('-------------TOKEN TYPE--------------')
        print(response.body.token_type)
        print('-------------BODY--------------')
        print(vars(response.body))

    except APIException as e:
        data["items"] = "Error! " + e.reason
    except Exception as e:
        data["items"] = e.message
  
    return render_template('index.html', data=data)

# Route for the UWS username/password form (to generate a Session Token)
@app.route('/session-token')
def session_token_page():
    return render_template('session-token.html')

# Route to handle session token generation
@app.route('/generate-session-token', methods=['POST'])
def generate_session_token():
    global client, client_id, client_secret

    data = {
        "action": "Generate Session Token",
    }
    
    username = request.form.get('uws_username')
    password = request.form.get('uws_password')

    # Session token generation logic
    if username and password:

        session_management_controller = client.session_management
        body = LogInRequest(
            username= username,
            password= password
        )

        try:
            sessionTokenResponse = session_management_controller.start_connectivity_management_session(
                body=body
            )

        except ConnectivityManagementResultException as e: 
            data["items"] = "Connectivity Management Exception! " + e.reason
            return render_template('session-token.html', data=data)
        except APIException as e: 
            data["items"] = "API Exception! " + e.reason
            return render_template('session-token.html', data=data)
        
        # Session token generation success
        vzm2mToken = sessionTokenResponse.body.session_token 
        
        client = VerizonClient(
            thingspace_oauth_credentials=ThingspaceOauthCredentials(
                oauth_client_id=client_id,
                oauth_client_secret=client_secret,
                oauth_on_token_update=(lambda oauth_token:
                                # Add the callback handler to perform operations like save to DB or file etc.
                                # It will be triggered whenever the token gets updated
                                _save_token_to_database(oauth_token)),
                oauth_token_provider=_oauth_token_provider
            ),
            vz_m2m_token_credentials=VZM2mTokenCredentials(
                vz_m2m_token=vzm2mToken
            ),
            environment=Environment.PRODUCTION
        )
        
        data["items"] = vzm2mToken
        return render_template('index.html', data=data)
    else:
        data["items"] = "Username and Password are required"
        return render_template('session-token.html', data=data),


# Route to end session
@app.route('/end-session', methods=['GET'])
def end_session():
    global client
    data = {
        "action": "End Session",
    }

    session_management_controller = client.session_management
    try:
        result = session_management_controller.end_connectivity_management_session() 
        data["items"] = result.text
    except ConnectivityManagementResultException as e: 
        data["items"] = e.reason
    except APIException as e: 
        data["items"] = e.reason
    except Exception as e:
        data["items"] = e.message
    
    return render_template('index.html', data=data)

# Route to activate device
@app.route('/activate-device', methods=['GET'])
def activate_device():
    global client, device_id, device_kind, service_plan, mdn_zip_code, account_name, sku_number
    data = {
        "action": "Acitivate Device",
    }
    
    device_management_controller = client.device_management

    body = CarrierActivateRequest(
        devices=[
            AccountDeviceList(
                device_ids=[
                    DeviceId(
                        id=device_id,
                        kind=device_kind
                    )
                ]
            )
        ],
        service_plan = service_plan,
        mdn_zip_code = mdn_zip_code,
        account_name = account_name,
        sku_number = sku_number,
    )

    try:
        result = device_management_controller.activate_service_for_devices(body)

        # Controllers return type is an APIResponse object
        # Below we print out the properties of the API response object
        print('-------------STATUS CODE--------------')
        print(result.status_code) #int
        print("-----------------------------------")
        print(result.reason_phrase) #str
        print("-----------------------------------")
        print(vars(result.headers)) #dict
        print("-----------------------------------")
        print(result.text) #str
        print("-----------------------------------")
        print(vars(result.body)) #object
        print("-----------------------------------")
        print(result.errors) #Array of Strings
        print("-----------------------------------")
        print(vars(result.request)) #object

        data["items"] = result.text
    except ConnectivityManagementResultException as e: 
        data["items"] = "Connectivity Management Exception! " + e.reason
    except APIException as e: 
        data["items"] = "API Exception! " + e.reason
    except AuthValidationException as e:
        data["items"] = "Auth Validation Exception! " + e.message
    return render_template('index.html', data=data)

# Route to list service plans
@app.route('/get-service-plans', methods=['GET'])
def get_service_plans():
    global client, account_name
    data = {
        "action": "List Service Plans",
    }

    if account_name:
        service_plans_controller = client.service_plans
        try:
            result = service_plans_controller.list_account_service_plans(account_name)
            data["items"] = result.text
        except ConnectivityManagementResultException as e: 
            data["items"] = "Connectivity Management Exception! " + e.reason
            return render_template('index.html', data=data)
        except APIException as e: 
            data["items"] = "API Exception! " + e.reason
            return render_template('index.html', data=data)
        return render_template('index.html', data=data)
    else:
        data["items"] = "Error! " + e.reason
        return render_template('index.html', data=data)

# Route to list device info
@app.route('/get-device-info', methods=['GET'])
def get_device_info():
    global client, device_id, device_kind
    data = {
        "action": "List Device Information",
    }
    
    if device_id and device_kind:
        device_management_controller = client.device_management
        body = AccountDeviceListRequest(
            device_id=DeviceId(
                id=device_id,
                kind=device_kind
            )
        )
        try:
            result = device_management_controller.list_devices_information(body)
            data["items"] = result.text
        except ConnectivityManagementResultException as e: 
            data["items"] = "Connectivity Management Exception! " + e.reason
            return render_template('index.html', data=data)
        except APIException as e:
            data["items"] = "API Exception! " + e.reason
            return render_template('index.html', data=data) 
        return render_template('index.html', data=data), 200
    else:
        data["items"] = "Bad Request! " + e.reason
        return render_template('index.html', data=data)


# Function to save the token to a database
def _save_token_to_database(last_oauth_token):
    # Add the callback hander to perform operations like save to DB when token is updated
    print("Save Token")
    print(last_oauth_token)

# Function to load the token from the database
def _oauth_token_provider(last_oauth_token, auth_manager):
    # Add the callback handler to provide a new OAuth token
    # It will be triggered whenever the last provided o_auth_token is null or expired
    print("Load Token")
    print(last_oauth_token)

    if last_oauth_token is None:
        last_oauth_token = auth_manager.fetch_token()
    
    return last_oauth_token

if __name__ == '__main__':
    app.run(debug=True, port=2222)
