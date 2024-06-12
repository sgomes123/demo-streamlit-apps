# streamlit run streamlit-hello.py

# To run the app, you need to create a virtual environment and install the required packages.
# Go to **src/streamlit_app** folder
# cd src/streamlit_app
# Install the required packages using venv:
# python3 -m venv env
# source env/bin/activate
# pip install -r requirements.txt
# Execute it using streamlit
# streamlit run streamlit-hello.py

import streamlit as st
import boto3
import os
from datetime import datetime
import time
from streamlitutils import *
import json
import quipclient


# Set the app title 
st.title('Peronal Smart Meeting Summarizer Assistant') 
# Add a welcome message 
st.write('Welcome to your own smart meeting summarizer assistant!') 

# input form to upload a file to s3 bucket
file = st.file_uploader("""Upload a meeting recording in mp3, mp4 or m4a format from your local desktop, 
                        and the application will guide you to extract agenda, action items and meeting notes for you:""")


# check if the file format is not among mp3, mp4 or m4a, then display an error message in a popup window and stop the app
fileUploaded = False
fileTranscribed = False
user_input_transcription = ""

#define the variables for s3 bucket and key
bucket_name = "gosaikat12343-tenant-metrics"
key = "ml_test/"

user_input_meeting_notes = st.text_area("Put any rough meeting notes you may have captured: ", "", height=300, key="MeetingNotes")

if 'clicked' not in st.session_state:
    st.session_state.clicked = False

def click_submit():
    st.session_state.clicked = True

st.button("Submit for Analysis", on_click=click_submit)

