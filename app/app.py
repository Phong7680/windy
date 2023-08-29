from flask import Flask,render_template,request, flash, url_for, redirect
import pickledb, random
import os, time
from flask import current_app, send_from_directory
from pathlib import Path
import sqlite3

#アップリ
app = Flask(__name__)
app.config["SECRET_KEY"] = "2aFDJ7A34FfafdA522FFdda"

#データベース
userdb = pickledb.load("user.db", False)
systemdb = pickledb.load("system.db", False)

#新しいデータベース
data = sqlite3.connect('DATA')
db = data.cursor()

#データベースが存在するかどうかチェック
db.execute("SELECT COUNT(*) FROM sqlite_master"
          "    WHERE TYPE = 'table' AND name = 'tweet'")
row = db.fetchone()

#画像保存位置
basedir = Path(__file__).parent.parent
UPLOAD_FOLDER = str(Path(basedir, "apps", "images"))

#プロフィール写真
avatardb = pickledb.load("avatar.db", False)

if row[0] != 1:
    db.execute("CREATE TABLE tweet(id int, user text, tweet text, date text, tweet_picture text)")
    data.commit()
data.close()

#ログイン中
systemdb.set("_login", "")
systemdb.set("mypage", "0")
systemdb.dump()

#INDEX
@app.route("/", endpoint="index")
def index():
    #Login中チェック
    if not systemdb.get("_login"):
        return render_template("login.html", id="")
    
    #投稿内容表示
    alltw = getAllTweet("user")

    #not mypage
    systemdb.set("mypage", "0")
    systemdb.dump()
    print("---------------------------------")
    a = tweet_pic()
    print(a[0][0])
    print("---------------------------------")
    print(a[0][1])
    return render_template('index.html', list=alltw[0], dt_size=alltw[1], avatar=avatar(), tw_pt = tweet_pic())

#LOGIN
@app.route("/login", methods=['GET', 'POST'], endpoint="login")
def login():

    systemdb.set("tweet_picture", "no")
    systemdb.dump()

    if request.method == "POST":
        userid = request.form.get("id")
        passwd = request.form.get("passwd")

        #入力チェック
        is_valid = True

        if not userid:
            flash("ユーザ名は必須です。")
            is_valid = False
        if not passwd:
            flash("パスワードは必須です。")
            is_valid = False
        if not is_valid:
            #return redirect(url_for("login"))
            return render_template("login.html", id ="")

        #　Loginチェック
        if userdb.get(userid) == passwd:
            print("login ok.")
            systemdb.set("_login", userid)
            systemdb.dump()
            return redirect(url_for("index"))
        else:
            print("login fail.")
            return render_template("login.html", msg="login error.", id="")
    else:
        print("GET")
        return render_template("login.html", id="")

#LOGOUT
@app.route("/logout")
def logout():
    #ログイン中解除
    systemdb.set("_login","") 
    systemdb.dump()
    return render_template("login.html",id="")

#ユーザ登録
@app.route("/user", endpoint="user")
def user():
    return render_template("user.html")

#ユーザ登録
@app.route("/useradd",methods=['GET','POST'], endpoint="useradd")
def useradd():
    userid = request.form.get("id")
    passwd = request.form.get("passwd")

    #入力チェック
    is_valid = True
    if not userid:
        flash("ユーザ名は必須です。")
        is_valid = False
    if not passwd:
        flash("パスワードは必須です。")
        is_valid = False
    if not is_valid:
        return render_template("user.html")
    
    #ユーザ重複チェック
    is_valid = True
    for user in userdb.getall():
        if user == userid:
            flash(userid+"が登録されました。他のユーザ名を入力してください。")
            is_valid = False
            break
    if not is_valid:
        return render_template("user.html")

    userdb.set(userid, passwd)
    userdb.dump()
    systemdb.set("_login", "")
    systemdb.dump()
    avatardb.set(userid, "0")
    avatardb.dump()
    return render_template("login.html", id = userid)

