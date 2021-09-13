from flask import Flask, render_template,request,jsonify
from bson import json_util
from pymongo import MongoClient
import os
import qrcode
import ast
from datetime import datetime, timedelta
import base64

app = Flask(__name__)

qr_images = os.path.join('static', 'images')
app.config['QRIMAGES'] = qr_images

client = MongoClient("mongodb://dbcovid:jJKZMcJ1Uhh0kVVzVDXCubicG6UBkLreHJcR4uY830VRAEFtk3Tw0w6RJn7xm93wDEiaMFj9ukJIbIQIgg62rg==@dbcovid.mongo.cosmos.azure.com:10255/?ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000&appName=@dbcovid@")
#client = MongoClient(os.environ['CUSTOMCONNSTR_DBCONNECTION'])
db = client.mymongodb
dados_viagem = db.coviddata

BASE_URL = "https://127.0.0.1:5000/get/"
#BASE_URL = "https://covid19ufpr.azurewebsites.net/get/"

@app.route('/', methods=['GET'])
def main_page():
    return render_template('index.html', title='UFPR COVID MONITOR')

@app.route('/post/<id>', methods=['POST'])
def post_data(id):
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
