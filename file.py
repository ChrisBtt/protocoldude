#!/usr/bin/env python
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
    year = path[0:4].isnumeric()
    month = path[5:6].isnumeric()
    date = path[7:8].isnumeric()
    name = year and month and data and path[4] is '-' and path[6] is '-'

    if path.endswith('.txt') and name:
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

    def get_tops(self):
        """separate the given protocol in several TOPs from '===' to '==='"""
        for i, line in enumerate(self.protocol):
            # check for TOP title
            if line.startswith("===") and self.protocol[i+2].startswith("==="):
                print(str(i) + line)
                ende = self.protocol[i+3:].index("===")+i+2 if (line in self.protocol[i+3:]) else len(self.protocol)-1
                top = TOP(len(self.tops)+1, i, ende)
                self.tops.append(top)
        print(len(self.tops))

    def rename_title(self):
        """Adjust TOP title type setting"""
        for top in self.tops:
            if not self.protocol[top.start+1].startswith("TOP: "): self.protocol[top.start+1] = "TOP " + str(top.number) + ": " + self.protocol[top.start+1]
            else: self.protocol[top.start+1] = "TOP " + top.number + ": " + self.protocol[top.start+1,5:]
            length = len(self.protocol[top.start+1])
            self.protocol[top.start+2] = "="*length
            self.protocol[top.start] = "="*length


class TOP(Protocol): # inherit from "object"
    """Separates the several TOPs out of one protocol and provides different functions to further process the sections"""

    def __init__(self, number: int, start: int, ende: int):
        self.number = number
        self.start = start
        self.ende = ende # only at first because of of missing information

    def get_user(protocol: list):
        for line in protocol[start:end]:
            # check for mail address
            if "${" in protocol[i]:
                start = protocol[i].index("${")
                end = protocol[i].index("}")
                user = protocol[i][start+2:end]
                j = len(tops[0])-1
                while tops[1][j] > i: j-=1
                users[0].append(user)
                users[2].append(j+1)
        return users

    def rewrite_title(self):
        print("")


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

def list_mails(names: list) -> int:
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



def send_mail(login, password):
    server = smtplib.SMTP("mail.urz.uni-heidelberg.de", 587)

    #Next, log in to the server
    server.login(login, password)

    fromaddr = "chrisb@mathphys.stura.uni-heidelberg.de"
    toaddr = "chris-blattgerste@gmx.de"

    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Python test email"
    body = "Python test mail"
    msg.attach(MIMEText(body, 'plain'))

    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)


def write_success(protocol):
    protocol = ":Protocoldude: Mails versandt @ 16:39:57 Uhr, 19.01.2018\n\n" + protocol

    with open("protokoll_neu.txt","w") as f:
        f.write(protocol)

    return protocol


if __name__ == "__main__":

    # MATHPHYS_LDAP_ADDRESS = "ldap1.mathphys.stura.uni-heidelberg.de"
    # MATHPHYS_LDAP_BASE_DN = "ou=People,dc=mathphys,dc=stura,dc=uni-heidelberg,dc=de"
    #
    # login = getpass.getuser()
    # password = getpass.getpass(prompt='Passwort für deinen Mail-Account: ')
    # print(login)
    # print(password)

    # disables error messages
    sys.tracebacklimit = 0

    parser = argparse.ArgumentParser()
    parser.add_argument("infile", metavar="[path/to/file]", type=argparse.FileType('r'))
    args = parser.parse_args()

    protocol = Protocol(path=args.infile.name)
    protocol.get_tops()
    for top in protocol.tops:
        print("Start: {}".format(top.start))
        print("Ende: {}".format(top.ende))

    protocol.rename_title()
    print('\n'.join(protocol.protocol) + '\n')
    
    # tops = get_tops(protocol)
    # print(tops)
    # users = get_user(protocol, tops)
    # print(users)

    # users_result = ldap_search(users)
    # mails = extract_mails(ldap_search(users[0])) + list_mails(users[0])
    # for user in users[0]:
    #     for mail in mails:
    #     if (user in mail.split('@'))

    # print(mails)

    write_success(protocol)
    with open('protocol_neu.txt', 'w') as file:
        file.write('\n'.join(protocol) + '\n')
