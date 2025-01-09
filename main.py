import os
import json
import base64
from dotenv import load_dotenv

from flask import Flask, render_template, request, redirect, url_for, jsonify
from verizon.models.custom_fields_update_request import CustomFieldsUpdateRequest
from verizon.models.custom_fields import CustomFields
from verizon.models.carrier_deactivate_request import CarrierDeactivateRequest
from verizon.models.delete_devices_request import DeleteDevicesRequest
from verizon.models.carrier_actions_request import CarrierActionsRequest
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
username = os.getenv("UWS_USERNAME")
password = os.getenv("UWS_PASSWORD")

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
    global device_id, device_kind, service_plan, mdn_zip_code, account_name, sku_number
    data = {
        "action": "Activate Device",
    }
    
    client = _initialize_client()
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
        print('-------------REASON PHRASE--------------')
        print(result.reason_phrase) #str
        print('-------------HEADERS--------------')
        print(vars(result.headers)) #dict
        print('-------------RESULT TEXT--------------')
        print(result.text) #str
        print('-------------RESULT BODY--------------')
        print(vars(result.body)) #object
        print('-------------ARRAY OF ERRORS--------------')
        print(result.errors) #Array of Strings
        print('-------------REQUEST OBJECT--------------')
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
    global account_name
    data = {
        "action": "List Service Plans",
    }

    client = _initialize_client()
    service_plans_controller = client.service_plans
    try:
        result = service_plans_controller.list_account_service_plans(account_name)
        data["items"] = result.text
    except ConnectivityManagementResultException as e: 
        data["items"] = "Connectivity Management Exception! " + e.reason
    except APIException as e: 
        data["items"] = "API Exception! " + e.reason
    return render_template('index.html', data=data)


# Route to list device info
@app.route('/get-device-info', methods=['GET'])
def get_device_info():
    global client, device_id, device_kind
    data = {
        "action": "List Device Information",
    }

    client = _initialize_client()
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
    except APIException as e:
        data["items"] = "API Exception! " + e.reason

    return render_template('index.html', data=data)

# Route to update device custom field
@app.route('/update-device-custom-field', methods=['GET'])
def update_device_custom_field():
    global client, device_id, device_kind
    data = {
        "action": "Update Device Custom Field",
    }
    
    client = _initialize_client()
    device_management_controller = client.device_management
    body = CustomFieldsUpdateRequest(
        custom_fields_to_update=[
            CustomFields(
                key='CustomField1',
                value='West Region'
            ),
            CustomFields(
                key='CustomField2',
                value='Distribution'
            )
        ],
        devices=[
            AccountDeviceList(
                device_ids=[
                    DeviceId(
                        id=device_id,
                        kind=device_kind
                    )
                ]
            )
        ]
    )

    try:
        result = device_management_controller.update_devices_custom_fields(body)
        data["items"] = result.text
    except ConnectivityManagementResultException as e: 
        data["items"] = "Connectivity Management Exception! " + e.reason
    except APIException as e:
        data["items"] = "API Exception! " + e.reason

    return render_template('index.html', data=data) 

# Route to deactivate device
@app.route('/deactivate-device', methods=['GET'])
def deactivate_device():
    global client, device_id, device_kind, account_name
    data = {
        "action": "Deactivate Device",
    }
    
    client = _initialize_client()
    device_management_controller = client.device_management
    body = CarrierDeactivateRequest(
        account_name=account_name,
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
        reason_code='FF',
        etf_waiver=True,
        delete_after_deactivation=True
    )

    try:
        result = device_management_controller.deactivate_service_for_devices(body)
        data["items"] = result.text
    except ConnectivityManagementResultException as e: 
        data["items"] = "Connectivity Management Exception! " + e.reason
    except APIException as e:
        data["items"] = "API Exception! " + e.reason

    return render_template('index.html', data=data) 

# Route Delete deactivated devices
@app.route('/delete-deactivated-devices', methods=['GET'])
def delete_deactivated_devices():
    global client
    data = {
        "action": "Delete Deactivated Devices",
    }
    
    client = _initialize_client()
    device_management_controller = client.device_management
    body = DeleteDevicesRequest(
        devices_to_delete=[
            AccountDeviceList(
                device_ids=[
                    DeviceId(
                        id='09005470263',
                        kind='esn'
                    )
                ]
            ),
            AccountDeviceList(
                device_ids=[
                    DeviceId(
                        id='85000022411113460014',
                        kind='iccid'
                    )
                ]
            ),
            AccountDeviceList(
                device_ids=[
                    DeviceId(
                        id='85000022412313460016',
                        kind='iccid'
                    )
                ]
            )
        ]
    )

    try:
        result = device_management_controller.delete_deactivated_devices(body)
        data["items"] = result.text
    except ConnectivityManagementResultException as e: 
        data["items"] = "Connectivity Management Exception! " + e.reason
    except APIException as e:
        data["items"] = "API Exception! " + e.reason

    return render_template('index.html', data=data) 

# Route suspend device
@app.route('/suspend-device', methods=['GET'])
def suspend_device():
    global client, device_id, device_kind
    data = {
        "action": "Suspend device",
    }
    
    client = _initialize_client()
    device_management_controller = client.device_management
    body = CarrierActionsRequest(
        devices=[
            AccountDeviceList(
                device_ids=[
                    DeviceId(
                        id=device_id,
                        kind=device_kind
                    )
                ]
            )
        ]
    )

    try:
        result = device_management_controller.suspend_service_for_devices(body)
        data["items"] = result.text
    except ConnectivityManagementResultException as e: 
        data["items"] = "Connectivity Management Exception! " + e.reason
    except APIException as e:
        data["items"] = "API Exception! " + e.reason

    return render_template('index.html', data=data) 


# Route to Restore Device
@app.route('/restore-device', methods=['GET'])
def restore_device():
    global client
    data = {
        "action": "Restore Device",
    }
    
    client = _initialize_client()

    try:
        ##result = None
        ##data["items"] = result.text
        data["items"] = "Not implemented"
    except ConnectivityManagementResultException as e: 
        data["items"] = "Connectivity Management Exception! " + e.reason
    except APIException as e:
        data["items"] = "API Exception! " + e.reason

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

# Function to fully initialize the client with the session token
def _initialize_client():
    global client, username, password
    # Initialize the client
    client = VerizonClient(
        thingspace_oauth_credentials=ThingspaceOauthCredentials(
            oauth_client_id=client_id,
            oauth_client_secret=client_secret,
        ),
        environment=Environment.PRODUCTION
    )
    
    session_management_controller = client.session_management
    body = LogInRequest(
        username= username,
        password= password
    )

    sessionTokenResponse = session_management_controller.start_connectivity_management_session(
        body=body
    )

    # Session token generation success
    vzm2mToken = sessionTokenResponse.body.session_token 
    
    client = VerizonClient(
        thingspace_oauth_credentials=ThingspaceOauthCredentials(
            oauth_client_id=client_id,
            oauth_client_secret=client_secret,
        ),
        vz_m2m_token_credentials=VZM2mTokenCredentials(
            vz_m2m_token=vzm2mToken
        ),
        environment=Environment.PRODUCTION
    )

    return client

if __name__ == '__main__':
    app.run(debug=True, port=8080)
