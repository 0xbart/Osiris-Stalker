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
        for grade in self.grades.items():
            attachmenttext = (str(grade[1][1]['omschrijving']) + "\n"
                             "Toetsvorm: " + str(grade[1][1]['toetsvorm']) + "\n"
                             "Toetsdatum: " + str(grade[1][1]['toetsdatum']) + "\n"
                             "Mutatiedatum: " + str(grade[1][1]['mutatiedatum']) + "\n"
                             "Resultaat: " + str(grade[1][1]['resultaat']) + "\n")
            attachment = {"title": grade[1][1]['module'],
                          "text": attachmenttext,
                          "prkdwn_in": ["text","pretext"]}
            gradeAttachments.append(attachment)

        slack = slackweb.Slack(url=webhook)
        slack.notify(text="Osiris UPDATE!",
                     channel=channel,
                     username=username,
                     attachments=gradeAttachments)