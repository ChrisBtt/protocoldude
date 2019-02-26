#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# possible input mail adresses:
#     ${internal}          => internal@mathphys.stura.uni-heidelberg.de
#     ${external@some.com} => external@some.com
#     ${external@some.com Some Name} => external@some.com
#     ${Some Name external@some.com} => external@some.com

import argparse
import numpy as np
import subprocess
import sys
import ldap
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import getpass

def check_path(path: str) -> bool:
    """checks the input file name for a valid date and type .txt"""
    year = path[0:4].isnumeric()
    month = path[5:7].isnumeric()
    date = path[8:9].isnumeric()
    name = year and month and date and path[4] is '-' and path[7] is '-'

    if '.txt' in path and name:
        return True
    else:
        raise Exception('Der Dateipfad führt nicht zu einem Sitzungsprotokoll!')
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
            else: self.protocol[top.start+1] = "TOP " + top.number + ": " + self.protocol[top.start+1,5:]
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
            login = input('URZ ID für den Mailversand: ')
            server.login(login, getpass.getpass(prompt='Passwort für deinen Mail-Account: '))
            fromaddr = getpass.getuser()
            for top in self.tops:
                top.send_mail(server, self.protocol)
            server.quit()
            self.mails = True
            print("Alle Mails wurden erfolgreich verschickt. \n")
        except:
            print("Mails konnten nicht verschickt werden. Hast du die richtigen Anmeldedaten eingegeben?")
            pass

    def write_success(self):
        if self.mails:
            self.protocol.insert(0, ":Protocoldude: Mails versandt @ 16:39:57 Uhr, 19.01.2018")
            self.protocol.insert(1, "\n")

        with open(self.path, 'w') as file:
            file.write('\n'.join(self.protocol) + '\n')
        subprocess.call(['svn add', '{}'.format(self.path)])
        subprocess.call(['svn commit', '-m', '"Protokoll der gemeinsamen Sitzung hinzugefügt"')
        print("Protokoll bearbeitet und in den Sumpf geschrieben.")


class TOP(Protocol): # inherit from "object"
    """Separates the several TOPs out of one protocol and provides different functions to further process the sections"""

    def __init__(self, number: int, start: int, end: int):
        self.number = number
        self.start = start
        self.end = end # only at first because of of missing information
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
        # print(self.users)
        # print(extract_mails(ldap_search(self.users)))
        # print(list_mails(self.users))
        if extract_mails(ldap_search(self.users)) is not None:
            self.mails = extract_mails(ldap_search(self.users))
            if list_mails(self.users):
                self.mails.append(list_mails(self.users))

        if list_mails(self.users):
            self.mails = list_mails(self.users)

        # for user in users[0]:
        #     for mail in mails:
        #     if (user in mail.split('@'))
    def send_mail(self, server, protocol):
        for user,mail in zip(self.users,self.mails):
            fromaddr = user

            msg = MIMEMultipart()
            msg['From'] = fromaddr
            msg['To'] = mail
            msg['Subject'] = "Gemeinsame Sitzung: {}".format(protocol[self.start+1])

            body = "Hallo {},\n\nDu sollst über irgendwas informiert werden. Im Sitzungsprotokoll steht dazu folgendes:\n\n{}\n\n\nViele Grüße, Dein SPAM-Skript.".format(user, '\n'.join(protocol[self.start:self.end])+'\n')
            # \n\nSollte der Text abgeschnitten sein, schaue bitte im Sitzungsprotokoll nach (Zeile #{tops[i]} – MathPhys Login notwendig).\n#{url}/#{file}\" | mail -a \"Reply-To: #{$replyto}\" -a \"Content-Type: text/plain; charset=UTF-8\" -s \"#{$subject}: #{title} (#{date})\" '#{mail}';", false) unless $debug
            # body = '\n'.join(body) + '\n'
            msg.attach(MIMEText(body, 'plain'))

            text = msg.as_string()
            server.sendmail(fromaddr, toaddr, text)

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

def list_mails(names: list) -> list:
    # define common mail lists
    users = np.array(["fachschaft", "liebe Fachschaft"])
    users = np.vstack([users, ["flachschaft", "liebe Fachschaft"]])
    users = np.vstack([users, ["bernd", "liebe Fachschaft"]])
    users = np.vstack([users, ["fsinformatik", "liebe Fachschaft"]])
    users = np.vstack([users, ["fsphysik", "liebe Fachschaft"]])
    users = np.vstack([users, ["fsmathematik", "liebe Fachschaft"]])
    users = np.vstack([users, ["fsmathinf", "liebe Fachschaft"]])
    users = np.vstack([users, ["infostudkom", "liebes Mitglied der Studienkommission Informatik"]])
    users = np.vstack([users, ["tistudkom", "liebes Mitglied der Studkom TI"]])
    users = np.vstack([users, ["mathstudkom", "liebe MathStudKomLerInnen"]])
    users = np.vstack([users, ["mathestudkom", "liebe MathStudKomLerInnen"]])
    users = np.vstack([users, ["physstudkom", "liebe Mitglied der Studkom Physik"]])
    users = np.vstack([users, ["physikstudkom", "liebe Mitglied der Studkom Physik"]])
    users = np.vstack([users, ["studkomphysik", "liebe Mitglied der Studkom Physik"]])
    users = np.vstack([users, ["scstudkom", "liebe Mitglied der Studkom SciCom"]])
    users = np.vstack([users, ["mathfakrat", "liebes Mitglied des MatheInfo-Fakrats"]])
    users = np.vstack([users, ["fakratmathinf", "liebes Mitglied des MatheInfo-Fakrats"]])
    users = np.vstack([users, ["physfakrat", "liebes Mitglied des Physik-Fakrats"]])
    users = np.vstack([users, ["fakratphys", "liebes Mitglied des Physik-Fakrats"]])
    users = np.vstack([users, ["fakratphysik", "liebes Mitglied des Physik-Fakrats"]])
    users = np.vstack([users, ["akfest", "liebes Mitglied der AK-Fest Liste"]])

    mails = []
    for name in names:
        if name in users[:,0]:
            mails.append(name + "@mathphys.stura.uni-heidelberg.de")
    return mails

## check system 'Fachschaftsserver'
#output = subprocess.check_output(["uname", "-n"]).decode("utf-8")
#
#if ('fsmath' not in output):
#    raise Exception("Im Moment funktioniert das Skript nur auf dem Fachschaftsserver. Versuch es da nochmal.")

#def check_user(user):
#    output = subprocess.check_output(["ls", "-1", "/home"]).decode("utf-8")
#    while (user not in output and user not in users[:,0]):
#        print('Benutzername nicht gefunden.')
#        if (input('Soll die Mail an wen anderes verschickt werden? [y/n]') is 'y'):
#            user = input('Dann gib jetzt den Emüfänger ein: ')
#        else:
#            print("E-Mail wird übersprungen. Versuch's später nochmal mit mehr Enthusiasmus")
#            return False
#    print('Benutzer {} gefunden'.format(user))
#    return user


if __name__ == "__main__":

    MATHPHYS_LDAP_ADDRESS = "ldap1.mathphys.stura.uni-heidelberg.de"
    MATHPHYS_LDAP_BASE_DN = "ou=People,dc=mathphys,dc=stura,dc=uni-heidelberg,dc=de"

    # login = getpass.getuser()
    # password = getpass.getpass(prompt='Passwort für deinen Mail-Account: ')
    # print(login)
    # print(password)

    # disables error messages
    sys.tracebacklimit = 0

    parser = argparse.ArgumentParser()
    parser.add_argument("infile", metavar="[path/to/file]", type=argparse.FileType('r'))
    args = parser.parse_args()

    check_path(path=args.infile.name)
    protocol = Protocol(path=args.infile.name)
    protocol.get_tops()
    protocol.get_users()
    for top in protocol.tops:
        print("Start: {}".format(top.start))
        print(top.users)
        print(top.mails)
        print("Ende: {}".format(top.end))

    protocol.rename_title()
    # protocol.send_mails()
    protocol.write_success()


    # print(mails)
