# Osiris Stalker (c) Github.com/l0ngestever

import configparser
import traceback
import argparse
import requests
import logging
import json
import sys
import os

from bs4 import BeautifulSoup
from notifiers.slack import SlackNotify
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base


db_path = '%s//sqlite.db' % os.path.join(os.path.dirname(os.path.realpath(__file__)))
base = declarative_base()
engine = create_engine('sqlite:///%s' % db_path)


class Grade(base):
    __tablename__ = 'grade'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date_test = Column(String, nullable=True)
    date_result = Column(String, nullable=True)
    module = Column(String, nullable=True)
    description = Column(String, nullable=True)
    weighting = Column(String, nullable=True)
    result = Column(String, nullable=True)

    def __init__(self, date_test=None, date_result=None, module=None, description=None, weighting=None, result=None):
        self.date_test = date_test
        self.date_result = date_result
        self.module = module
        self.description = description
        self.weighting = weighting
        self.result = result

    def __repr__(self):
        return "<Grade(id='%d', date_test='%s', date_result='%s', module='%s', weighting='%s', result='%s')>" % (
            self.id, self.date_test, self.date_result, self.module, self.weighting, self.result)


class Osiris:

    # START DEFAULT VARS

    args = None
    config = None

    logger = logging.getLogger('Osiris-Stalker')
    logger.setLevel(logging.DEBUG)

    URL_BASE = 'https://studievolg.hsleiden.nl/student/Personalia.do'
    URL_AUTH = 'https://studievolg.hsleiden.nl/student/AuthenticateUser.do'
    URL = 'https://studievolg.hsleiden.nl/student/ToonResultaten.do'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:39.0) Gecko/20100101 Firefox/39.0'
    }

    payload = {
        'startUrl': 'Personalia.do',
        'inPortal': '',
        'callDirect': '',
        'requestToken': '',
        'VB_gebruikersNaam': '',
        'VB_wachtWoord': '',
        'event': 'login'
    }

    # END OF DEFAULT VARS

    def __init__(self, args, config):
        self.args = args
        self.config = config

        if args.l:
            self.payload['VB_gebruikersNaam'] = args.u
            self.payload['VB_wachtWoord'] = args.p
        elif args.c:
            try:
                self.payload['VB_gebruikersNaam'] = config.get('credentials', 'username')
                self.payload['VB_wachtWoord'] = config.get('credentials', 'password')
            except Exception:
                logging.critical("Reading config failed.")
                logging.critical(traceback.format_exc())
                sys.exit(1)
        else:
            logging.critical("No valid choice. Exiting.")
            sys.exit(1)

    def getGrades(self):
        try:
            with requests.Session() as s:
                r = s.get(self.URL_BASE, headers=self.headers, verify=False)

                # extract request token
                soup = BeautifulSoup(str(r.text), 'lxml')
                requesttoken = soup.find("input", type="hidden", id="requestToken")

                # Put request token in payload
                self.payload['requestToken'] = requesttoken.attrs['value']

                p = s.post(self.URL_AUTH, headers=self.headers, data=self.payload)

                r = s.get(self.URL)
                data = r.text

                soup = BeautifulSoup(data, 'lxml')
                table = soup.find("table", attrs={"class": "OraTableContent"})

                headings = [th.get_text() for th in table.find("tr").find_all("th")]
                datasets = [headings]

                allgrades = {}
                grades_done = 0
                for row in table.find_all("tr")[1:]:
                    allgrades[grades_done] = {
                        "toetsdatum": row.contents[0].text,
                        "module": row.contents[1].text,
                        "omschrijving": row.contents[2].text,
                        "toetsvorm": row.contents[3].text,
                        "weging": row.contents[4].text,
                        "resultaat": row.contents[6].text,
                        "mutatiedatum": row.contents[8].text
                    }
                    grades_done += 1
                return allgrades
        except Exception:
            logging.critical("Unhandled exception! Trowing traceback.")
            logging.critical(traceback.format_exc())
            sys.exit(1)

    def compareChanges(self, newGrades):
        oldGrades = False

        try:
            # Load old grades, if available
            try:
                oldGradesfile = open(os.path.join(os.getcwd(), "storage/osiris_results.json"), "r")
                oldGrades = json.loads(oldGradesfile.read())
                oldGradesfile.close()
            except IOError:
                oldGrades = {0: {
                        "toetsdatum": "",
                        "module": "",
                        "omschrijving": "",
                        "toetsvorm": "",
                        "weging": "",
                        "resultaat": "",
                        "mutatiedatum": ""
                }}
                pass

            # Compare each new grade with presence in old grades
            try:
                reallyNewGrades = {}
                if not oldGrades:
                    return newGrades
                for newGrade in newGrades.items():
                    change = True
                    for oldGrade in oldGrades.items():
                        if newGrade[1]['mutatiedatum'] == oldGrade[1]['mutatiedatum'] \
                                and newGrade[1]['module'] == oldGrade[1]['module'] \
                                and newGrade[1]['resultaat'] == oldGrade[1]['resultaat'] \
                                and newGrade[1]['toetsvorm'] == oldGrade[1]['toetsvorm']:
                            change = False
                    if change:
                        reallyNewGrades[reallyNewGrades.__len__() + 1] = newGrade

                if reallyNewGrades != {}:
                    return reallyNewGrades
                else:
                    return False
            except Exception:
                logging.critical("Unhandled exception! Trowing traceback.")
                logging.critical(traceback.format_exc())
                sys.exit(1)

        except Exception:
            logging.critical("Unhandled exception! Trowing traceback.")
            logging.critical(traceback.format_exc())
            sys.exit(1)

    def sendNotifications(self, gradesToSend):
        # Notify via slack if allowed
        if config.get('slack', 'enabled') == "True":
            SlackNotify(config, gradesToSend).sendNotification()

    def writeGrades(self, gradesToStore):
        with open(os.path.join(os.getcwd(), "storage/osiris_results.json"), "w") as f:
            f.write(json.dumps(gradesToStore))

    def stalk(self):
        try:
            results = self.getGrades()

            oldresults = self.compareChanges(results)

            if oldresults:
                logging.info("New grades detected!")
                self.sendNotifications(oldresults)
                self.writeGrades(results)
            else:
                logging.info("No new grades found")
        except Exception:
            logging.critical("Getting Osiris results failed.")
            logging.critical(traceback.format_exc())
            sys.exit(1)