#ユーザ削除
@app.route("/delete",methods=['GET','POST'], endpoint="delete")
def delete():
    #まだログインしていない場合
    if not systemdb.get("_login"):
        return render_template("login.html", id="")

    #ユーザ削除
    if request.method == 'GET':
        code = random.randint(1000, 9999) #確認コード生成
        systemdb.set("_code", str(code))
        systemdb.dump()
        return render_template("delete.html", number=code, error="")
    else:
        CODE = request.form.get("code")
        if str(CODE) == systemdb.get("_code"):
            userdb.rem(systemdb.get("_login"))
            userdb.dump()
            systemdb.set("_login","") #ログイン中解除
            systemdb.dump()
            return render_template("delete.html", number = 0, error="")
        else:
            code = random.randint(1000, 9999) #確認コード生成
            systemdb.set("_code", str(code))
            systemdb.dump()
            return render_template("delete.html", number=code, error="1")

#ユーザ一覧
@app.route("/users")
def users():
    dt_size = userdb.totalkeys()
    list_user= []
    for k in userdb.getall():
        list_user.append(k)
    return render_template("list.html", users = list_user, dt_size = dt_size)

#パスワード変更
@app.route("/passwd-change", methods=["GET", "POST"], endpoint="passchage")
def passwd_change():
    if request.method == "GET":
        return render_template("pass.html")
    else:
        newpass1 = request.form.get("newpasswd1")
        newpass2 = request.form.get("newpasswd2")

        #入力チェック
        is_valid = True
        if newpass1 != newpass2:
            flash("パスワードが一致しません。もう一度入力してください。")
            is_valid = False
        if newpass1 == "":
            flash("パスワードを入力してください。")
            is_valid = False
        if newpass2 == "":
            flash("パスワード確認を入力してください。")
            is_valid = False
        if not is_valid:
            return render_template("pass.html", id="")
        if systemdb.get("_login") == "":
            return render_template("login.html", id="")

        #パスワード変更
        userdb.set(systemdb.get("_login"), newpass1)
        userdb.dump()
        return render_template("pass_success.html")

#投稿
@app.route("/send", methods=['POST'], endpoint="send")
def send():
    #ログイン中チェック
    if not systemdb.get("_login"):
        return render_template("login.html", id="")
    
    data = sqlite3.connect('DATA')
    db = data.cursor()

    # Tweet idの設定
    db.execute("SELECT count(*) FROM tweet")
    result = db.fetchall()

    key = getid()

    contents = request.form["contents"]
    
    #投稿データを保存
    if contents != "":
        data = sqlite3.connect('DATA')
        db = data.cursor()
        now = time.strftime('%Y/%m/%d %H:%M')

        sql = "INSERT INTO tweet VALUES(" + str(key) + ",'" + systemdb.get("_login") + "','" + contents + "','" + now
        if systemdb.get("tweet_picture") == "yes":
            systemdb.set("tweet_picture", "no")
            systemdb.dump()
            sql = sql + "', 'y')"
        else:
            sql = sql + "', 'n')"

        db.execute(sql)
        data.commit()
        data.close()

    #DATAからすべての投稿データをindex.htmlに渡す
    alltw = getAllTweet("user")

    #not mypage
    systemdb.set("mypage", "0")
    systemdb.dump()

    return render_template('index.html', list=alltw[0], dt_size=alltw[1], avatar=avatar(), tw_pt = tweet_pic())


#全投稿削除
@app.route("/twalldelete", methods=['POST'])
def twalldelete():
    data = sqlite3.connect('DATA')
    db = data.cursor()
    db.execute("DELETE FROM tweet WHERE user = '" + systemdb.get("_login")+"'")
    data.commit()
    data.close()
    alltw = getAllTweet("my")
    return render_template('mypage.html', list=alltw[0], dt_size=alltw[1], avatar=avatar(), tw_pt=tweet_pic())

#投稿削除
@app.route("/twdelete", methods=['POST'])
def twdelete():
    #チェックされた投稿を削除
    deletecontents = request.form.getlist("key")
    for k in deletecontents:
        data = sqlite3.connect('DATA')
        db = data.cursor()
        for row in db.execute("SELECT * FROM tweet WHERE id=" + str(k)):
            if row[4] == 'y':
                os.remove(os.path.join(str(UPLOAD_FOLDER), str(k)+".jpg"))
        db.execute("DELETE FROM tweet WHERE id ="+str(k))
        data.commit()
        data.close()
        
    #全投稿を取得    
    alltw = getAllTweet("my")
    return render_template('mypage.html', list=alltw[0], dt_size=alltw[1], avatar=avatar(), tw_pt=tweet_pic())


