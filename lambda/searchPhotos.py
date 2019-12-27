import json
import boto3
import datetime
import requests

lambda_client = boto3.client('lambda')

region = 'us-east-1'
service = 'es'
headers = { "Content-Type": "application/json" }
host = 'https://vpc-photostest-n7j44q5lcxuspzhsgxpcnhd3uu.us-east-1.es.amazonaws.com'
index = 'photos'
type = 'photos-type'
url = host + '/' + index + '/' + type + '/'

lex = boto3.client('lex-runtime', region_name=region)

s3 = boto3.resource("s3")


# Query Elastic search to get image paths
def get_photo_path(labels):
    img_paths = []
    unique_labels = [] 
    for x in labels: 
        if x not in unique_labels: 
            unique_labels.append(x)
    labels = unique_labels
    for i in labels:
        path = host + '/_search?q=labels:'+i
        print(path)
        response = requests.get(path, headers=headers)
        dict1 =  json.loads(response.text)
        hits_count = dict1['hits']['total']['value']
        print ("DICT : ", dict1)
        for k in range(0, hits_count):
            img_obj = dict1["hits"]["hits"]
            img_bucket = dict1["hits"]["hits"][k]["_source"]["bucket"]
            img_name = dict1["hits"]["hits"][k]["_source"]["id"]
            img_link = 'https://s3.amazonaws.com/' + str(img_bucket) + '/' + str(img_name)
            print (img_link)
            img_paths.append(img_link)
    print (img_paths)
    return img_paths


def get_labels(query):
    response = lex.post_text(
        botName='cloudChatBot',                 
        botAlias="imagePhotoBot",
        userId="snehal",           
        inputText=query
    )
    
    print('Lex response:', response)
    print ("response")
    labels = []
    if response:
        print ("slot: ",response['slots'])
        slot_val = response['slots']
        for key,value in slot_val.items():
            if value!=None:
                labels.append(value)
    return labels


def saveToS3(bucket, file,  content):
  s3.Bucket(bucket).put_object(Key=file, Body=json.dumps(content))
  print('Saved audio reponse from transcribe to S3')


def lambda_handler(event, context):
    print ('event : ', event)
    query = event['queryStringParameters']
    print("Query", query)
    q1 = query['q']
    if q1 == "searchAudio":
        lambda_client = boto3.client('lambda')
        invoke_response = lambda_client.invoke(FunctionName="extractTranscribe",InvocationType='RequestResponse')
        print("Transcribe Response :", invoke_response)
        q1 = invoke_response['Payload'].read().decode("utf-8")
        print('q1 : ', q1)
        q1 = {
            'q' : q1
        }
        saveToS3('hw3-photos-bucket-b2', 'audioResponse.json', q1)
        return {
            'statusCode':200,
            'body': json.dumps({
                'imagePaths':[],
                'userQuery':query
            }),
            'headers':{
                'Access-Control-Allow-Origin': '*'
            }
        } 
    elif q1 == "getAudio":
        q1 = json.loads(s3.Bucket('hw3-photos-bucket-b2').Object('audioResponse.json').get()['Body'].read().decode("utf-8"))
        print("Text : ", q1)
        print("Final String:", q1['q'])
        q1 = q1['q']

    labels = get_labels(q1)
    if len(labels) == 0:
        print ("No images found!")
    print ("LABELS : ",labels)
    img_paths = get_photo_path(labels)
    return {
        'statusCode':200,
        'body': json.dumps({
            'imagePaths':img_paths,
            'userQuery':query,
            'labels': labels,
        }),
        'headers':{
            'Access-Control-Allow-Origin': '*'
        }
    }