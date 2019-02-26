#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# possible input mail adresses:
#     ${internal}          => internal@mathphys.stura.uni-heidelberg.de
#     ${external@some.com} => external@some.com
#     ${external@some.com Some Name} => external@some.com
#     ${Some Name external@some.com} => external@some.com

import argparse
import datetime
import subprocess
import sys
import ldap
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import getpass

# define common mail lists
list_users = [["fachschaft", "Liebe Fachschaft"]]
list_users.append(["flachschaft", "Liebe Fachschaft"])
list_users.append(["bernd", "Liebe Fachschaft"])
list_users.append(["fsinformatik", "Liebe Fachschaft"])
list_users.append(["fsphysik", "Liebe Fachschaft"])
list_users.append(["fsmathematik", "Liebe Fachschaft"])
list_users.append(["fsmathinf", "Liebe Fachschaft"])
list_users.append(["infostudkom", "Liebes Mitglied der Studienkommission Informatik"])
list_users.append(["tistudkom", "Liebes Mitglied der Studkom TI"])
list_users.append(["mathstudkom", "Liebe MathStudKomLerInnen"])
list_users.append(["mathestudkom", "Liebe MathStudKomLerInnen"])
list_users.append(["physstudkom", "Liebe Mitglied der Studkom Physik"])
list_users.append(["physikstudkom", "Liebe Mitglied der Studkom Physik"])
list_users.append(["studkomphysik", "Liebe Mitglied der Studkom Physik"])
list_users.append(["scstudkom", "Liebe Mitglied der Studkom SciCom"])
list_users.append(["mathfakrat", "Liebes Mitglied des MatheInfo-Fakrats"])
list_users.append(["fakratmathinf", "Liebes Mitglied des MatheInfo-Fakrats"])
list_users.append(["physfakrat", "Liebes Mitglied des Physik-Fakrats"])
list_users.append(["fakratphys", "Liebes Mitglied des Physik-Fakrats"])
list_users.append(["fakratphysik", "Liebes Mitglied des Physik-Fakrats"])
list_users.append(["akfest", "Liebes Mitglied der AK-Fest Liste"])

def check_path(path: str) -> bool:
    """checks the input file name for a valid date and type .txt"""
    year = path[0:4].isnumeric()
    month = path[5:7].isnumeric()
    date = path[8:9].isnumeric()
    name = year and month and date and path[4] is '-' and path[7] is '-'

    if path.endswith('.txt'):
        return True
    else:
        raise Exception('Der Dateipfad führt nicht zu einem Sitzungsprotokoll oder du schaust besser nochmal über den Filenamen!')
        return False

class Protocol(object):
    """reads in the protocol and processes it"""
    def __init__(self, path):
        # validate filename as protocol (yyyy-mm-dd) and .txt
        self.path = path

        print('\nProtokoll "{}" wird bearbeitet .. \n \n'.format(self.path))

        with open(self.path, 'r') as file:
            self.protocol = file.read().splitlines()
        self.tops = []
        self.mails = False

    def get_tops(self):
        """separate the given protocol in several TOPs from '===' to '==='"""
        for i, line in enumerate(self.protocol):
            # check for TOP title
            if line.startswith("===") and self.protocol[i+2].startswith("==="):
                end = self.protocol[i+3:].index("===")+i+2 if (line in self.protocol[i+3:]) else len(self.protocol)-1
                top = TOP(len(self.tops)+1, i, end)
                self.tops.append(top)

    def rename_title(self):
        """Adjust TOP title type setting"""
        for top in self.tops:
            if not self.protocol[top.start+1].startswith("TOP: "): self.protocol[top.start+1] = "TOP " + str(top.number) + ": " + self.protocol[top.start+1]
            else: self.protocol[top.start+1] = self.protocol[top.start+1][:3] + str(top.number) + " " + self.protocol[top.start+1][3:]
            length = len(self.protocol[top.start+1])
            self.protocol[top.start+2] = "="*length
            self.protocol[top.start] = "="*length

    def get_users(self):
        for top in self.tops:
            top.get_user(self.protocol)
            top.get_mails()

    def send_mails(self):
        try:
            server = smtplib.SMTP("mail.urz.uni-heidelberg.de", 587)
            login = input('Uni ID für den Mailversand: ')
            server.login(login, getpass.getpass(prompt='Passwort für deinen Uni Account: '))   

            for top in self.tops:
                top.send_mail(server, self.protocol)
            server.quit()
            self.mails = True
            print("\nAlle Mails wurden erfolgreich verschickt. \n")
        except Exception as e:
            print(e)
            print("\nMails konnten nicht verschickt werden. Hast du die richtigen Anmeldedaten eingegeben?")
            pass

    def write_success(self):
        if self.mails:
            now = datetime.datetime.now()
            self.protocol.insert(0, ":Protocoldude: Mails versandt @ {}".format(now.strftime("%H:%M %d.%m.%Y")))
            self.protocol.insert(1, "\n")

        with open(self.path, 'w') as file:
            file.write('\n'.join(self.protocol) + '\n')
        try:
            subprocess.run(['svn', 'up'], check=True)
            subprocess.run(['svn', 'add', '{}'.format(self.path)], check=True)
            subprocess.run(['svn', 'commit', '-m', '"Protokoll der gemeinsamen Sitzung hinzugefügt"'], check=True)
            print("Protokoll bearbeitet und in den Sumpf geschrieben.\n Für heute hast du's geschafft!")
        except: 
            print("Konnte SVN Update nicht durchführen. \n Das musst Du irgendwie von Hand reparieren mit 'svn cleanup' oder so.")
            print("Das Protokoll wurde trotzdem bearbeitet und gespeichert.")
            pass


