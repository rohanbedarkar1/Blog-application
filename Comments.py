from flask import Flask, request
from flask import jsonify
import json
from datetime import datetime
from cassandra.cluster import Cluster
import pandas as pd
from itertools import chain

app = Flask(__name__)

@app.route('/commentscount/<string:article_id>',methods = ['GET'])
def getCommentcount(article_id):
    if request.method == 'GET':
        cur = get_commentsdb().cursor()
        cur.execute("Select  count(comment) as comment from comments where article_id= :article_id",{"article_id":article_id})
        row = cur.fetchall()
        return jsonify(row), 200

@app.route('/commentsOfArticle/<string:article_id>',methods = ['GET'])
def getCommentofEachArticle(article_id):
    if request.method == 'GET':
        cur = get_commentsdb().cursor()
        cur.execute("Select  group_concat(comment) from comments where article_id= :article_id group by article_id order by comment_id desc limit 10",{"article_id":article_id})
        row = cur.fetchall()
        return jsonify(row), 200


#Add comments to the database
@app.route('/comment', methods = ['POST'])
def AddComment():
    if request.method == 'POST':
        executionState:bool = False
        cluster = Cluster(['172.17.0.2'])
        data = request.get_json(force=True)
        try:
            session = cluster.connect()
            uid = request.authorization["username"]
            pwd = request.authorization["password"]
            time_created = datetime.now()
            check_data_statement = session.prepare("SELECT COUNT(*) from blogkeyspace.data_by_articleID where user_name=? and article_id=?").bind((uid, data['article_id']))
            check_data = session.execute(check_data_statement)
            if check_data[0].count >= 1:
                insert_comment_statement = session.prepare("UPDATE blogkeyspace.data_by_articleID SET comment= comment + ? where user_name=? and article_id=?").bind(([data['comment']], uid, data['article_id']))
                session.execute(insert_comment_statement)
                executionState = True
            else:
                insert_comment_statement = session.prepare("INSERT INTO blogkeyspace.data_by_articleID (article_id, date_created, user_name, comment, timestamp) VALUES (?,?,?,?)").bind((data['article_id'], time_created, uid, [data['comment']], time_created))
                session.execute(insert_comment_statement)
                executionState = True
        except Exception as e:
            print(e)
            executionState = False
        finally:
            if executionState:
                return jsonify(message="Inserted SucessFully"), 201
            else:
                return jsonify(message="Fail to insert the data"), 409    #use 409 if value exists and send the message of conflict

#delete a comment from the database
@app.route('/comment', methods = ['DELETE'])
def deleteComment():
    if request.method == 'DELETE':
        executionState:bool = False
        cluster = Cluster(['172.17.0.2'])
        try:
            comment_data = request.args.get('comment_id')
            article_data = request.args.get('article_id')
            session = cluster.connect()
            uid = request.authorization["username"]
            pwd = request.authorization["password"]
            delete_statement = session.prepare("DELETE comment[?] from blogkeyspace.data_by_articleID WHERE user_name=? and article_id=?").bind((int(comment_data), uid,int(article_data)))
            session.execute(delete_statement)
            executionState = True
        except Exception as e:
            print(e)                #if it fails to execute rollback the database
            executionState = False
        finally:
            if executionState:
                return jsonify(message="Deleted Sucessfully"), 201
            else:
                return jsonify(message="Fail to delete the data"), 409

#retrive all or n number of comments from the database
@app.route('/comment', methods = ['GET'])
def retriveComments():
    if request.method == 'GET':
        executionState:bool = False
        cluster = Cluster(['172.17.0.2'])
        try: #move the try block after the below for test case if the data is none or not then only try db connection
            article_data = request.args.get('article_id')
            limit_data = request.args.get('number')
            result_2d = []
            result_1d = []
            session = cluster.connect()
            if article_data is not None and limit_data is not None:
                get_data_statement = session.prepare("select comment from blogkeyspace.data_by_articleID where article_id=? limit ?").bind((int(article_data), int(limit_data)))
                data = session.execute(get_data_statement)
                executionState = True
                for index, row in pd.DataFrame(data).iterrows():
                    result_2d.append(row[0])
                result_1d = list(chain.from_iterable(result_2d))[::-1]
                if result_1d == []:
                    return jsonify(message="No such value exists"), 204
                return jsonify(result_1d[:int(limit_data)]), 200

            if article_data is not None and limit_data is None:
                article_data = int(article_data)
                get_data_statement = session.prepare("SELECT comment from blogkeyspace.data_by_articleID WHERE article_id=?").bind((article_data,))
                data = session.execute(get_data_statement)
                executionState = True
                df = pd.DataFrame(data)
                for index, row in df.iterrows():
                    if row[0] is None:
                        return jsonify(message="No such value exists"), 204
                    else:
                        result_2d.append(row[0])
                result_1d = list(chain.from_iterable(result_2d))[::-1]
                return jsonify(result_1d), 200
        except Exception as e:
            print(e)
            executionState = False
        finally:
            if executionState == False:
                return jsonify(message="Fail to get the data"), 204

#Update the comments in the database for a particular user
@app.route('/comment', methods =['PUT'])
def UpdateComments():
    if request.method == 'PUT':
        executionState:bool = False
        cluster = Cluster(['172.17.0.2'])
        try:
            data = request.get_json(force = True)
            print(data['comment_id'])
            session = cluster.connect()
            timeCreated = datetime.now()
            uid = request.authorization["username"]
            pwd = request.authorization["password"]
            update_statement = session.prepare("update blogkeyspace.data_by_articleID set comment[?] = ?, timestamp=? WHERE user_name=? and article_id=?").bind((data['comment_id'], data['comment'], timeCreated, uid, data['article_id']))
            session.execute(update_statement)
            executionState = True

        except Exception as e:
            print(e) #if it fails to execute rollback the database
            executionState = False
        finally:
            if executionState:
                return jsonify(message="Updated SucessFully"), 201
            else:
                return jsonify(message="Fail to update the data"), 409

if __name__ == '__main__':
    app.run(debug=True, port=5001)
