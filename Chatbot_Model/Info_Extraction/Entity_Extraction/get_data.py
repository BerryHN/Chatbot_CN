#-*- coding:utf-8 _*-
"""
@author:charlesXu
@file: get_data.py
@desc: 连接数据库
@time: 2018/08/08
"""

import pymysql
import re
import pprint
import json
import split_sentence

from pymongo import MongoClient


def get_addr():
    conn = pymysql.connect(host='localhost',
                           # host='192.168.11.251',
                           # host='data.npacn.com',
                           port=3306,
                           user='root',
                           password='Aa123456',
                           # password='youtong123',
                           # password='mysql',
                           database='zhizhuxia',
                           # database='sipai_backup',
                           charset='utf8',
                           cursorclass=pymysql.cursors.DictCursor)  # 默认返回元祖，加上这个参数返回的是字典结构


    with conn.cursor() as cur1:

        # sql1 = """SELECT id, doc_assets FROM sm_document_copy WHERE doc_assets not like "%\'name\': None%" limit 100;"""
        sql1 = """SELECT doc_result from doc_test limit 10"""

        cur1.execute(sql1)
        #设定游标从第一个开始移动
        cur1.scroll(0, mode='absolute')
        #获取此字段的所有信息
        results = cur1.fetchall()
        # print(results)
        yield results

def conn():
    conn = pymysql.connect(  # host='localhost',
        # host='192.168.11.251',
        host='data.npacn.com',
        port=3306,
        user='youtong',
        password='duc06LEQpgoP',
        # password='youtong123',
        # password='mysql',
        database='sipai',
        # database='sipai_backup',
        charset='utf8',
        cursorclass=pymysql.cursors.DictCursor)  # 默认返回元祖，加上这个参数返回的是字典结构
    return conn


# 从数据库获取数据  mysql
def get_datas():
    one_data = {}   # 存放其中一条数据
    result_list = []
    db = pymysql.Connect("data.npacn.com", "youtong", "duc06LEQpgoP", "sipai")    # 阿里云mysql
    # db = pymysql.Connect("localhost", "root", "Aa123456", "zhizhuxia")
    cursor = db.cursor()
    sql = "SELECT uuid, obligors, creditors, doc_result from sm_document where 661643 < uuid "
    # sql = "SELECT uuid, obligors, creditors, doc_result from sm_document where 280000 < uuid and uuid <= 300000"  # 线程2 结束
    # sql = "SELECT uuid, obligors, creditors, doc_result from sm_document where 376937 < uuid"      # 正在运行
    # sql = "SELECT uuid, obligors, creditors, doc_result FROM doc_test limit 1"   #  obligors 原告    creditors 被告
    # sql = "SELECT doc_result from doc_test where id like '%DE%'"
    # sql = "SELECT doc_content from doc_test where uuid=666"
    # sql = "SELECT uuid, obligors, creditors, doc_result from sm_document"    # 阿里云数据库查询
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        # for result in results:
            # demo_sent = result[0]
            # text_sent = split_sentence.split_sentence_thr(demo_sent)
            # for text in text_sent:
            #     result_list.append(text)

                # to_str = str(text)
                # if text == '' or text.isspace():
                #     print('See you next time!')
                #     break
                # else:
                #     text = list(text.strip())
        # print(result_list)
        return results
    except Exception as e:
        print("Exception is", e)
    db.close()

# 从数据库获取数据  mongo
# uri = 'mongodb://' + 'root' + ':' + '123456' + '@' + 'test.npacn.com' + ':' + '8017' +'/'+ 'itslaw'
# uri = 'mongodb://test.npacn.com' + ':' + '20000' +'/'+ 'testdb'  # 集群
uri = 'mongodb://' + 'root' + ':' + '123456' + '@' + 'test.npacn.com' + ':' + '20000' +'/'+ 'itslaw'
client = MongoClient(uri)
def get_MONGO_data():
    '''
    查询mongodb数据,并做预处理
    :return: 嵌套的字典-提取后的信息
    '''
    datas = []
    try:
        db = client.itslaw      # 连接所需要的数据库
        collection = db.neimenggu   # collection名
        print('Connect Successfully')
        # 查询数据
        #data_result = collection.find({"doc_province":"湖北省"}).limit(200)
        data_result = collection.find().limit(30000)
        n = 0
        for item in data_result:
            n += 1
            result = {"judge_text": " ",
                      "addr": " ",
                      "charge": "",
                      "keywords": "", "court": "", "proponents": "", "opponents": ""}
            pros = []
            opps = []
            text = []
            judgementId = item['judgementId']   # 判决文书id   唯一标示
            result['judgementId'] = judgementId
            if 'doc_province' in item.keys() and 'doc_city' in item.keys():
                addr = str(item['doc_province']) + str(item['doc_city'])  # 案件的归属地
                result['addr'] = addr
            # 获取罪名
            if 'reason' in item['content'].keys():
                charge = item['content']['reason']['name']
                result['charge'] = charge
            # 获取关键词
            if 'keywords' in item['content'].keys():
                keywords = item['content']['keywords']
                result['keywords'] = keywords

            # 获取法院信息
            if 'court' in item['content'].keys():
                court = item['content']['court']['name']
            # 获取原告
            if 'proponents' in item['content'].keys():
                proponents = item['content']['proponents']  # 原告
                for i in range(len(proponents)):
                    pro = proponents[i]['name']
                    pros.append(pro)
                result['proponents'] = pros

            # # 获取被告
            if 'opponents' in item['content'].keys():
                opponents = item['content']['opponents']   # 被告
                for i in range(len(opponents)):
                    opp = opponents[i]['name']
                    opps.append(opp)
                result['opponents'] = opps

            # 获取当事人及判决等信息
            detail = item['content']['paragraphs']  # 这是一个list
            for i in range(len(detail)):
                if 'typeText' in detail[i].keys():
                    if detail[i]['typeText'] == '裁判结果' or detail[i]['typeText'] == '本院认为':
                        texts = detail[i]['subParagraphs']
                        for i in range(len(texts)):
                            text.append(texts[i]['text'])   # 判决文本内容，list形式存储
            text_temp = ','.join(text)
            result["judge_text"] = re.sub("<a.+?</a>", '', text_temp)
            result['court'] = court
            print('当前数为：', n)
            yield result
    except Exception as e:
        print('Mongo Error is', e)
    # return datas

def del_MONGO_data(judgementId):
    '''
    根据judgement_id删除数据
    :param judgementId:
    :return:
    '''

    db = client.itslaw  # 连接所需要的数据库
    collection = db.neimenggu  # collection名
    return collection.delete_one({"judgementId": judgementId})

def write_data():
    db = pymysql.Connect("localhost", "root", "Aa123456", "zhizhuxia")
    cursor = db.cursor()
    insert_ner_result = ("INSERT INTO doc_result(per, loc, org, re_loc)" "VALUES(%s, %s, %s, %s)")

    cursor.execute(insert_ner_result)

def write_to_mysql():
    pass

def write_to_mongo():
    pass

# get_datas()
# get_MONGO_data()
# ju_id = '999b0cc2-0a8e-49ec-a00b-2e91e3123cd7'
# del_MONGO_data(ju_id)
