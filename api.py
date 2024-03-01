import os
from urllib import request, response
from flask import Flask, request, jsonify

import face_recognition

from werkzeug.exceptions import HTTPException

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

def get_azure_container_client( loginPath : str):

    # Informações fornecidas
    # connection_string = "DefaultEndpointsProtocol=https;AccountName=codereconhecimento;AccountKey=taIOzH1zxOsWN8HfwOLZqnCl1EO9x53f0txAc6jhBDlLB2/tc2Rr23n9pscd+IuF14YLm+gZ/o+i+ASt0e1C7w==;EndpointSuffix=core.windows.net"
    connection_string = "DefaultEndpointsProtocol=https;AccountName=securepass;AccountKey=xRFzevfEIqCJ30rilIwKqI6SeZvugSOSYP8uij9RXUu6c9tqeCx3yxpWCZ94/PD0esQgieuBKSqb+ASt/k2tJQ==;EndpointSuffix=core.windows.net"
    
    # container_name = "containerblobstorage"
    container_name = "securepasscontainer"

    # Conectar com o serviço do Azure
    blob_service_client = BlobServiceClient.from_connection_string( connection_string )

    # Acessando o conteiner da aplicação
    container_client = blob_service_client.get_container_client( container_name )

    # Listar blobs dentro do contêiner
    blobs = container_client.list_blobs()

    # Baixar os arquivos do blob para a pasta temporarea
    for blob in blobs:
        blob_client = container_client.get_blob_client( blob.name )

        # Baixando o arquivo para o diretorio
        blobPath = "/home/azureuser/temp/" + blob.name

        with open( blobPath, "wb") as file:
            download_stream = blob_client.download_blob()
            file.write( download_stream.read() )

            comparacao = recognition_images( loginPath, blobPath )
            if comparacao == True:
                return jsonify({"" : blob.name}), 202

            if comparacao:
                return os.path.splitext( blob.name )[0].lower()

    return jsonify({'error': 'Usuario não encontrado'}), 404

def limpar_arquivos():
    # Execute o comando rm -rf temp
    os.system("rm -rf temp")

    # Cria a pasta
    os.mkdir( "temp" )

    return


def recognition_images(arquivoLogin : str , arquivoBlob : str) -> bool:
    # Passando para o recognition reconhecer a imagem de login
    loginRecognition = face_recognition.load_image_file( arquivoLogin )
    encodingLogin = face_recognition.face_encodings( loginRecognition )[0]

    # Passando para o recognition reconhecer a imagem do blob
    blobRecognition = face_recognition.load_image_file( arquivoBlob )
    encodingBlob = face_recognition.face_encodings( blobRecognition )[0]

    # Comparar encoding da camera com o encoding blob
    resultado_comparacao = face_recognition.compare_faces([ encodingBlob ], encodingLogin )

    print( resultado_comparacao )

     # Se match -> retornar 200 e nome da imagem
    if resultado_comparacao[0]:
        # apagando os arquivos gerados
        limpar_arquivos()

        # Rosto corresponde à base
        return True

    return False

app = Flask(__name__)

@app.route("/login", methods=["POST"])
def login_post():

    if 'file' not in request.files:
        return 'Nenhum arquivo enviado', 400
    
    file = request.files['file']
    filepath = "/home/azureuser/temp/loginenvio" + os.path.splitext( file.filename )[1].lower()
    file.save( filepath )

    return get_azure_container_client( filepath )

app.run(host='0.0.0.0')