import slackweb
from configparser import ConfigParser


class SlackNotify:
    config = ConfigParser()
    grades = {}

    def __init__(self, config, grades):
        self.config = config
        self.grades = grades

    def sendNotification(self):
        webhook = self.config.get('slack', 'webhookurl')
        username = self.config.get('slack', 'username')
        channel = self.config.get('slack', 'channel')

        gradeAttachments = []

        for grade in self.grades:
            grade_msg = "Module %s, Omschrijving %s\nToetsvorm %s\nToetsdatum %s, Mutatiedatum %s\nResultaat %s" % (
                grade['module'], grade['description'], grade['test_type'],
                grade['date_test'], grade['date_result'], grade['result'],
            )

            msg = {
                "title": grade['module'],
                "text": grade_msg,
                "prkdwn_in": ["text", "pretext"]
            }

            gradeAttachments.append(msg)

        slack = slackweb.Slack(url=webhook)
        slack.notify(text="Osiris update! %d nieuwe cijfers!" % len(gradeAttachments), channel=channel,
                     username=username, attachments=gradeAttachments)
