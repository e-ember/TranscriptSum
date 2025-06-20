#download all necessary libraries (APIs, OpenAI)
import sys
import subprocess

print("\nInstalling/updating required libraries...\n")
subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "google-api-python-client", "google-auth-oauthlib", "google-auth-httplib2", "openai", "python-dotenv", "--quiet"])

#import libraries
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from openai import OpenAI
import os
from dotenv import load_dotenv

#This function uses Google Docs API to extract text from a Google Doc and save it locally as a text file.
def get_meeting_notes():
    #set scopes of Google Docs API, accesses user's documents.
    SCOPES = ['https://www.googleapis.com/auth/documents']
    CREDS = "client_creds.json"     #client_creds.json contains client credentials for Google Docs API

    #prompt user to authenticate with Google account, return a credentials object
    try:
        flow = InstalledAppFlow.from_client_secrets_file(CREDS, SCOPES)
        credentials = flow.run_local_server(port=0)
    except:
        print("Failure to authenticate with Google account. Please try again.")
        exit()

    #set up Google Docs API service object
    service = build('docs', 'v1', credentials=credentials)

    #prompt user to enter Google Docs URL
    input_url = input("Enter the Google Docs URL: ")

    #isolate the Google Docs ID from the URL
    try:
        DOC_ID = input_url.split("/d/")[1].split("/")[0]
    except:
        print('Invalid URL. Please enter a valid Google Docs URL.')
        exit()
    #fetch the document using the Google Docs API
    document = service.documents().get(documentId=DOC_ID).execute()

    #extract the content of the document
    document_content = document.get('body').get('content')

    #extract text from document content (this is the meeting notes)
    all_document_text = ""
    for element in document_content:
        if 'paragraph' in element:
            for sub_element in element['paragraph']['elements']:
                text_run = sub_element.get('textRun')
                if text_run:
                    all_document_text += text_run.get('content', '')

    #download meeting notes as text file
    with open(f"{document.get('title')}.txt", "w") as f:
        f.write(all_document_text)
    f.close()

    return service, document, all_document_text

#This function takes a String of meeting notes as input and uses OpenAI's GPT-3.5-turbo model to summarize the notes and extract action items.
def summarize_notes(all_document_text):
    #load environment variables, including OpenAI API key
    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    #prompt ChatGPT to summarize meeting notes and extract action items
    try:
        response = client.chat.completions.create(model="gpt-3.5-turbo", 
                                        messages=[{"role":"user", "content":f"Summarize the following meeting notes:[START MEETING NOTES]\n{all_document_text}[END MEETING NOTES] in three sentences and only three sentences, no less and no more. In addition, give me some bullet points of any descriptions of action items mentioned in the meeting along with the people responsible in the format • PERSON: ACTION, including the bullet point. Add two newline spaces between the summary and the bullet points. Be specific! Don't include anything other than the summary and the bullet points."}]).choices[0].message.content
    except:
        print("Error with OpenAI API response. Please check the API key or status of OpenAI.")
        exit()

    return response

#This function takes in a Google Docs service object, the document object, and the response from OpenAI's API. It creates a new Google Docs document for the summary and action items, and saves it to the user's Google Drive.
def save_summary_notes(service, document, response):        
    #Create a new Google Docs document for the summary - summary_doc
    title = document.get('title') + " - Summary"
    body = {
        'title': title
    }
    summary_doc = service.documents().create(body=body).execute()

    #Insert ChatGPT's response into the new document
    start_insert = document['body']['content'][0]['endIndex']
    requests = [
        {
            'insertText': {
                'location':{
                    'index': start_insert
                },
                'text': response
            }
        }
    ]

    #Update the newly created document with the summary and action items
    service.documents().batchUpdate(documentId=summary_doc.get('documentId'), body={'requests': requests}).execute()

    return title

def main():
    #Extract text from meeting notes Google Doc and save it locally as text file
    service, document, all_document_text = get_meeting_notes()

    #Obtain summary and action items from OpenAI's API
    response = summarize_notes(all_document_text)

    #Save summary notes to user's Google Drive account
    title = save_summary_notes(service, document, response)
    print("Summary document with action items has been created and saved to your Google Drive as: \"" + title+"\"")

main()