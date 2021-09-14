from types import MethodType
from flask import Flask, render_template,request,jsonify, redirect, session
from flask.helpers import url_for
from bson import json_util
from pymongo import MongoClient
import os
import qrcode
import ast
from datetime import datetime, timedelta
import base64
from passlib.context import CryptContext

app = Flask(__name__)
app.config['SECRET_KEY'] = 'oh_so_secret'

qr_images = os.path.join('static', 'images')
app.config['QRIMAGES'] = qr_images

client = MongoClient("mongodb://dbcovid:jJKZMcJ1Uhh0kVVzVDXCubicG6UBkLreHJcR4uY830VRAEFtk3Tw0w6RJn7xm93wDEiaMFj9ukJIbIQIgg62rg==@dbcovid.mongo.cosmos.azure.com:10255/?ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000&appName=@dbcovid@")
#client = MongoClient(os.environ['CUSTOMCONNSTR_DBCONNECTION'])
db = client.mymongodb
dados_viagem = db.coviddata
dados_pessoas = db.peopledata

BASE_URL = "https://127.0.0.1:5000/get/"
#BASE_URL = "https://covid19ufpr.azurewebsites.net/get/"

pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000
)

@app.route('/', methods=['GET', 'POST'])
def login_page():
    if not session.get("name"):
        if request.method == 'POST':
            data_return = dados_pessoas.find({"email":request.values.get('email')})
            data = json_util.dumps(data_return, default=json_util.default)
            if data != "[]":
                data_converted = ast.literal_eval(data)
                if(pwd_context.verify(request.values.get('senha'), data_converted[0]["senha"])):
                    session["name"] = data_converted[0]["nome_completo"]
                    return redirect (url_for('viagens_page'))
                else:
                    return redirect(url_for('login_page'))
            else:
                return redirect(url_for('login_page'))
        else:
            return render_template('index.html', title='UFPR COVID MONITOR')
    else:
        return redirect (url_for('viagens_page'))

@app.route('/cadastro_pessoa', methods=['GET', 'POST'])
def cadastrar_pessoa_page():
    if not session.get("name"):
        if request.method == 'POST':
            data_return = dados_pessoas.find({"email":request.values.get('email')})
            data = json_util.dumps(data_return, default=json_util.default)
            if data == "[]":
                dados_pessoas.insert({"email": request.values.get('email'),"senha": pwd_context.encrypt(request.values.get('senha')) + "=", "nome_completo": request.values.get('nome_completo')})
                return redirect(url_for('login_page'))
            else:
                return 'ERROR'
        else:
            return render_template('cadastrar_pessoa.html', title='UFPR COVID MONITOR')
    else:
        return redirect (url_for('viagens_page'))

@app.route('/viagens', methods=['GET'])
def viagens_page():
    if not session.get("name"):
        return redirect(url_for("login_page"))
    else:
        return f'Bem vindo, {session["name"]}!' 

@app.route('/cadastro_viagem', methods=['GET'])
def cadastrar_viagem_page():
    if not session.get("name"):
        return redirect(url_for("login_page"))
    else:
        return render_template('cadastrar_viagem.html', title='UFPR COVID MONITOR')

@app.route('/post/<id>', methods=['POST'])
def post_data(id):
    if not session.get("name"):
        return redirect(url_for("login_page"))
    else:
        now = datetime.now() - timedelta(hours=3)
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        data_received = request.get_json(force=True)
        temperatura=data_received["temperatura"]
        umidade = data_received["umidade"]
        luminosidade = data_received["luminosidade"]
        dados_viagem.insert({"hashid": id, "periodo": dt_string,"temperatura": temperatura, "umidade": umidade, "luminosidade": luminosidade})
        return jsonify({"status": "OK", "id": id, "periodo":dt_string, "temperatura": temperatura, "umidade": umidade, "luminosidade": luminosidade})


@app.route('/get/<id>', methods=['GET'])
def get_data(id):
    if not session.get("name"):
        return redirect(url_for("login_page"))
    else:
        elements_list = []
        period_list = []
        temperature_list = []
        humidity_list = []
        luminosity_list = []
        data_return = dados_viagem.find({"hashid":id})

        data = json_util.dumps(data_return, default=json_util.default)
        data_converted = ast.literal_eval(data)
        for element in data_converted:
            elements_list.append(element['periodo'])
            period_list.append(element['periodo'])
            elements_list.append(element['temperatura'])
            temperature_list.append(element['temperatura'])
            elements_list.append(element['umidade'])
            humidity_list.append(element['umidade'])
            elements_list.append(element['luminosidade'])
            luminosity_list.append(element['luminosidade'])

        decoded_data = base64.b64decode(id)
        dict_data = ast.literal_eval(decoded_data.decode())

        return render_template('data.html', title='UFPR COVID MONITOR', origem=dict_data["origem"], 
        destino=dict_data["destino"], idLote=dict_data["idLote"], dados=elements_list, periodo=period_list,
        temperatura=temperature_list, umidade=humidity_list, luminosidade=luminosity_list)

@app.route('/qrcode', methods=['POST'])
def get_qrcode():
    if not session.get("name"):
        return redirect(url_for("login_page"))
    else:
        data_generated = str({
            "origem":f"{request.values.get('origem')}",
            "destino":f"{request.values.get('destino')}",
            "idLote":f"{request.values.get('idLote')}"
        })
        data_generated_bytes = data_generated.encode("ascii")
        hash_generated = (base64.b64encode(data_generated_bytes)).decode("ascii")
        img = qrcode.make(f'{BASE_URL}{hash_generated}')
        img.save(f'{hash_generated}.png')
        os.rename(f'{hash_generated}.png', f'./static/images/{hash_generated}.png')
        full_filename = os.path.join(app.config['QRIMAGES'], f'{hash_generated}.png')
        return render_template("qrcode.html", origem=request.values.get("origem"), destino=request.values.get("destino"),
                                codigo=request.values.get("idLote"), nomeImagem=full_filename, title='UFPR COVID MONITOR')
    

if __name__ == "__main__":
    app.run(debug=True)
