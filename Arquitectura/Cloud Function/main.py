import json
import functions_framework
from google.cloud import storage
from google.cloud import secretmanager
from googleapiclient.discovery import build
import csv
import logging
import os

# Obtenemos la API key de YouTube del Google Cloud Secret Manager
def get_secret(project_id, secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")

# Función para obtener los comentarios del video de YouTube
def get_video_comments(api_key, video_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    comments = []
    response = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        textFormat="plainText"
    ).execute()

    while response:
        for item in response['items']:
            snippet = item['snippet']['topLevelComment']['snippet']
            comment = snippet['textDisplay']
            author = snippet['authorDisplayName']
            comments.append({"author": author, "comment": comment})
        if 'nextPageToken' in response:
            response = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                pageToken=response['nextPageToken'],
                textFormat="plainText"
            ).execute()
        else:
            break

    return comments

# Función para guardar los comentarios en formato CSV en un bucket del Google Cloud Storage
def save_comments_to_csv(comments, bucket_name, output_subfolder, video_id):
    output_file_name = f"{output_subfolder}/comentarios.csv"
    local_temp_file = f"/tmp/comentarios.csv"
    
    # Guardamos los comentarios en el archivo CSV temporalmente para trabajar sobre ello
    with open(local_temp_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Autor', 'Comentario'])
        for item in comments:
            writer.writerow([item['author'], item['comment']])
    
    # Subimos el archivo CSV finalizado al buecket del Google Cloud Storage
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(output_file_name)
    blob.upload_from_filename(local_temp_file)
    
    # Eliminamos el archivo temporal después de subirlo
    os.remove(local_temp_file)
    
    logging.info(f"Archivo CSV guardado en 'gs://{bucket_name}/{output_file_name}'")

# Entry point, es decir, por donde tiene que empezar a ejecutarse el python del Cloud Funtion
@functions_framework.http
def analyze_youtube_video(request):
    # Evitarmos problemas de acceso y peticiones desde la web con las cabeceras
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600'
    }

    if request.method == 'OPTIONS':
        # Configuración para la solicitud de preflight (CORS)
        return ('', 204, headers)

    try:
        request_json = request.get_json(silent=True)

        if request_json and 'videoID' in request_json:
            video_id = request_json['videoID']
            
            # Variables a utilizar
            project_id = 'hatespeechdetector-420911'
            secret_id = 'yt_api_key'
            bucket_name = 'ds-edw-raw-d1655b14'
            output_subfolder = 'CSV'
            
            # Obtenemos la API key de YouTube
            api_key = get_secret(project_id, secret_id)
            
            # Obtenemos los comentarios del vídeo de YouTube
            comments = get_video_comments(api_key, video_id)
            
            # Guardamos los comentarios en un archivo CSV
            save_comments_to_csv(comments, bucket_name, output_subfolder, video_id)
            
            # Respuesta para luego poder pintarla en la web
            response_data = {
                "video_id": video_id,
                "results": comments
            }
            # retornamos la respuesta en formato json
            return (json.dumps(response_data), 200, headers)
        else:
            return ('Bad Request: Missing videoID', 400, headers)
    except Exception as e:
        # para registrar los errores en logs de Google Cloud Functions
        logging.error(f"Error processing request: {e}")
        return ('Internal Server Error', 500, headers)
