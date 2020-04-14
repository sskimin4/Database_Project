#-*- coding: utf-8 -*-

import datetime
import time
import sys
import MeCab
import operator
from pymongo import MongoClient
from bson import ObjectId
from itertools import combinations

DBname = "db20161584"
conn = MongoClient('dbpurple.sogang.ac.kr')
db = conn[DBname]
db.authenticate(DBname,DBname)
stop_word= {}
def printMenu():
    print "0. CopyData"
    print "1. Morph"
    print "2. print morphs"
    print "3. print wordset"
    print "4. frequent item set"
    print "5. association rule"

def make_stop_word():
    f=open("wordList.txt",'r')
    while True:
        line = f.readline()
        if not line: break
        stop_word[line.strip('\n')] = line.strip('\n')
    f.close()

def morphing(content):
    t=MeCab.Tagger('-d/usr/local/lib/mecab/dic/mecab-ko-dic')
    nodes=t.parseToNode(content.encode('utf-8'))
    MorpList = []
    while nodes:
        if nodes.feature[0] == 'N' and nodes.feature[1] == 'N':
            w=nodes.surface
            if not w in stop_word:
                try:
                    w=w.encode('utf-8')
                    MorpList.append(w)
                except:
                    pass
        nodes = nodes.next
    return MorpList
def p0():
    col1 =db['news']
    col2=db['news_freq']

    col2.drop()

    for doc in col1.find():
        contentDic={}
        for key in doc.keys():
            if key != "_id":
                contentDic[key] = doc[key]
        col2.insert(contentDic)

def p1():
    for doc in db['news_freq'].find():
        doc['morph'] = morphing(doc['content'])
        db['news_freq'].update({"_id":doc['_id']},doc)
def p2(url):
    collect = db['news_freq']
    for doccu in collect.find({"url":url}):
        for x in doccu['morph']:
            print x
def p3():
    col1=db['news_freq']
    col2 = db['news_wordset']
    col2.drop()
    for doc in col1.find():
        new_doc ={}
        new_set=set()
        for w in doc['morph']:
            new_set.add(w.encode('utf-8'))
        new_doc['word_set']=list(new_set)
        new_doc['url']=doc['url']
        col2.insert(new_doc)
def p4(url):
    collect = db['news_wordset']
    for doccu in collect.find({"url":url}):
        for x in doccu['word_set']:
            print x
def p5(length):
    d = dict()
    col1 = db['news_wordset']
    if length == 1:
        realcol1 = db['candidate_L1']
        realcol1.drop()
        for doc in col1.find():
            for word in doc['word_set']:
                if word not in d.keys():
                    d[word] = 1
                else: 
                    d[word]+=1

        for i in d.keys():
            if d.get(i) < 100 * 0.1:
                d.pop(i)
            else:
                realcol1.insert({"item_set" : i, "support" : d.get(i)})
    elif length == 2:
        realcol2 = db['candidate_L2']
        realcol2.drop()
        temp = db['candidate_L1']
        item_case = []
        real_case = []
        i=0
        for doc in temp.find():
            j=0
            for doc2 in temp.find():
                if j > i:
                    real_case.append(doc2['item_set'])
                    real_case.append(doc['item_set'])
                    item_case.append(real_case)
                    real_case = []
                j+=1
            i+=1
        length = len(item_case)
        for i in range(0,length):
            for doc in col1.find():
                if item_case[i][0] in doc['word_set']:
                    if item_case[i][1] in doc['word_set']:
                        if frozenset(item_case[i]) not in d.keys():
                            d[frozenset(item_case[i])] = 1
                        else:  
                            d[frozenset(item_case[i])] += 1
                    else:
                        continue
                else:
                    continue
        for i in d.keys():
            if d.get(i) < 100 * 0.1:
                d.pop(i)
            else:
                 realcol2.insert({"item_set" : list(i), "support" : d.get(i)})
    elif length == 3:
        realcol3 = db['candidate_L3']
        realcol3.drop()
        temp = db['candidate_L2']
        item_case = []
        real_case = []
        i=0
        for doc in temp.find():
            j=0
            for doc2 in temp.find():
                if j > i:
                    if doc['item_set'][1] != doc2['item_set'][1]:
                        if doc['item_set'][0] == doc2['item_set'][0]:
                            real_case.append(doc['item_set'][0])
                            real_case.append(doc['item_set'][1])
                            real_case.append(doc2['item_set'][1])
                            item_case.append(real_case)
                            real_case=[]
                j+=1
            i+=1
        length = len(item_case)
        for i in range(0,length):
            for doc in col1.find():
                if item_case[i][0] in doc['word_set']:
                    if item_case[i][1] in doc['word_set']:
                        if item_case[i][2] in doc['word_set']:
                            if frozenset(item_case[i]) not in d.keys():
                                d[frozenset(item_case[i])] = 1
                            else:
                                d[frozenset(item_case[i])] += 1
                        else:
                             continue
                    else:
                        continue
                else:
                    continue
        for i in d.keys():
            if d.get(i) < 100 * 0.1:
                d.pop(i)
            else:
                realcol3.insert({"item_set" : list(i), "support" : d.get(i)})

