from types import MethodType
from flask import Flask, json, render_template,request,jsonify, redirect, session, flash
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

client = MongoClient(os.environ['CUSTOMCONNSTR_DBCONNECTION'])
db = client.mymongodb
dados_viagem = db.coviddata
dados_pessoas = db.peopledata
dados_equipamentos = db.equipmentdata

#BASE_URL = "https://127.0.0.1:5000/get/"
BASE_URL = "https://covid19ufpr.azurewebsites.net/get/"
#BASE_URL_HTTP = "http://127.0.0.1:5000/get/"
BASE_URL_HTTP = "http://covid19ufpr.azurewebsites.net/get/"

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
                    session["email"] = data_converted[0]["email"]
                    return redirect (url_for('viagens_page'))
                else:
                    flash("Senha incorreta.")
                    return redirect(url_for('login_page'))
            else:
                flash("Email incorreto.")
                return redirect(url_for('login_page'))
        else:
            return render_template('index.html', title='UFPR COVID MONITOR')
    else:
        return redirect (url_for('viagens_page'))

@app.route('/logout', methods=['GET'])
def logout():
    if not session.get("name"):
        return redirect(url_for('login_page'))
    else:
        session["name"] = None
        session["email"] = None
        return redirect(url_for('login_page'))

@app.route('/cadastro_pessoa', methods=['GET', 'POST'])
def cadastrar_pessoa_page():
    if not session.get("name"):
        if request.method == 'POST':
            data_return = dados_pessoas.find({"email":request.values.get('email')})
            data = json_util.dumps(data_return, default=json_util.default)
            if data == "[]":
                dados_pessoas.insert({"email": request.values.get('email'),"senha": pwd_context.encrypt(request.values.get('senha')) + "=", "nome_completo": request.values.get('nome_completo'), "viagens": []})
                flash("Cadastro realizado com sucesso.")
                return redirect(url_for('login_page'))
            else:
                flash("O email já está sendo usado.")
                return redirect(url_for('cadastrar_pessoa_page'))
        else:
            return render_template('cadastrar_pessoa.html', title='UFPR COVID MONITOR')
    else:
        return redirect (url_for('viagens_page'))

@app.route('/viagens', methods=['GET'])
def viagens_page():
    dados = []
    hashes = []
    if not session.get("name"):
        return redirect(url_for("login_page"))
    else:
        data_return = dados_pessoas.find({"email":session["email"]})
        for viagem in data_return[0]["viagens"]:
            hashes.append(viagem)
            decoded_data = base64.b64decode(viagem)
            dict_data = ast.literal_eval(decoded_data.decode())
            dados.append(f"Origem: {dict_data['origem']} - Destino: {dict_data['destino']} ({dict_data['idLote']})")

        return render_template('viagens.html', title='UFPR COVID MONITOR', dados=dados, nome_pessoa=session["name"], hash=hashes)

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

@app.route('/cadastrar_equipamento', methods=['POST'])
def cadastrar_equipamento():
    data_received = request.get_json(force=True)
    data_return_equipment = dados_pessoas.find({"idEquipamento":data_received["idEquipamento"]})
    data_equipment = json_util.dumps(data_return_equipment, default=json_util.default)
    print(data_equipment == "[]")
    if data_equipment != "[]":
        return jsonify({"Status": "Error - Equipment ID already exists"})
    else:
        dados_equipamentos.insert({"idEquipamento": data_received["idEquipamento"], "telefone": "4199999999", "temperatura_minima": 0, "temperatura_maxima": 25, "luminosidade_minima": 0,
        "luminosidade_maxima": 1, "umidade_minima": 0, "umidade_maxima": 50, "hashURL": "teste"})
        return jsonify({"Status": "Ok - Equipment added"})

@app.route('/qrcode', methods=['POST'])
def get_qrcode():
    if not session.get("name"):
        return redirect(url_for("login_page"))
    else:
        print(request.values["idEquipamento"])
        data_return_equipment = dados_equipamentos.find({"idEquipamento":int(request.values.get("idEquipamento"))})
        data_equipment = json_util.dumps(data_return_equipment, default=json_util.default)
        if data_equipment == "[]":
            flash("Equipamento inexistente.")
            return redirect(url_for('cadastrar_viagem_page'))
        else:
            data_generated = str({
                "origem":f"{request.values.get('origem')}",
                "destino":f"{request.values.get('destino')}",
                "idLote":f"{request.values.get('idLote')}"
            })
            data_generated_bytes = data_generated.encode("ascii")
            hash_generated = (base64.b64encode(data_generated_bytes)).decode("ascii")
            data_equipment = ast.literal_eval(data_equipment)
            dados_equipamentos.update_one({"idEquipamento": data_equipment[0]["idEquipamento"]},
            {"$set": {"telefone": str(request.values.get("telefone")), "temperatura_minima": int(request.values.get("temperatura_minima")), 
            "temperatura_maxima": int(request.values.get("temperatura_maxima")), "luminosidade_minima": int(request.values.get("luminosidade_minima")),
            "luminosidade_maxima": int(request.values.get("luminosidade_maxima")), "umidade_minima": int(request.values.get("umidade_minima")), 
            "umidade_maxima": int(request.values.get("umidade_maxima")), "hashURL": BASE_URL_HTTP + str(hash_generated)}})
            dados_pessoas.update_one({"email": session["email"]}, {"$push": {"viagens": hash_generated}})
            img = qrcode.make(f'{BASE_URL}{hash_generated}')
            img.save(f'{hash_generated}.png')
            os.rename(f'{hash_generated}.png', f'./static/images/{hash_generated}.png')
            full_filename = os.path.join(app.config['QRIMAGES'], f'{hash_generated}.png')
            return render_template("qrcode.html", origem=request.values.get("origem"), destino=request.values.get("destino"),
                                    codigo=request.values.get("idLote"), nomeImagem=full_filename, title='UFPR COVID MONITOR')
    

if __name__ == "__main__":
    app.run(debug=True)
