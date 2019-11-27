# API V2

# Dependencies

## Evironment

- [MongoDB](https://docs.mongodb.com/manual/administration/install-community/)
- [Python](https://www.python.org/downloads/)
- [pyenv](https://github.com/pyenv/pyenv-installer)
- [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv)

## Packages

- `pip install -r requirements.txt`

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

Mongo stores all project metadata, users, tags, and bookmarks. Your mongo database is the main source of data that this api interfaces with. The database is named `wevolver`. If you'd like to change that name you can do so in `app.py` with this line `connect(host=app.config.get("DATABASE_HOST", "wevolver"))`. Just change wevolver to whatever name you decide to give the database.

1. Create a database in MongoDB named 'wevolver'
2. Add the host:port to `settings.py` under `DATABASE_HOST`

## Welder

Welder-Api-V2 interfaces with another project called [Welder-Git-Server](https://github.com/Wevolver/Welder-Git-Server).

In order to create projects, you'll need to configure Welder-Git-Server first. Once you've followed the steps to configure that project, take the domain and port on which it's being served and add that to the settings folder under `WELDER_BASE_URL`.

## Configure Google Custom Search

Google Custom Search is used as on-site search for projects.

1. Create a Google Custom Search instance: https://cse.google.com/
2. In the search engine settings, generate a programmatic search custom access key
3. Add the key to the development settings in ./settings.py under SEARCH_KEY

# Configure Auth

Welder-apiv2 is the main point of authentication between all of Welder's services. It determines if users are able to query the database and read metadata and also if they can read files through Welder-Git-Server.

## Auth0

Auth0 handles all authentication. Auth0 config is all handled in `auth/auth0.py`

1. configure an api on Auth0 according to this guide: https://auth0.com/docs/quickstart/spa/react#configure-auth0
2. Based on your configuration, fill in `AUTH0_DOMAIN`

## JWT

Welder-Apiv2 authenticates users against Auth0 and then creates a JWT token that can be sent to to Welder-Git-Server

First create a public/private key pair and add them as `jwt.sign` and `jwt.verify`. This will be used to verify that the permission grant is coming from Welder-Apiv2.

Then, take the public key, `jwt.verify`, and add that to Welder-Git-Server as `Welder-Git-Server/welder/permissions/jwt.verify`.

# Configure AWS Keys

`awscli` is used to manage aws credentials. Welder-apiv2 uses s3 for both project images a LFS files. In order to upload either you'll need to configure [awscli](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)

You'll also need to create an s3 bucket called `wevolver-project-images` ( this can be changed in `resources/projectImage.py`).

# Configure Mailchimp list

 Amazon SES is used to send notification emails. These will be configured with the AWS Keys, but we use Mailchimp to handle news letter sign ups

 1. Sign up for Mailchimp and configure an email list for newsletter signups
 2. Add the associated key to `settings` under `MAILCHIMP_KEY`
