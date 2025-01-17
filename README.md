# Verizon Workshop Python Flask

## Introduction
This is a simple Python Flask app that will be used to demonstrate how to use the [Verizon Thingspace Developer Documentation](https://thingspace.verizon.com/documentation/api-documentation.html#/http/quick-start/introduction-to-the-verizon-api).

## Develop on Local machine
### Install Python
Python 3.10+ is the preferred version you can check your version by running
```
python3 --version
```

If you need to upgrade to a newer version of Python, go to the [python download page](https://www.python.org/downloads/).  

**Mac Users**
*The system Python on macOS 12.6.5 is Python 3.9.6 whose ssl module is compiled with LibreSSL 2.8.3. The removal of LibreSSL support in urllib3 2.0 makes it impossible to be used with the system Python on macOS.*

### Install pip
Pip is a package manager for Python. You can install pip by running the following command:
```
python3 -m pip install --user --upgrade pip
```

## Getting Started
### Download the code
Users can download the code by clicking the green "Code" button and selecting "Download ZIP".

Choose a folder to save the code and unzip the file.

### Create a virtual environment
A virtual environment is a self-contained directory tree that contains a Python installation for a particular version of Python, plus a number of additional packages.

**Open a terminal application and navigate to the folder where you downloaded the code.**

Create a virtual environment by running the following command:
```
python3 -m venv venv
```
Activate the virtual environment by running the following command:
```
source venv/bin/activate
```

### Install the dependencies
```
pip install -r requirements.txt
```

### Set the environment variables
Create a file called .env in the root of the project. Add the following environment variables:

```
VERIZON_CLIENT_ID="YOUR_CLIENT_ID"
VERIZON_CLIENT_SECRET="YOUR_CLIENT_SECRET"
UWS_USERNAME="YOUR_USERNAME"
UWS_PASSWORD = "YOUR_PASSWORD"
```

For the workshop, I'll share my credentials with you via email, but in a real-world scenario, you would need to create an app in the Verizon Developer Platform and get your own credentials.

### Run the app
```
python3 main.py
```

### Access the app
Open a web browser and navigate to http://127.0.0.1:8080/


## Develop in Replit

Use the Replit IDE to develop the app.

* Go to https://replit.com/ and create an account.
* Access this code as a [Replit project](https://replit.com/@sidmaestre/verizon-workshop-python-flask).
* Fork the Replit project into your account.
* Set the 4 environment variables in the Replit IDE. Go to the **All Tools Panel** and click on **Secrets**.
* Add the following 4 environment variables: VERIZON_CLIENT_ID, VERIZON_CLIENT_SECRET, UWS_USERNAME, UWS_PASSWORD.
* Run the project.

You can access the app at the URL provided by Replit.

## License
This project is licensed under the MIT License