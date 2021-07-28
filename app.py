from flask import Flask, render_template,request,jsonify # For flask implementation
from bson import ObjectId, json_util
from pymongo import MongoClient
import os
import qrcode
import ast

app = Flask(__name__)

qr_images = os.path.join('static', 'images')
app.config['QRIMAGES'] = qr_images

client = MongoClient(r"mongodb://dbufpr:elFQouf8xTqeQREobCw6Rtf9h0IRTdhctcl6MZ1mbqyxMoFbsHKVugrClakPhMUPBEe5cW2Hvm15bvuEbo4DlQ==@dbufpr.mongo.cosmos.azure.com:10255/?ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000&appName=@dbufpr@") #PRIMARY CONNECTION STRING
db = client.mymongodb    #Select the database
todos = db.coviddata #Select the collection name

BASE_URL = "https://covid19ufpr.azurewebsites.net/get/"

@app.route('/', methods=['GET'])
def main_page():
    return render_template('index.html', title='UFPR COVID MONITOR')

@app.route('/post/<id>', methods=['POST'])
def post_data(id):
    data_received = request.get_json(force=True)
    temperatura=data_received["temperatura"]
    umidade = data_received["umidade"]
    luminosidade = data_received["luminosidade"]
    todos.insert({"hashid": id, "temperatura": temperatura, "umidade": umidade, "luminosidade": luminosidade})
    return jsonify({"status": "OK", "id": id, "temperatura": temperatura, "umidade": umidade, "luminosidade": luminosidade})


@app.route('/get/<id>', methods=['GET'])
def get_data(id):
    elements_list = []
    data_return = todos.find({"hashid":id})

    data = json_util.dumps(data_return, default=json_util.default)
    data_converted = ast.literal_eval(data)
    for element in data_converted:
        for dado in element.values():
            if (type(dado) is int) or (type(dado) is float):
                elements_list.append(dado)

    return render_template('data.html', title='UFPR COVID MONITOR', dados=elements_list)

@app.route('/qrcode', methods=['POST'])
def get_qrcode():
    hash_generated = str(hash(request.values.get("destino") + request.values.get("origem")))
    img = qrcode.make(f'{BASE_URL}{hash_generated}')
    img.save(f'{hash_generated}.png')
    os.rename(f'{hash_generated}.png', f'./static/images/{hash_generated}.png')
    full_filename = os.path.join(app.config['QRIMAGES'], f'{hash_generated}.png')
    return render_template("qrcode.html", origem=request.values.get("origem"), destino=request.values.get("destino"),
                            codigo=request.values.get("idLote"), nomeImagem=full_filename, title='UFPR COVID MONITOR')
    

if __name__ == "__main__":
    app.run(debug=True)