def p6(length):
    min_conf= 0.5
    d1= dict()
    d2= dict()
    d3= dict()
    temp1=db['candidate_L1']
    temp2=db['candidate_L2']
    temp3=db['candidate_L3']
    for doc in temp1.find():
        d1[doc['item_set']]= float(doc['support'])
    for doc in temp2.find():
        d2[frozenset(doc['item_set'])]= float(doc['support'])
    for doc in temp3.find():
        d3[frozenset(doc['item_set'])]= float(doc['support'])
    if length == 2:
        for doc in temp2.find():
            chance1 = d2.get(frozenset(doc['item_set']))/d1.get(doc['item_set'][0])
            chance2 = d2.get(frozenset(doc['item_set']))/d1.get(doc['item_set'][1])
            if chance1 > 0.5:
                print doc['item_set'][0] + ' => ' + doc['item_set'][1] + '    ' + str(chance1)
            if chance2 > 0.5:
                print doc['item_set'][1] + ' => ' + doc['item_set'][0] + '    ' + str(chance2)
    if length == 3:
        for doc in temp3.find():
            chance1 = d3.get(frozenset(doc['item_set']))/d1.get(doc['item_set'][0])
            chance2 = d3.get(frozenset(doc['item_set']))/d1.get(doc['item_set'][1])
            chance3 = d3.get(frozenset(doc['item_set']))/d1.get(doc['item_set'][2])
            chance4 = d3.get(frozenset(doc['item_set']))/d2.get(frozenset([doc['item_set'][0],doc['item_set'][1]]))
            chance5 = d3.get(frozenset(doc['item_set']))/d2.get(frozenset([doc['item_set'][1],doc['item_set'][2]]))
            chance6 = d3.get(frozenset(doc['item_set']))/d2.get(frozenset([doc['item_set'][0],doc['item_set'][2]]))

            if chance1 > 0.5:
                print doc['item_set'][0] + ' => ' + doc['item_set'][1] + ' ,' + doc['item_set'][2] +'    ' + str(chance1)
            if chance2 > 0.5:
                print doc['item_set'][1] + ' => ' + doc['item_set'][0] + ' ,' + doc['item_set'][2]+'    ' + str(chance2)
            if chance3 > 0.5:
                print doc['item_set'][2] + ' => ' + doc['item_set'][0] + ' ,' + doc['item_set'][1]+'    ' + str(chance3)
            if chance4 > 0.5:
                print doc['item_set'][0] + ' ,'+ doc['item_set'][1] + ' => '+ doc['item_set'][2] + '    ' + str(chance4)
            if chance5 >0.5:
                print doc['item_set'][1] + ' ,'+ doc['item_set'][2] + ' => '+ doc['item_set'][0] + '    ' + str(chance5)
            if chance6 > 0.5:
                print doc['item_set'][0] + ' ,'+ doc['item_set'][2] + ' => '+ doc['item_set'][1] + '    ' + str(chance6)

if __name__== "__main__":
    make_stop_word()
    printMenu()
    selector = input()
    if selector == 0:
        p0()
    elif selector ==1:
        p1()
        p3()
    elif selector ==2:
        url =str(raw_input("input news url:"))
        p2(url)
    elif selector ==3:
        url =str(raw_input("input news url:"))
        p4(url)
    elif selector ==4:
        length = int(raw_input("input length of the frequent item:"))
        p5(length)
    elif selector==5:
        length=int(raw_input("input length of the frequent item:"))
        p6(length)


