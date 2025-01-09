# Verizon Workshop Python Flask

## Introduction
This is a simple Python Flask app that will be used to demonstrate how to use the [Verizon Developer Platform](https://developer.verizon.com/).

## Prerequisites
### Install Python
Python 3.10+ is the preferred version you can check your version by running
```
python3 --version
```

If you need to upgrade to a newer version of Python, go to the [python download page](https://www.python.org/downloads/).  

**Mac Users**
The system Python on macOS 12.6.5 is Python 3.9.6 whose ssl module is compiled with LibreSSL 2.8.3. The removal of LibreSSL support in urllib3 2.0 makes it impossible to be used with the system Python on macOS.

### Install pip
Pip is a package manager for Python. You can install pip by running the following command:
```
python3 -m pip install --user --upgrade pip
```

## Getting Started
### Download the code
GitHub users can download the code by clicking the green "Code" button and selecting "Download ZIP".

Choose a folder to save the code and unzip the file.

### Create a virtual environment
A virtual environment is a self-contained directory tree that contains a Python installation for a particular version of Python, plus a number of additional packages.

Open a terminal application and navigate to the folder where you downloaded the code.

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
### Run the app
```
python3 main.py
```
