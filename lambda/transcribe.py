import json
import time
import boto3
import datetime



def lambda_handler(event, context):
    transcribe = boto3.client('transcribe')
    
    job_name = datetime.datetime.now().strftime("%m-%d-%y-%H-%M%S")
    job_uri = "https://hw3-photos-bucket-b2.s3.amazonaws.com/Recording.wav"
    storage_uri = "transcriptrecordings"

    s3 = boto3.client('s3')
    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': job_uri},
        MediaFormat='wav',
        LanguageCode='en-US',
        OutputBucketName=storage_uri
    )

    while True:
        status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
            break
        print("Not ready yet...")    
    
    job_name = str(job_name) + '.json'
    print (job_name)
    obj = s3.get_object(Bucket="transcriptrecordings", Key=job_name)
    print ("Object : ", obj)
    body = json.loads(obj['Body'].read().decode('utf-8'))
    print ("Body :", body)
    
    print ("1",body)
    print("2",body["results"])
    print ("3",body["results"]["transcripts"])
    print ("4",body["results"]["transcripts"][0])
    return body["results"]["transcripts"][0]["transcript"]
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }