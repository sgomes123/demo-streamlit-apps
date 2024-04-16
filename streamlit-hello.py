import streamlit as st
import boto3


# Set the app title 
st.title('My First Streamlit App') 
# Add a welcome message 
st.write('Welcome to my Streamlit app!') 
# Create a text input 
user_input = st.text_input('Enter a custom message:', 'Hello, Streamlit!') 
# Display the customized message 
st.write('Customized Message:', user_input)

# input form to upload a file to s3 bucket
file = st.file_uploader('Upload a file')
if file is not None:
     # read the file
     data = file.read()
     # upload the file to s3 bucket
     bucket = 'XXXXXXXXXXXX'
     s3 = boto3.client('s3')
     s3.upload_fileobj(file, bucket, file.name)
     # display a success message
     st.success('File uploaded successfully!')
else:
     # display a warning message
     st.warning('No file uploaded!')



# streamlit run streamlit-hello.py

# To run the app, you need to create a virtual environment and install the required packages.
# Go to **src/streamlit_app** folder
# cd src/streamlit_app
# Install the required packages using venv:
# python3 -m venv env
# source env/bin/activate
# pip install -r requirements.txt
# Execute it using streamlit
# streamlit run main.py