if __name__ in '__main__':
    parser = argparse.ArgumentParser(description='Osiris stalker (version 1.0)')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', help='Load config file.', action='store')
    group.add_argument('-l', help='Login with credentials [-u / -p required].', action='store_true')

    group = parser.add_argument_group("Login with parameters [-l required]")
    group.add_argument('-u', help='Username of Osiris (without @student.hsleiden.nl).')
    group.add_argument('-p', help='Password of Osiris (hsleiden account).')

    parser.add_argument('--create-database', help='Create database. Note: only if not exists.', action='store_true')

    args = parser.parse_args()

    if args.create_database:
        if not os.path.exists(db_path):
            base.metadata.create_all(engine)
        else:
            logging.warning("Database exists! Please delete the old one.")

    if args.l:
        if args.u is None or args.p is None:
            logging.critical("Params [-u / -p] missing.")
            sys.exit(0)

    config = None

    if args.c:
        try:
            try:
                config = configparser.ConfigParser()
                config.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), args.c))
            except Exception:
                logging.critical("Config cannot be load.")
                sys.exit(1)
        except IOError:
            logging.critical("Config not found.")
            sys.exit(1)

    # Everything looks fine. Let's stalk Osiris. :-)

    osiris = Osiris(args, config)
    osiris.stalk()
