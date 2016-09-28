import slackweb
from configparser import ConfigParser

class SlackNotify:
    config = ConfigParser()
    webhook = ""
    username = ""
    channel = ""
    slack = ""

    def __init__(self, config):
        try:
            self.config = config
            self.webhook = self.config.get('slack', 'webhookurl')
            self.username = self.config.get('slack', 'username')
            self.channel = self.config.get('slack', 'channel')
            self.slack = slackweb.Slack(url=self.webhook)
        except Exception:
            raise NotImplementedError

    def checkenabled(self):
        if self.config.get('slack', 'enabled') == "True":
            return True
        return False

    def sendgrades(self, grades):
        grade_attachments = []
        for grade in grades.items():
            attachmenttext = (str(grade[1][1]['omschrijving']) + "\n"
                             "Toetsvorm: " + str(grade[1][1]['toetsvorm']) + "\n"
                             "Toetsdatum: " + str(grade[1][1]['toetsdatum']) + "\n"
                             "Mutatiedatum: " + str(grade[1][1]['mutatiedatum']) + "\n"
                             "Resultaat: " + str(grade[1][1]['resultaat']) + "\n")
            attachment = {"title": grade[1][1]['module'],
                          "text": attachmenttext,
                          "mrkdwn_in": ["text","pretext"]}
            grade_attachments.append(attachment)

        self.slack.notify(text="Osiris UPDATE!",
                          channel=self.channel,
                          username=self.username,
                          attachments=grade_attachments)
        return True

    def senderror(self, errormessage):
        self.slack.notify(text="Error in Osiris-Stalker!\n" + errormessage,
                          channel=self.channel,
                          username=self.username)
        return True