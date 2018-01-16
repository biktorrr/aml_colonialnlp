# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from frog import Frog, FrogOptions
import os
import subprocess
from PIL import Image
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import sys
import pyocr.builders
import csv
from collections import Counter
reload(sys)
sys.setdefaultencoding('utf-8')

frog = Frog(FrogOptions(parser=True))
tools = pyocr.get_available_tools()
directory = '/home/pypdfocr/document5/'
inp = directory + '*.pdf'
out = directory + 'document.png'
filetype = '.png'
tool = tools[0]
langs = tool.get_available_languages()
lang = langs[3]
tgnFile = 'tgnFile.csv'
aatFile = 'aatFile.csv'
entityList = []
countDictionary = {}
conceptList = []
uriList = []
termList = []
persons = []
locations = []

def transformFile(inp, out):
    #OCR - Transforms PDF-file to a set of pre-processed PNG files.
    subprocess.call(['convert', '-density', '600', inp, '-scale', '@1700000', '-colorspace', 'Gray', '-level', '50x100%', out])

def performOCR(directory, filetype):
    #Performs OCR and NER on PNG files to extract persons, locations and AAT concepts.
    if len(tools) == 0:
        print('No OCR tool found')
        sys.exit(1)
    for filename in os.listdir(directory):
        if filename.endswith(filetype):
            txt = tool.image_to_string(
                Image.open(directory.decode() + filename),
                lang = lang,
                builder = pyocr.builders.TextBuilder()
            )
            txt = txt.decode('utf-8')
            output = frog.process(txt)
            for item in output:
                if 'B-PER' in item['ner']:
                    if item['posprob'] > 0.9:
                        if '_' not in item['text'] and len(item['text']) > 3:
                            person = str(item['text'])
                            persons.append(person)
                elif 'B-LOC' in item['ner']:
                    if item['posprob'] > 0.9:
                        if '_' not in item['text'] and len(item['text']) > 3:
                            location = str(item['text'])
                            locations.append(location)
                elif 'I-NP' in item['chunker']:
                    if item['posprob'] > 0.95:
                        entity = item['text']
                        entity = str(entity)
                        if entity.startswith('-') or entity.endswith('-'):
                            entity = entity.replace('-', '')
                        elif entity.isupper():
                            entity = entity.islower()
                        entityList.append(entity)
    return persons, locations, entityList

def countFrequency(entityList):
    #Counts frequently occurring words in list of nouns.
    global countDictionary
    counts = Counter(entityList)
    for key, value in counts.items():
        if value > 2:
            if type(key) == str and len(key) > 4:
                countDictionary[key] = value
    countDict = [(k, countDictionary[k]) for k in sorted(countDictionary, key = countDictionary.get, reverse=True)]
    return countDict

def readCSV(queryFile, conceptRow, uriRow):
    #Reads and processes the TGN and the AAT .CSV files.
    with open(queryFile) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=str(','))
        for row in readCSV:
            aatConcepts = row[conceptRow]
            aatUris = row[uriRow]
            conceptList.append(aatConcepts)
            uriList.append(aatUris)
    return conceptList, uriList

def createEntityDict(entities, conceptList, uriList):
    #Compares the text entities to the Getty entities and puts the matches in a dictionary.
    ind_dict = dict((k,i) for i,k in enumerate(conceptList))
    inter = set(ind_dict).intersection(entities)           
    indices = [ ind_dict[x] for x in inter ]
    for l in indices:
        for m,uris in enumerate(uriList):
            if l == m:
                termList.append(uris)
    entityDict = dict(zip(inter, termList))
    return entityDict

def createPersonsList(personsDict, locationsDict):
    #Puts entities that do not occur in the TGN locations dictionary in a persons list.
    persList = []
    for key in personsDict.keys():
        if key not in locationsDict.keys():
            persList.append(key)
    return persList

def main():
    transformFile(inp, out)
    persons, locations, entityList = performOCR(directory, filetype)
    countDict = countFrequency(entityList)
    conceptList, uriList = readCSV(queryFile=tgnFile, conceptRow=1, uriRow=0)
    aatList, aatUriList = readCSV(queryFile=aatFile, conceptRow=2, uriRow=0)
    personsDict = createEntityDict(persons, conceptList, uriList)
    locationsDict = createEntityDict(locations, conceptList, uriList)
    persList = createPersonsList(personsDict, locationsDict)
    entitiesDict = createEntityDict(entityList, aatList, aatUriList)
    print('Persons: ', persList)
    print('Locations: ', locationsDict)          
    print('Architectural entities: ', entitiesDict)
    print('Frequently occurring words: ', countDict)

if __name__ == '__main__':
    main()



