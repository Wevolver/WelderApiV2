# API V2

# Dependencies

1. Install [MongoDB](https://docs.mongodb.com/manual/administration/install-community/)
2. Install [Python](https://www.python.org/downloads/)
3. Install [pyenv](https://github.com/pyenv/pyenv-installer)
4. Install [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv)

# Setup

1. Clone this repo and `cd` into the project root.
2. Create a virtual environment: `pyenv virtualenv 3.7.1 api-v2-env`
3. Activate the virtual environment: `pyenv activate api-v2-env`
4. Install dependencies: `pip install -r requirements.txt`
5. Start MongoDB: `mongod` Make sure you have created a database named 'wevolver'
6. Run the flask app on debug mode: `FLASK_APP=app.py FLASK_DEBUG=1 flask run`
7. If you want to be able to upload images using the editor or in the project settings: install the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/installing.html) and input your AWS credentials.

# Configuration

1. Change the values DevelopmentConfig `./settings.py` to match you MongoDB and Welder setup.
2. Create a database in MongoDB named 'wevolver'

# Deployment instructions

1. Follow the instructions in [Wevolver Deployment](https://bitbucket.org/wevolver/deployment/src/master/)

# Configure Google Custom Search

# Configure Settings

# Configure Mailchimp list

# Configure Auth0
- Add Private Key

# Configure AWS Keys
