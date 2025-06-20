from google.oauth2 import service_account
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from openai import OpenAI
import os
from dotenv import load_dotenv

#python3 -m pip install --upgrade google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2

SCOPES = ['https://www.googleapis.com/auth/documents']
CREDS = "client_creds.json"

flow = InstalledAppFlow.from_client_secrets_file(CREDS, SCOPES)
credentials = flow.run_local_server(port=0)

# credentials = service_account.Credentials.from_service_account_file(CREDS, scopes=SCOPES)
service = build('docs', 'v1', credentials=credentials)

#https://docs.google.com/document/d/18jR7tuhTSEB2DixusRON-SvtA7N5SXSsLSem51bC70s/edit?tab=t.0
input_url = input("Enter the Google Docs URL: ")

DOC_ID = input_url.split("/d/")[1].split("/")[0]
document = service.documents().get(documentId=DOC_ID).execute()

# print(document.get('body').get('content')[0:3])

document_content = document.get('body').get('content')

all_document_text = ""
for element in document_content:
    if 'paragraph' in element:
        text = element['paragraph']['elements'][0]['textRun']['content']
        all_document_text += text


with open("output.txt", "w") as f:
    f.write(all_document_text)
f.close()

# load_dotenv()
client = OpenAI(api_key="")
print(client.models.list())

response = client.chat.completions.create(model="gpt-3.5-turbo", 
                                   messages=[{"role":"user", "content":f"Summarize the following text:\n{all_document_text} in two or three sentences, and give me some bullet points of any action items."}])

print(response.choices[0].message.content)