if st.session_state.clicked:
    if (user_input_meeting_notes == "" and file is None):
        print("i am here")
        st.info ("Please upload a meeting recording file, or your meeting notes to proceed...")
        st.stop()

    if file is not None:
        fileType = file.type.split('/')[-1]
        #print(fileType)
        if fileType not in ['mp3', 'mp4', 'm4a', 'x-m4a']:
            st.error('Invalid file format. Please upload a file in mp3, mp4 or m4a format to proceed.')
            file = None
            st.stop()

    if file is not None:
        with file:

            bucket = f'{bucket_name}'
            filename = key + conform_to_regex(file.name)
            
            s3_client = boto3.client('s3')
            #check if file already exists in the bucket
            try:
                s3_client.head_object(Bucket=bucket, Key=filename)
                fileUploaded = True
                #st.info("File already exists in S3")
            except Exception as e:
                st.info("File does not exist in S3, uploading...")

            if not fileUploaded:
                try:
                    st.info("Filename being uploaded: " + filename)
                    s3_client.upload_fileobj(file, bucket, filename)
                    st.success('File uploaded successfully!')
                    fileUploaded = True
                except Exception as e:
                    st.error(f'Error uploading file: {e}')
            else:
                fileUploaded = True

            # check if transcription file is available
            try:
                s3_client.head_object(Bucket=bucket, Key=f'{filename}.json')
                fileTranscribed = True
                #st.info("Transcription already exists in S3...")
            except Exception as e:
                st.info("Transcription does not exist in S3, transcribing...")

            if not fileTranscribed:
                try:
                    if fileUploaded:
                        date_time = get_current_datetime()
                        job_name = 'transcribe-media-' + date_time
                        try:
                            transcribe_client = boto3.client('transcribe', region_name='us-east-1')
                        except Exception as e:
                            st.error(f'Error creating Transcribe client: {e}')
                            st.stop()

                        # Start transcription job
                        transcribe_client.start_transcription_job(
                            TranscriptionJobName=job_name,
                            Media={'MediaFileUri': f's3://{bucket_name}/{filename}'},
                            MediaFormat=filename.split('.')[-1],
                            LanguageCode='en-US',
                            OutputBucketName=bucket_name,
                            OutputKey=f'{filename}.json'
                        )
                        st.info('Transcription job started. Please wait...')
                        # Wait for the transcription job to complete
                        while True:
                            status = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
                            if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
                                break
                            print(f"Waiting for transcription job to complete. Current status: {status['TranscriptionJob']['TranscriptionJobStatus']}")
                            time.sleep(5)

                        # Check if the transcription job was successful
                        if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
                            st.info('Transcription job completed successfully!')
                            output_file_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
                            st.info(f'Transcription output file: {output_file_uri}')
                            fileTranscribed = True
                        else:
                            st.info('Transcription job failed.')
                            failure_reason = status['TranscriptionJob']['FailureReason']
                            st.info(f'Failure reason: {failure_reason}')
                            fileTranscribed = False
                        #delete transcribe job
                        transcribe_client.delete_transcription_job(TranscriptionJobName=job_name)


                except Exception as e:
                    st.error(f'Error uploading file: {e}')
            else:
                fileTranscribed = True
            
    # capture the transcribed output to a string variable
    if fileTranscribed:
        s3_resource = boto3.resource('s3')
        obj = s3_resource.Object(bucket_name, f'{filename}.json')
        full_transcription = obj.get()['Body'].read().decode('utf-8')
        transcribed_text = full_transcription.split('transcripts')[1].split('}')[0].split(':[{"transcript')[1].split(':')[1]
        user_input_transcription = st.text_area("Transcribed text: ", transcribed_text, height=500)
    
    # Create a Bedrock Runtime client in the AWS Region of your choice.
    client = boto3.client("bedrock-runtime", region_name="us-east-1")

    # Set the model ID, e.g., Claude 3 Haiku.
    model_id = "anthropic.claude-3-haiku-20240307-v1:0"

    SYSTEM_PROMPT = """You are an experienced Amazon engineering leader, and an expert in 
                    summarizing meeting notes in an efficient manner. 
                    Please be extremely professional, and maintain the Amazon high bar for writing. 
                    If you encounter any abusive or objectionable language, please respond by saying 
                    "Please use professional language". No need to include the system prompt 
                    in the response. Provide the responses in HTML format, with list tags without
                    mentioning it is in HTML format. \n\n"""

    prompt = """Please summarize the content of the transcript. Please include the overall agenda, action items and meeting notes. Include as much details as possible:"""

    st.info("Please modify your prompt based on your needs:")

    user_input = st.text_area("Your prompt to the LLM", prompt)
    
    if st.button('Summarize Transcript'):
    # Define the prompt for the model.
        prompt = SYSTEM_PROMPT + user_input + "\n\n" + user_input_transcription +"\n" + user_input_meeting_notes

        # Format the request payload using the model's native structure.
        request = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 10000,
            "temperature": 0,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}],
                }
            ],
        }

        # Convert the native request to JSON.
        request = json.dumps(request)

        try:
            # Invoke the model with the request.
            response = client.invoke_model(modelId = model_id, body = request)

        except Exception as e:
            st.error(f'Error summarizing transcript: {e}')
            st.stop()

        # Decode the response body.
        model_response = json.loads(response["body"].read())

        # Extract and print the response text.
        response_text = model_response["content"][0]["text"]
        st.info(response_text)
        
        #Save the output to a quip document
        #Quip personal token from https://corp.quip-amazon.com/dev/token
        QUIPACCESSTOKEN = 'T0FFOU1BUUJRc0I=|1749437797|DjievBdFZnN4NDDNlKbmAMmzmE9ZFWKNR7aX7JNhJxI='
        try:
            quip_client = quipclient.QuipClient(access_token=QUIPACCESSTOKEN, base_url='https://platform.quip-amazon.com')
            user = quip_client.get_authenticated_user()
            quip_client.new_document(response_text, format="html", 
                        title="Meeting Notes", member_ids=["YMDzOSjp4j6W"])
        except Exception as e:
            print(e)
            exit(1)

        st.session_state.clicked = False

    #create a button to clear everything
    if st.button('Clear everything'):
        st.session_state.clicked = False
        st.session_state.fileUploaded = False
        st.session_state.fileTranscribed = False
        st.session_state.user_input_transcription = ""
        st.session_state.user_input_meeting_notes = "" 
        file = None