class TOP(Protocol):
    """Separates the several TOPs out of one protocol and provides different functions to further process the sections"""

    def __init__(self, number: int, start: int, end: int):
        self.number = number
        self.start = start
        self.end = end
        self.users = []
        self.mails = []

    def get_user(self, protocol: list):
        """searches for all mentioned users in the TOP paragraph"""
# TODO: recognize multiple users in one line
        for line in protocol[self.start:self.end]:
            # check for mail address
            if "${" in line and "}" in line:
                start = line.index("${")
                end = line.index("}")
                user = line[start+2:end]
                self.users.append(user)

        self.users = list(set(self.users)) # remove duplicates

    def get_mails(self):
        if extract_mails(ldap_search(self.users)) is not None:
            self.mails = extract_mails(ldap_search(self.users))

        for user in self.users:
            if user in list_users[:][0]:
                self.mails.append(user + "@mathphys.stura.uni-heidelberg.de")

    def send_mail(self, server, protocol):
        for user,mail in zip(self.users,self.mails):
            fromaddr = "fachschaft@mathphys.stura.uni-heidelberg.de"

            msg = MIMEMultipart()
            msg['From'] = fromaddr
            msg['To'] = mail
            msg['Subject'] = "Gemeinsame Sitzung: {}".format(protocol[self.start+1])

            if user in list_users[:][0]:
                body = list_users[list_users[:][0].index(user)][1] + ",\n\n"
            else:
                body = "Hallo {},\n\n".format(user)
            body += "Du sollst über irgendwas informiert werden. Im Sitzungsprotokoll steht dazu folgendes:\n\n{}\n\n\nViele Grüße, Dein SPAM-Skript.".format('\n'.join(protocol[self.start:self.end])+'\n')
            # \n\nSollte der Text abgeschnitten sein, schaue bitte im Sitzungsprotokoll nach (Zeile #{tops[i]} – MathPhys Login notwendig).\n#{url}/#{file}\" | mail -a \"Reply-To: #{$replyto}\" -a \"Content-Type: text/plain; charset=UTF-8\" -s \"#{$subject}: #{title} (#{date})\" '#{mail}';", false) unless $debug

            msg.attach(MIMEText(body, 'plain'))

            text = msg.as_string()
            server.sendmail(fromaddr, mail, text)

def ldap_search(users: list) -> list:
    """ searches for a list of users in our ldap """
    server = ldap.initialize('ldaps://' + MATHPHYS_LDAP_ADDRESS)
    users = ['(uid={})'.format(user) for user in users]
    query = '(|{})'.format("".join(users))
    query_result = server.search_s(
        MATHPHYS_LDAP_BASE_DN,
        ldap.SCOPE_SUBTREE,
        query
    )
    return query_result

def extract_mails(query: list) -> list:
    """ extract mails from nonempty ldap queries """
    if query:
        mails = []
        for result in query:
            dn = result[0]
            attributes = result[1]
            mails.append(attributes["mail"][0].decode('utf-8'))
        return mails

if __name__ == "__main__":

    MATHPHYS_LDAP_ADDRESS = "ldap1.mathphys.stura.uni-heidelberg.de"
    MATHPHYS_LDAP_BASE_DN = "ou=People,dc=mathphys,dc=stura,dc=uni-heidelberg,dc=de"

    # disables error messages
    sys.tracebacklimit = 0

    # check system 'Fachschaftsserver'
#     output = subprocess.check_output(["uname", "-n"]).decode("utf-8")
#
#     if ('arcadia' not in output or 'blueberry' not in output):
#        raise Exception("Im Moment funktioniert das Skript nur auf dem Fachschaftsserver. Versuch es da nochmal.")
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", metavar="[path/to/file]", type=argparse.FileType('r'))
    args = parser.parse_args()
    check_path(path=args.infile.name)

    protocol = Protocol(path=args.infile.name)
    protocol.get_tops()
    protocol.get_users()
    protocol.rename_title()
    protocol.send_mails()
    protocol.write_success()
