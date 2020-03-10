from flask import Flask, request, jsonify, g, Response
from passlib.apps import custom_app_context as pwd_context
from cassandra.cluster import Cluster
import datetime
import pandas as pd


app = Flask(__name__)

#remaining handle sql query fail and return the status codes
#create user other
@app.route('/user', methods=['POST'])
def InsertUser():
    if request.method == 'POST':
        executionState:bool = False
        cluster = Cluster(['172.17.0.2'])
        data =request.get_json(force= True)
        try:
            session = cluster.connect()
            date_created = datetime.datetime.now()
            is_active = 1
            hash_password = pwd_context.hash(data['hashed_password'])
            get_count_statement = session.prepare("SELECT COUNT(*) FROM blogkeyspace.user_by_username WHERE user_name = ? ALLOW FILTERING").bind((data['user_name'],))
            user_exits = session.execute(get_count_statement)
            if user_exits[0].count <= 0:
                insert_user_statement = session.prepare("INSERT INTO blogkeyspace.user_by_username (user_name, hashed_password, full_name, email_id, date_created, is_active ) VALUES (?,?,?,?,?,?)").bind((data['user_name'],hash_password, data['full_name'], data['email_id'], date_created, is_active))
                session.execute(insert_user_statement)
                executionState = True
        except Exception as e:
            print(e)
            executionState = False
        finally:
            if executionState:
                return jsonify(message="Data Instersted Sucessfully"), 201
            else:
                return jsonify(message="Failed to insert data"), 409

#update user

@app.route('/user', methods=['PATCH'])

def UpdateUser():
    if request.method == 'PATCH':
        executionState:bool = False
        cluster = Cluster(['172.17.0.2'])
        try:
            data  = request.get_json(force=True)
            session = cluster.connect()
            uid = request.authorization["username"]
            pwd = request.authorization["password"]
            hash_password = pwd_context.hash(data['hashed_password'])
            check_active_statement = session.prepare("SELECT count(*) FROM blogkeyspace.user_by_username WHERE user_name=? AND is_active=? ALLOW FILTERING").bind((uid, 1))
            user_exits = session.execute(check_active_statement)
            if user_exits[0].count == 1:
                update_password_statement = session.prepare("UPDATE blogkeyspace.user_by_username SET hashed_password=? WHERE user_name=?").bind((hash_password, uid))
                session.execute(update_password_statement)
                executionState = True
        except Exception as e:
            print(e)
        finally:
            if executionState:
                return jsonify(message="Updated SucessFully"), 201
            else:
                return jsonify(message="Failed to update the data"), 409


#delete user

@app.route('/user', methods=['DELETE'])

def DeleteUser():
    if request.method =="DELETE":
        executionState:bool = False
        cluster = Cluster(['172.17.0.2'])
        try:
            uid = request.authorization["username"]
            pwd = request.authorization["password"]
            session = cluster.connect()
            user_exits_statement = session.prepare("SELECT count(*) FROM blogkeyspace.user_by_username WHERE user_name=? ALLOW FILTERING").bind((uid,))
            user_exits = session.execute(user_exits_statement)
            if user_exits[0].count == 1:
                delete_statement = session.prepare("DELETE FROM blogkeyspace.user_by_username where user_name=?").bind((uid,))
                session.execute(delete_statement)
                executionState = True
        except Exception as e:
            print(e)
        finally:
            if executionState:
                return jsonify(message="Data SucessFully deleted"), 200
            else:
                return jsonify(message="Failed to delete data"), 409


def check_auth(username, password):#print("inside check_auth")\
    cluster = Cluster(['172.17.0.2'])
    session = cluster.connect()
    user_exits_statement = session.prepare("SELECT user_name, hashed_password from blogkeyspace.user_by_username WHERE user_name=?").bind((username,))
    user_exits  = session.execute(user_exits_statement)
    user_dataframe = pd.DataFrame(list(user_exits))
    for index,rows in df.iterrows():
        if row[0][0] == username and pwd_context.verify(password,row[0][1]):
            return True
        else:
            return False

def authenticate():
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 403,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


@app.route('/auth-server', methods= ['POST'])
def decorated():
    try:
        uid = request.authorization["username"]
        pwd = request.authorization["password"]
        if not uid or not pwd or check_auth(uid, pwd) == False:
            return authenticate()
        else:
            return jsonify(message = "OK")
    except:
        return "Need authentication for this operation\n", 401


if __name__== "__main__":
    app.run(debug=True)
