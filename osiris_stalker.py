# Osiris Stalker (c) Github.com/l0ngestever
import traceback

from bs4 import BeautifulSoup
import ConfigParser
import argparse
import requests
import json
import sys
import os


class Osiris:
    # START DEFAULT VARS
    args = None
    config = None

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
        'gebruikersNaam': '',
        'wachtWoord': '',
        'event': 'login'
    }

    # END OF DEFAULT VARS

    def __init__(self, args, config):
        self.args = args
        self.config = config

        if args.l:
            self.payload['gebruikersNaam'] = args.u
            self.payload['wachtWoord'] = args.p
        elif args.c:
            try:
                self.payload['gebruikersNaam'] = config.get('credentials', 'username')
                self.payload['wachtWoord'] = config.get('credentials', 'password')
            except Exception:
                print "Reading config failed."
                sys.exit(0)
        else:
            print "No valid choice. Exiting."
            sys.exit(0)

    def stalk(self):
        try:
            with requests.Session() as s:
                r = s.get(self.URL_BASE, verify=False)

                # Get first cookie --> Important!
                cookie = {
                    'JSESSIONID': r.cookies['JSESSIONID']
                }

                p = s.post(self.URL_AUTH, headers=self.headers, data=self.payload, cookies=cookie)

                r = s.get(self.URL)
                data = r.text

                soup = BeautifulSoup(data, 'lxml')
                table = soup.find("table", attrs={"class": "OraTableContent"})

                headings = [th.get_text() for th in table.find("tr").find_all("th")]
                datasets = [headings]

                for row in table.find_all("tr")[1:]:
                    dataset = zip(td.get_text() for td in row.find_all("td"))
                    datasets.append(dataset)

                old_results = None
                results = {
                    "course_1": datasets[1][1][0],
                    "grade_1": datasets[1][6][0],
                    "course_2": datasets[2][1][0],
                    "grade_2": datasets[1][6][0]
                }

                try:
                    f_old = open(os.path.join(os.path.realpath(__file__), 'osiris_results.json'), 'r')
                    old_results = json.loads(f_old.read())
                    f_old.close()
                except IOError:
                    pass

                try:
                    result_shared_items = set(old_results.items()) & set(results.items())
                except AttributeError:
                    result_shared_items = []

                if len(result_shared_items) == len(results):
                    print 'No Osiris updates.'
                else:
                    print 'Osiris updates detected!'

                    f = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'osiris_results.json'), 'w')
                    f.write(json.dumps(results, indent=True, sort_keys=False))
                    f.close()

                    msg = "Osiris update! This are the latest two results of Osiris: \n\n"
                    msg += "1: {}: {}\n".format(results['course_1'], results['grade_1'])
                    msg += "2: {}: {}".format(results['course_2'], results['grade_2'])

                    print msg

                    # TODO REWRITE THIS VERY UGLY UGLY MAIL FUNCTION
                    # smtplib or flask-mail?

                    # result_php_mail = subprocess.call(["php", "-f", "/<FULL PATH>/sendMailUpdate.php",
                    #                                    "email@example.com", msg])
                    # print 'result: ' + str(result_php_mail)
        except Exception:
            print "Getting Osiris results failed."
            print traceback.format_exc()
            sys.exit(0)


if __name__ in '__main__':
    parser = argparse.ArgumentParser(description='Osiris stalker (version 1.0)')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', help='Load config file.', action='store')
    group.add_argument('-l', help='Login with credentials [-u / -p required].', action='store_true')

    group = parser.add_argument_group("Login with parameters [-l required]")
    group.add_argument('-u', help='Username of Osiris (without @student.hsleiden.nl).')
    group.add_argument('-p', help='Password of Osiris (hsleiden account).')

    args = parser.parse_args()

    if args.l:
        if args.u is None or args.p is None:
            print "Params [-u / -p] missing."
            sys.exit(0)

    config = None

    if args.c:
        try:
            try:
                config = ConfigParser.ConfigParser()
                config.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), args.c))
            except Exception:
                print "Config cannot be load."
                sys.exit(0)
        except IOError:
            print "Config not found."

    # Everything looks fine. Let's stalk Osiris. :-)

    osiris = Osiris(args, config)
    osiris.stalk()
