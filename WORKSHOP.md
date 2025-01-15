# Woorkshop for the 2025-01-15

## How to Setup Python SDK from Scratch

Create a new python virtual environment and install the Verizon Python SDK.

In your terminal (or replit), run the following commands:

### Create a new directory
```
mkdir workshop
```

### Navigate to the new directory
```
cd workshop
```

### Create new python virtual environment by running 
```
python3 -m venv venv
```

### Activate new virtual environment by running 
```
source venv/bin/activate
```

### Add Verizon Python SDK dependency
```
pip install sdksio-verizon-apis-sdk==1.7.0
```

### Open Project in VS Code (unless you are in Replit)
```
code .
```

### Create a new python file
Create a new python file named `main.py`

### Add the following code to the `main.py` file
```python
from verizon.models.log_in_request import LogInRequest
from verizon.exceptions.connectivity_management_result_exception import ConnectivityManagementResultException
from verizon.exceptions.api_exception import APIException
from verizon.http.auth.thingspace_oauth import ThingspaceOauthCredentials
from verizon.configuration import Environment
from verizon.verizon_client import VerizonClient

client = VerizonClient(
    thingspace_oauth_credentials=ThingspaceOauthCredentials(
        oauth_client_id='YOU_CLIENT_ID',
        oauth_client_secret='YOUR_CLIENT_SECRET'
    ),
    environment=Environment.PRODUCTION
)

session_management_controller = client.session_management
body = LogInRequest(
    username='YOUR_USERNAME',
    password='YOUR_PASSWORD'
)

try:
    result = session_management_controller.start_connectivity_management_session(
        body=body
    )
    print(result)
except ConnectivityManagementResultException as e: 
    print(e)
except APIException as e: 
    print(e)
```

### Set the following environment variables
Client ID, Client Secret, Username, and Password

## Run the program
```
python3 main.py
```