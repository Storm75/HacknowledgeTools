#!/usr/bin/python3
import csv
import hashlib
import os
import re
import requests
import sys
import time
from bs4 import BeautifulSoup
from Crypto.Hash import MD5
from selenium import webdriver
from urllib.request import urlparse
from hurry.filesize import size
from concurrent.futures import *
from datetime import datetime

EXTS = ('.zip', '.gz', '.tgz', '.bz2', '.xz', '.dmg')
CSV_FILE = "hash_list.csv"
PLATFORMS = 'platforms'
DOWNLOAD_KEY = "Download"
DOWNLOAD_URL_KEY = "Download\?"

def get_MD5(url):
    chunk_size = 8192
    file_path = hashlib.md5(url.encode('utf-8')).hexdigest() + ".tmp"
    getresponse = requests.get(url, stream=True)
    with open(file_path, 'wb') as f:
        for data in getresponse.iter_content(chunk_size=10008192):
            f.write(data)
    h = MD5.new()
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if len(chunk):
                h.update(chunk)
            else:
                break
        f.close()
    os.remove(file_path)
    return h.hexdigest()

def addToCSV(url, hash):
        with open(CSV_FILE, 'a',newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([url, hash])

def addToDownload(url):
        time.sleep(0.05)
        downloadLinkList.append(url)

def Download(url, i):
    if csvdict.get(url) is None:
        filesize = size(int(requests.head(url).headers['content-length']))
        print (filesize + " " + str(i) + "/" + str(downloadListLength) + " (" + url + ")")
        addToCSV(url, get_MD5(url))
    else:
        print ("Skipped " + str(i) + "/" + str(downloadListLength) + " " + url)
    return

def cleanUrl(url):
    split = url.split("://")
    protocol = split[0]
    cleanedUrl = split[1].replace("//", '/')
    return protocol + "://" + cleanedUrl

def noImg(node):
    child = node.findChild()
    if (child and child.name != "img") or not child:
        return True
    return False

def listFD(url):
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'html.parser')
    subchildfutures = []
    for node in soup.find_all('a'):
        href = node.get('href')
        if node.getText() != "Parent Directory" and href != "/" and not href.startswith("http://") and not href.startswith("https://") and href[0] != "/" and href.endswith('/'):
            if noImg(node):
                cleaned = cleanUrl(url + "/" + node.get('href'))
                with ThreadPoolExecutor(max_workers=100) as subchildexecutor:
                    subchildfutures.append(subchildexecutor.submit(listFD, cleaned))

        elif href.endswith(EXTS):
            if noImg(node):
                addToDownload(url + node.get('href'))
    #wait(subchildfutures)
    return True

def getHrefs(driver, src=False, verbose=False):
    ret = []
    if src: hrefs = driver.find_elements_by_xpath("//*[@href or @src]")
    else: hrefs = driver.find_elements_by_xpath("//*[@href]")
    for elem in hrefs:
        infohref = "[" + elem.text + "] " + elem.get_attribute("href")
        tuplehref = (elem.text, elem.get_attribute("href"))
        ret.append(tuplehref)
        if verbose:
            print (infohref)
    if verbose:
        print ("[******************************************************]")
    return ret

def diffHrefs(oldHref, newHref, verbose=False):
    for old in oldHref:
        for new in newHref:
            if old[1] == new[1]:
                newHref.remove(new)
    if verbose:
        for href in newHref:
            print ("[" + href[0] + "] " + href[1])
    return newHref

def findDownloadLink(hrefList, url_key):
    for elem in hrefList:
        if re.search(url_key, elem[1]):
            addToDownload(elem[1])

def getDownloadableFiles(url, soup):
    found = []
    base_url = urlparse(url)
    for node in soup.find_all('a'):
        href = node.get('href')
        if href:
            urlparsed = urlparse(href)
            if urlparsed.path.endswith(EXTS):
                if href.startswith("/"):
                    found.append(base_url.scheme + "://" + base_url.netloc + href)
    return found

def scrap(url):
    if url[0] == "#" or url == "\n" or url is None:
        return "Url Skip"
    get_url = requests.get(url)
    print ("Parsing : " + url)
    page = get_url.text
    soup = BeautifulSoup(page, 'html.parser')

    # If the page a directory listing ...
    if soup.title and re.search("Index of ", soup.title.string, re.IGNORECASE):
        listFD(url)
    # If the page is Github repo
    elif urlparse(url).netloc == "api.github.com":
        json = get_url.json()
        for tag in json:
            addToDownload(tag["zipball_url"])
            addToDownload(tag["tarball_url"])
    else:
        found = getDownloadableFiles(url, soup)
        if not found:
            #TODO Should be static scrapping, not with selenium webdriver
            driver = webdriver.PhantomJS(executable_path='./phantomjs64', service_log_path=os.path.devnull)
            driver.get(url)
            inithrefs = getHrefs(driver)
            findDownloadLink(inithrefs, DOWNLOAD_URL_KEY)
            named_divs = driver.find_elements_by_xpath("//div[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'" + urlparse(url).path.split('/')[1].lower() + "')]")
            for webElem in named_divs:
                webElem.click()
            diffHrefs(inithrefs, getHrefs(driver))
            platforms = driver.find_elements_by_xpath("//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'" + PLATFORMS + "')]")
            for webElem in platforms:
                webElem.click()
            lastHrefs = diffHrefs(inithrefs, getHrefs(driver))
            for elem in lastHrefs:
                if re.search(DOWNLOAD_KEY, elem[0], re.IGNORECASE):
                    addToDownload(elem[1])
            driver.quit()
        else:
            for href in found:
                addToDownload(href)
        return "finish"
    return True

startTime = datetime.now()
downloadLinkList = []

try:
    for item in os.listdir():
        if item.endswith(".tmp"):
            os.remove(item)
    fdlink = open('links.txt')
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(scrap, link.rstrip('\n')) for link in fdlink.readlines()]
    #wait(futures)
    afterScrapTime = datetime.now()
    deltaTime = afterScrapTime - startTime
    seconds = float(deltaTime.total_seconds())
    print ("Finished web scrapping in " + str(seconds) + " seconds.\nStart downloading " + str(len(downloadLinkList)) + " files.")
    downloadListLength = len(downloadLinkList)
   
    if not os.path.exists(CSV_FILE):
           open(CSV_FILE, 'x').close() 

    with open(CSV_FILE, mode='r') as infile:
        reader = csv.reader(infile)
        csvdict = {rows[0]: rows[1] for rows in reader}
    with ThreadPoolExecutor(max_workers=30) as executor:
            futures = [executor.submit(Download, url, i + 1) for i,url in enumerate(downloadLinkList)]
    #        wait(futures)
    sys.exit(0)
except (KeyboardInterrupt, SystemExit):
    sys.exit(1)
