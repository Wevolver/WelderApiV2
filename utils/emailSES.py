import boto3

# This address must be verified with Amazon SES.
SENDER = "Welder Notification <info@mail.wevolver.com>"
AWS_REGION = "eu-west-1"
SUBJECT = "Welder - You were invited to the project {}"

# The email body for recipients with non-HTML email clients.
BODY_TEXT = ("Hi, you were invited to the project: {}, join the project on {} Welder now!")

with open("utils/partials/project-invite.html", "r") as html:
    with open("utils/partials/style.html", "r") as css:
        BODY_CSS = css.read()
        BODY_HTML = html.read()


CHARSET = "UTF-8"
client = boto3.client('ses',region_name=AWS_REGION)

def sendInviteMemberEmail(recipient, project_name, user_slug, slug):
    project_url = "https://www.welder.app/{}/{}".format(user_slug, slug)
    try:
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    recipient,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML.format(BODY_CSS, project_url, project_name),
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT.format(project_name, project_url),
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT.format(project_name),
                },
            },
            Source=SENDER,
        )
    except Exception as e:
        print(e)
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