#検索
@app.route("/search", methods=["POST"])
def search():
    keyword = request.form.get("keyword")
    list_content = []
    dt_size = 0
    data = sqlite3.connect('DATA')
    db = data.cursor()

    # SQL命令
    sql = "SELECT * FROM tweet WHERE (tweet = '"+ str(keyword)+"' OR user = '" +str(keyword)+ "')"
    if systemdb.get("mypage") == "1":
        sql = sql + " AND user = '" +systemdb.get("_login") + "'"
    sql = sql + " ORDER BY id DESC"

    for row in db.execute(sql):
        filename = ""
        if avatardb.get(row[1]) == "1":
            filename = row[1]
        else:
            filename = "avatar"
        list_content.append((str(int(row[0])), row[1], row[2], row[3], row[4], filename))
        dt_size += 1

    print(list_content)

    data.close()
    if systemdb.get("mypage") == "0":
        return render_template("index.html", list=list_content, dt_size=dt_size, avatar=avatar(), tw_pt = tweet_pic())
    else:
        return render_template("mypage.html", list=list_content, dt_size=dt_size, avatar=avatar(), tw_pt = tweet_pic())

#全投稿内容とデータ件数の表示
def getAllTweet(a):
    list_content= []
    data = sqlite3.connect('DATA')
    db = data.cursor()

    # tweet
    sql = "SELECT * FROM tweet"
    if a == "user":
        sql = sql + " ORDER BY id DESC"
    else:
        sql = sql + " WHERE user = '" + systemdb.get("_login") + "' ORDER BY id DESC"

    filename = ""
    for row in db.execute(sql):
        if avatardb.get(row[1]) == "1":
            filename = row[1]
        else:
            filename = "avatar"
        list_content.append((str(int(row[0])), row[1], row[2], row[3], row[4], filename))

    # number tweet
    sql = "SELECT count(*) FROM tweet"
    if a != "user":
        sql = sql + " WHERE user = '" + systemdb.get("_login") + "'"
    db.execute(sql)
    result = db.fetchall()

    data.close()
    return list_content, result[0][0]

#画像
@app.route("/images/<path:filename>")
def image_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

#アップロード
basedir = Path(__file__).parent
UPLOAD_FOLDER = str(Path(basedir, "images"))

@app.route('/upload/<type>', methods=['GET','POST'], endpoint="upload")
def upload(type):
    if request.method == 'GET':
        return render_template('upload.html', complete="", type=type)
    elif request.method == 'POST':
        file = request.files['example']
        temp = file.filename.split('.')

        #ファイル拡張子チェック
        if not file or temp[1] != "jpg":
            return render_template('upload.html', error=1)
        #画像ファイル名変更
        if type == "profile":
            file.filename = str(systemdb.get("_login")) + ".jpg"
            avatardb.set(systemdb.get("_login"), "1")
            avatardb.dump()
        else:
            file.filename = str(getid()) + ".jpg"
            systemdb.set("tweet_picture", "yes")
            systemdb.dump()
        #画像保存
        file.save(os.path.join(str(UPLOAD_FOLDER), file.filename))
        return render_template('upload.html', filename=file.filename, complete="ok", type=type)


#アバター取得
def avatar():
    user =  avatardb.get(systemdb.get("_login"))
    if user == "1":
        return "images/"+systemdb.get("_login")+".jpg"
    else:
        return "images/avatar.jpg"

#投稿IDを取得
def getid():
    data = sqlite3.connect('DATA')
    db = data.cursor()
    db.execute("SELECT count(*) FROM tweet")
    result = db.fetchall()
    key = 0

    if result[0][0] != 0:
        for row in  db.execute("SELECT MAX(id) from tweet"):
            key = int(row[0])
        key += 1
    else:
        key = 1
    data.close()
    return key

#マイページ
@app.route('/mypage', methods=['GET','POST'], endpoint="mypage")
def mypage():
    #Login中チェック
    if not systemdb.get("_login"):
        return render_template("login.html", id="")

    #mypage
    systemdb.set("mypage", "1")
    systemdb.dump()

    alltw = getAllTweet("my")
    return render_template('mypage.html', list=alltw[0], dt_size=alltw[1], avatar=avatar(), tw_pt=tweet_pic())

def tweet_pic():
    tweet_pic = []
    if systemdb.get("tweet_picture") == "yes":
        tweet_pic.append((1, "images/"+str(getid())+".jpg", systemdb.get("_login")))
    else:
        tweet_pic.append((0, "", systemdb.get("_login")))
    return tweet_pic