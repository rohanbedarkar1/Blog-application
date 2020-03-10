from flask import Flask,request, g
from flask import jsonify
import datetime
from cassandra.cluster import Cluster


app = Flask(__name__)

#insert articles
@app.route('/article',methods = ['POST'])
#remove requires auth while installing the nginx and this line also
def insertarticle():
    if request.method == 'POST':
        data = request.get_json(force = True)
        executionState:bool = False
        cluster = Cluster(['172.17.0.2'])
        article_id = 0
        try:
            session = cluster.connect()
            current_time= datetime.datetime.now()
            is_active_article=1
            uid = request.authorization["username"]
            pwd = request.authorization["password"]
            get_count_stmt = session.prepare("SELECT MAX(article_id) FROM blogkeyspace.data_by_articleID")
            row = session.execute(get_count_stmt)
            article_id = row[0].system_max_article_id
            if not article_id == 0 and not article_id is None:
                article_id += 1
            else:
                article_id = 1
            insert_article_statement = session.prepare("INSERT INTO blogkeyspace.data_by_articleID (article_id, title, user_name, content, date_created, date_modified, is_active_article) VALUES (?,?,?,?,?,?,?)").bind((article_id, data['title'], uid, data['content'], current_time, current_time, is_active_article))
            session.execute(insert_article_statement)
            url_article=("http://127.0.0.1:5000/article/"+str(article_id)+"")
            insert_url_statement = session.prepare("UPDATE blogkeyspace.data_by_articleID set url=? where article_id=? and user_name=?").bind((url_article,article_id,uid))
            session.execute(insert_url_statement)
            executionState = True
        except Exception as e:
            print(e)
        finally:
            if executionState:
                return jsonify(message="Data Inserted Sucessfully"), 201
            else:
                return jsonify(message="Failed to insert data"), 409


#cur.execute("UPDATE post_article set art=?,lmod_time=? where id=?", (data['art'],tmod,data['id']))

#get latest n article and get all article
@app.route('/article',methods = ['GET'])
def latestArticle():
    if request.method == 'GET': # try except
        limit = request.args.get('limit')
        article_id = request.args.get('article_id')
        metadata = request.args.get('metadata')
        executionState:bool = True
        cur = get_articledb().cursor()

        try:
            if limit is not None :
                cur.execute("select * from article  where is_active_article = 1 order by date_created desc limit :limit",  {"limit":limit})
                row = cur.fetchall()
                if list(row) == []:
                    return "No such value exists\n", 204
                return jsonify(row), 200

            if limit is None and article_id is None and metadata is None:
                cur.execute('''Select * from article where is_active_article=1''')
                row = cur.fetchall()
                if list(row) == []:
                    return "No such value exists\n", 204
                return jsonify(row), 200

            if article_id is not None:
                cur.execute("SELECT * from  article WHERE is_active_article=1 and article_id="+article_id)
                row = cur.fetchall()
                if list(row) == []:
                    return "No such value exists\n", 204
                return jsonify(row), 200

            if metadata is not None:
                cur.execute("select title,author,date_created,url from article  where is_active_article = 1 order by date_created desc limit :metadata", {"metadata":metadata})
                row = cur.fetchall()
                if list(row) == []:
                    return "No such value exists\n", 204
                return jsonify(row), 200

        except:
            get_articledb().rollback()
            executionState = False
        finally:
            if executionState == False:
                return jsonify(message="Fail to retrive from db"), 409
            else:
                return jsonify(row), 200

# update article

@app.route('/article',methods = ['PUT'])
def updateArticle():
    if request.method == 'PUT':
        executionState:bool = False
        cluster = Cluster(['172.17.0.2'])
        try:
            data = request.get_json(force = True)
            session = cluster.connect()
            tmod= datetime.datetime.now()
            uid = request.authorization["username"]
            pwd = request.authorization["password"]
            get_data_statement = session.prepare("select count(*) from blogkeyspace.data_by_articleID where article_id=? and user_name=? ALLOW FILTERING").bind((data['article_id'],uid))
            res = session.execute(get_data_statement)
            if res[0].count:
                update_article_statement = session.prepare("UPDATE blogkeyspace.data_by_articleID set title=?, content=?,date_modified=? where article_id=? and user_name =?").bind((data['title'],data['content'],tmod, data['article_id'], uid))
                session.execute(update_article_statement)
                executionState =True
            else:
                return jsonify(message="Article does not exist"), 409
        except Exception as e:
            print(e)
            executionState = True
        finally:
            if executionState:
                return jsonify(message="Updated Article SucessFully"), 201
            else:
                return jsonify(message="Failed to update Article"), 409

#delete article by article id

@app.route('/article', methods = ['DELETE'])
def deleteArticle():
    if request.method == 'DELETE':

        executionState:bool = False
        try:
            data = request.get_json(force=True)
            uid = request.authorization["username"]
            pwd = request.authorization["password"]
            cur.execute("select * from article where article_id=?",(data['article_id'],))
            res=cur.fetchall()
            if len(res) >0:
                cur.execute("update article set is_active_article=0 where article_id= :article_id and author= :author AND EXISTS(SELECT 1 FROM article WHERE author=:author AND is_active_article=1)",{"article_id":data['article_id'], "author":uid})
                row = cur.fetchall()
                if cur.rowcount >= 1:
                    executionState = True
                get_articledb().commit()

        except:
            get_articledb().rollback()
            print("Error")
        finally:
            if executionState:
                return jsonify(message="Deleted Article SucessFully"), 200
            else:
                return jsonify(message="Failed to delete Article"), 409



if __name__ == '__main__':
    app.run(debug=True, port=5003)
