from flask import Flask, render_template,request,redirect,url_for # For flask implementation
from bson import ObjectId # For ObjectId to work
from pymongo import MongoClient
import os
import qrcode

app = Flask(__name__)

qr_images = os.path.join('static', 'images')
app.config['QRIMAGES'] = qr_images

client = MongoClient(r"Paste the PRIMARY CONNECTION STRING here, between quotes") #PRIMARY CONNECTION STRING
db = client.mymongodb    #Select the database
todos = db.coviddata #Select the collection name

BASE_URL = "http://127.0.0.1:5000/"

@app.route('/', methods=['GET'])
def main_page():
    return render_template('index.html', title='UFPR COVID MONITOR')

@app.route('/post/<id>', methods=['POST'])
def post_data(id):
    temperatura=request.values.get("temperatura")
    umidade = request.values.get("umidade")
    coviddata.insert({"hashid": id, "temperatura": temperatura, "umidade": umidade})

@app.route('/get/<id>', methods=['GET'])
def get_data(id):
    data_return = coviddata.find({"hashid":id})
    return data_return

@app.route('/qrcode', methods=['POST'])
def get_qrcode():
    hash_generated = str(hash(request.values.get("destino") + request.values.get("origem")))
    img = qrcode.make(f'{BASE_URL}{hash_generated}')
    img.save(f'{hash_generated}.png')
    os.rename(f'{hash_generated}.png', f'./static/images/{hash_generated}.png')
    full_filename = os.path.join(app.config['QRIMAGES'], f'{hash_generated}.png')
    return render_template("qrcode.html", origem=request.values.get("origem"), destino=request.values.get("destino"),
                            codigo=request.values.get("idLote"), nomeImagem=full_filename, title='UFPR COVID MONITOR')
    

#if __name__ == "__main__":
#   app.run(debug=True)
