from flask import Flask, request
from flask import jsonify
import json
from datetime import datetime
from cassandra.cluster import Cluster


app = Flask(__name__)


@app.route('/tags',methods = ['GET'])
def getArticlesFromTag():
    if request.method == 'GET':
        data = request.args.get('tag')
        cur = get_tagsdb().cursor()
        cur.execute("Select article_id from tags WHERE tag_name = :tag_name ", {"tag_name":data})
        articlesList = cur.fetchall()
        if len(articlesList) ==0:
            return "No articles containing the tags", 204
        else:
            #fetch the urls of articles with list of result of article_ids
            #cur.execute("Select url from article WHERE article_id IN :articles", {"articles":articlesList})
            #urlList = cur.fetchall()
            return jsonify(articlesList), 200

@app.route('/tagsgrouped',methods = ['GET'])
def getTagsgrouped():
    if request.method == 'GET':
        data = request.args.get('tag')
        cur = get_tagsdb().cursor()
        cur.execute("Select  article_id, group_concat(tag_name) as tag_name from tags group by article_id order by article_id",)
        row = cur.fetchall()
        return jsonify(row), 200

#get tags from the url utility
@app.route('/tags/<string:article_id>',methods = ['GET'])
def getTagsFromArticle(article_id):
    if request.method == 'GET':
        cur = get_tagsdb().cursor()
        cur.execute("SELECT tag_name from tags WHERE article_id= :article_id ", {"article_id":article_id})
        row = cur.fetchall()
        return jsonify(row), 200

#get tags from the url utility
@app.route('/tags/grouped/<string:article_id>',methods = ['GET'])
def getTagsFromArticleID(article_id):
    if request.method == 'GET':
        cur = get_tagsdb().cursor()
        cur.execute("SELECT group_concat(tag_name) as tag_name from tags WHERE article_id= :article_id ", {"article_id":article_id})
        row = cur.fetchall()
        return jsonify(row), 200

@app.route('/tags', methods = ['POST'])
def addTagstoArticle():
    if request.method == 'POST':
        data = request.get_json(force=True)
        executionState:bool = False
        cluster = Cluster(['172.17.0.2'])
        try:
            #check if tag exists or not
            #check if the article exists or not
            session = cluster.connect()
            uid = request.authorization["username"]
            pwd = request.authorization["password"]
            time_created = datetime.now()
            check_data_statement = session.prepare("SELECT COUNT(*) from blogkeyspace.data_by_articleID where user_name=? and article_id=?").bind((uid, data['article_id']))
            check_data = session.execute(check_data_statement)
            if check_data[0].count >= 1:
                insert_tag_statement = session.prepare("UPDATE blogkeyspace.data_by_articleID SET tag_name= tag_name + ? where user_name=? and article_id=?").bind(([data['tag_name']], uid, data['article_id']))
                session.execute(insert_tag_statement)
                executionState = True
            else:
                insert_tag_statement = session.prepare("INSERT INTO blogkeyspace.data_by_articleID (tag_name, article_id, user_name) VALUES (?,?,?)").bind(([data['tag_name']], data['article_id'], uid))
                session.execute(insert_tag_statement)
                executionState = True
            executionState = True
        except Exception as e:
            print(e)
            executionState = False
        finally:
            if executionState:
                return jsonify(message="Tag inserted successfully \n"),201
            else:
                return jsonify(message="Failed to insert tag"),409

@app.route('/tags', methods = ['DELETE'])

def deleteTagFromArticle():
    if request.method == 'DELETE':
        data = request.get_json(force=True)
        #article_id = request.args.get('article_id')
        #print(tag_name+article_id)
        cluster = Cluster(['172.17.0.2'])
        executionState:bool = False
        try:
            session = cluster.connect()
            uid = request.authorization["username"]
            pwd = request.authorization["password"]
            delete_tag_statement = session.prepare("UPDATE blogkeyspace.data_by_articleID set tag_name = tag_name - ? WHERE user_name=? and article_id=?").bind(({data['tag_name']}, uid, data['article_id']))
            session.execute(delete_tag_statement)
            executionState = True
        except Exception as e:
            print(e)
        finally:
            if executionState:
                return jsonify(message="Deleted Tag SucessFully"),200
            else:
                return jsonify(message="Failed to delete tags from article"),409



if __name__ == '__main__':
    app.run(debug=True, port=5002)
