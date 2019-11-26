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

All settings variable can be found in the file `settings.py`. Multiple sets of keys can be created by creating alternate classes that contain the same instance variables as `DevelopmentConfig`. To use your created settings classes, change the class used in this line `app.config.from_object('settings.DevelopmentConfig')`

## MongoDB

1. Create a database in MongoDB named 'wevolver'

## Welder

Welder-Api-V2 interfaces with another project called [Welder-Git-Server](https://github.com/Wevolver/Welder-Git-Server).

In order to create projects, you'll need to configure Welder-Git-Server first. Once you've followed the steps to configure that project, take the domain and port on which it's being served and add that to the settings folder under `WELDER_BASE_URL`.


## Configure Google Custom Search

Google Custom Search is used as on-site search for projects.

1. Create a Google Custom Search instance: https://cse.google.com/
2. In the search engine settings, generate a programmatic search custom access key
3. Add the key to the development settings in ./settings.py under SEARCH_KEY

# Configure Mailchimp list

# Configure Auth0
- Add Private Key

# Configure AWS Keys

`awscli` is used to manage aws credentials. Welder-apiv2 uses s3 for both project images a LFS files. In order to upload either you'll need to configure [awscli](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)

You'll also need to create an s3 bucket called `wevolver-project-images` ( this can be changed in `resources/projectImage.py`).
