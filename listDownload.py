#!/usr/bin/python3
# Test normal
# https://www.egr.msu.edu/~khalil/NonlinearSystems/Sample/Lect_ .pdf 1 41 -p 100 -d 1 --quiet
# Test file:
# -i test.txt -o testDir

import os
import platform
import shlex
import sys
import threading
import time
from datetime import datetime

# Personal Lib
from src.ArgParse import *
from src.AtomicInteger import AtomicInteger

# Parametri Facoltativi/Valori di default
pDW = 5  # Prarallel Download
quite = True  # Xterm Support Terminal
fileList = ""
defaultDownloadPath = "./listDownload/"
# Url List
urlListParam = []  # [url, name, savePath]


def helpMan():
    print("correct syntax is:")
    print("listDownload.py <baseUrl> <endUrl> <startNum> <endNum> [Options]")
    print("\tbaseUrl:= First part of the url (until XX number)")
    print("\tendUrl:= Second part of the url (after XX number)")
    print("\tstartNum:= First index included")
    print("\tendNum:= Last index (included)")
    print("[Options]:")
    print("\t\t -p --listDownload <int> Number of concurrency downdload (default = 5)")
    print("\t\t -o --outSave <path> Saving directory Path (default = ./listDownload)")
    print("\t\t -d --digit <digit> Number of digit (default = 2)")
    print("\t\t -q --quiet no show all data")
    print("\t\t -v --verbose show all data by Xterm support Terminal")

    print("\n Is also possible setup multiple download in a File:")
    print("./listDownload.py -i <File List> [Options All]")
    print("[Options All]:")
    print("\t\t -p --listDownload <int> Number of concurrency downdload (default = 5)")
    print("\t\t --quiet no show all data")
    print("\n[File List syntax]:")
    print("For EVERY LINE the syntax MUST be is:")
    print("<baseUrl> <endUrl> <startNum> <endNum> [Options file]")
    print("[Options file] (in case of missing, the global option will be used:")
    print("\t\t -o --outSave <path> Saving directory Path (default = see global)")
    print("\t\t -d --digit <digit> Number of digit (default = see global)")

    print("You type the command:")
    print(sys.argv[1:])  # Press Ctrl+8 to toggle the breakpoint.
    exit(-1)


def urlListInit():
    """
    Make the urlList in base of the command line params
    :return:
    """
    global urlListParam, pDW, quite, fileList

    if "-i" in sys.argv:
        index = sys.argv.index("-i")
        fileList = sys.argv[index + 1]
        subList = sys.argv[1:index] + sys.argv[index + 2:]
        argvListParse = 0
        try:
            argvListParse = ArgListParse(subList)
        except Exception as e:
            print("Oops!", e, "occurred.")
            helpMan()

        # Estraggo i parametri funzionali
        if argvListParse.pDW is not None:
            pDW = argvListParse.pDW
        if argvListParse.quite is not None:
            quite = argvListParse.quite

        with open(fileList, 'r') as file1:
            Lines = file1.readlines()
        list_of_lists = [shlex.split(line) for line in Lines]
        argvParseFile = 0
        for line in list_of_lists:
            try:
                argvParseFile = ArgParse(line, argvListParse.outDir)
            except Exception as e:
                print("Oops!", e, "occurred.")
                print(line)
                helpMan()

        # Estraggo i parametri funzionali
        urlListParam += argvParseFile.urlParam

    else:  # Comando Singolo
        if len(sys.argv) < 5:
            helpMan()

        argvParseTerminal = 0
        try:
            terminalArgv = sys.argv[1:]
            argvParseTerminal = ArgParse(terminalArgv, defaultDownloadPath)
        except Exception as e:
            print("Oops!", e, "occurred.")
            helpMan()

        # Estraggo i parametri funzionali
        urlListParam += argvParseTerminal.urlParam

        if argvParseTerminal.pDW is not None:
            pDW = argvParseTerminal.pDW
        if argvParseTerminal.quite is not None:
            quite = argvParseTerminal.quite


# Thread active counter
tokenActive = AtomicInteger(0)
semActive = threading.Semaphore()


def thread_function(dataList):
    """
    :param dataList: #list: [url, name, savePath]
    :return:
    """
    url = dataList[0]
    name = dataList[1]
    name = name.replace(" ", "_")
    savePath = dataList[2]
    savePath = savePath.replace(" ", "_")
    try:
        os.makedirs(savePath)
    except FileExistsError:
        # Nop all Ok
        pass
    except Exception as e:
        print("[thread_function] makedirs get Error:", e)

    print("\nDownload: " + url + "\n\t Start " + name)
    if platform.system() == "Linux":
        if quite:
            cmd = f"wget {url}" + " --directory-prefix=\"" + savePath + "\"" + " --quiet"
        else:
            cmd = "xterm -e bash -c '" + "wget " + url + " --directory-prefix=\"" + savePath + "\"" + "'"
        # print(cmd)
        os.system(cmd)
    elif platform.system() == "Windows":
        fileName = f"{savePath}/{name}"
        cmd = f"Invoke-WebRequest -Uri {url}" + " -OutFile \"" + fileName + "\""
        # print("powershell.exe " + cmd)
        os.system(f"powershell.exe {cmd}")
    else:
        print("OS not Supported")
    print("\n\t END " + name)

    global tokenActive, semActive
    tokenActive.dec()
    semActive.release()


def main():
    urlListInit()

    print(f"The download start with {str(pDW)} parallel Connection")
    print(
        f"Output quiet = {str(quite)} My Current Work Directory is: {os.getcwd()}"
    )

    # Start parallel procedure
    start_time = datetime.now()

    global tokenActive, semActive
    tokenActive = AtomicInteger()
    semActive = threading.Semaphore(pDW)
    nDownload = 0
    for dwParam in urlListParam:
        semActive.acquire()
        tokenActive.inc()
        t = threading.Thread(target=thread_function, args=(dwParam,))
        t.start()
        nDownload += 1

    while tokenActive.value != 0:
        time.sleep(1)

    time_elapsed = datetime.now() - start_time
    print("## Downloads end ##")
    print(f'Total Time (hh:mm:ss.ms) {time_elapsed}')
    print(f'Mean Time General(hh:mm:ss.ms) {time_elapsed / nDownload}')
    print(f'Mean Time x File (hh:mm:ss.ms) {time_elapsed * pDW / nDownload}')


if __name__ == '__main__':
    main()
