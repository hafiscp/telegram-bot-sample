# For Logs
import logging 

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle

# Enabel Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Define States for Conversation
ID, PHOTO, DESCRIPTION = range(3)

# Google Drive Settings
FOLDER_MIME_TYPE = 'application/vnd.google-apps.folder'

IMAGE_MIME_TYPE = 'image/jpeg'
# MIME -> Multipurpose Internet Mail Extensions } Indicates format of files or documents

SCOPES = ['https://www.googleapis.com/auth/drive.file']
# Permits read-write access to files created or opened by the app. 
# This scope provides file access to only the files that the application itself has created and opened.

# Function to authenticate and create a service object
def create_drive_service():
  creds = None
  if os.path.exists('token.pickle'):
    with open('token.pickle','rb') as token:
      creds = pickle.load(token)
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_files('credentials.json', SCOPES)
      creds = flow.run_local_server(port=0)
    with open('token.pickle','wb') as token:
      pickle.dump(creds, token)

  service = build('drive','v3', credentials=creds)
  return service

# Start Function
def start(update:Update, context:CallbackContext) -> int:
  user = update.message.from_user
  first_name = user.first_name
  last_name = user.last_name or ''
  update.message.reply_text( f'Hello {first_name} {last_name}. \nWhat is your TDotCom ID ?')
  return ID

# ID Function
def id(update:Update, context:CallbackContext) -> int:
  user = update.message.from_user
  user_id = update.message.text
  context.user_data['id'] = user_id # Save ID in context data
  logger.info("ID of %s : %s", user.first_name, user_id)
  update.message.reply_text('Got it! \nSend me your Work Screenshot or Image.')
  return PHOTO

# Photo Function
def photo(update:Update, context: CallbackContext) -> int:
  user = update.message.from_user
  photo_file = update.message.photo[-1].get_file()
  photo_file.download(f'{user.first_name}.jpg')
  logger.info("Photo of %s : %s", user.first_name, photo_file)
  update.message.reply_text("Great, Image has been saved! \nNow give me a description for the image.", reply_markup=ReplyKeyboardRemove())
  return DESCRIPTION

# Description - Try 1
# def description(update:Update, context: CallbackContext)-> int:
  user = update.message.from_user
  description =  update.message.text
  context.user_data['description'] = description
  logger.info("Description from %s : %s", user.first_name, description)
  
  # Authentication
  service = create_drive_service()
  
  # Find 'Participants' Folder
  folder_name = 'Participants' #participant_folder_id
  folder_id = '' #participant_folder_id
  results = service.files().list(
    q = f"name='{folder_name}' and mimeType='{FOlDER_MIME_TYPE}' and trashed=false",
    spaces='drive',
    fields = "nextPageToken, files(id,name)").execute()
  items = results.get('files',[])

  if items:
    folder_id = items[0]['id'] #participant_folder_id
  else:
    pass

  results = service.files().list(
  q = f"name='{folder_name}' and mimeType='{FOlDER_MIME_TYPE}' and trashed=false",
  spaces='drive',
  fields = "nextPageToken, files(id,name)").execute()
  items = results.get('files',[])

  if items:
    folder_metadata = {
      'name': folder_name,
      'mimeType' : FOlDER_MIME_TYPE
    }
    folder = service.files().create(body=folder_metadata,fields='id').execute()
    folder_id = folder.get('id')
  else:
     pass
  # Upload the Image
  file_metadata = {
    'name' : context.user_data['id'],
    'parents' : [folder_id]
  }
  media = MediaFileUpload(f'{user.first_name}.jpg',mimetype=IMAGE_MIME_TYPE)
  file = service.files().create(body=file_metadata, media_body = media, fields = 'id').execute()
  update.message.reply_text(f"Uploaded the File with name : \n{file}. \nThank You!")
  return ConversationHandler.END

# Description - Try 2
def description(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    description = update.message.text
    context.user_data['description'] = description
    logger.info("Description from %s : %s", user.first_name, description)
  
    # Authentication
    service = create_drive_service()
  
    # Find 'Participants' Folder
    folder_name = 'Participants'
    folder_id = None
    results = service.files().list(
        q=f"name='{folder_name}' and mimeType='{FOLDER_MIME_TYPE}' and trashed=false",
        spaces='drive',
        fields="nextPageToken, files(id,name)"
    ).execute()
    items = results.get('files', [])

    if items:
        folder_id = items[0]['id']
    else:
        pass

    if folder_id:
        # Create user folder
        user_folder_name = context.user_data['id']
        results = service.files().list(
            q=f"name='{user_folder_name}' and mimeType='{FOLDER_MIME_TYPE}' and trashed=false and '{folder_id}' in parents",
            spaces='drive',
            fields="nextPageToken, files(id,name)"
        ).execute()
        user_items = results.get('files', [])

        if user_items:
            update.message.reply_text(f"Items found : {user_items}")
            
        else:
            # User's folder not found ?
            folder_metadata = {
                'name': user_folder_name,
                'mimeType': FOLDER_MIME_TYPE,
                'parents': [folder_id],
            }
            folder = service.files().create(body=folder_metadata, fields='id').execute()
            folder_id = folder.get('id')  

        # Upload the Image to - user's folder
        file_metadata = {
            'name': f"{user.first_name}.jpg",
            'parents': [folder_id],
        }
        media = MediaFileUpload(f'{user.first_name}.jpg', mimetype=IMAGE_MIME_TYPE)
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        update.message.reply_text(f"Uploaded the File with name: {file}. \nThank You!")
    else:
        update.message.reply_text("Failed to find 'Participants' folder. Please handle this case.")

    return ConversationHandler.END


# Cancel Function
def cancel(update:Update, context:CallbackContext)-> int:
  user = update.message.from_user
  logger.info("User %s Cancelled the Conversation", user.first_name)
  update.message.reply_text("Bye!", reply_markup=ReplyKeyboardRemove())
  return ConversationHandler.END


# Main Function
def main():
  BOT_TOKEN = '6610669277:AAFNx0EHD-S4Cr5mahInjAkQiLSV2NULtAI'
  updater = Updater(BOT_TOKEN)
  dp = updater.dispatcher

  conv_handler = ConversationHandler(
    entry_points = [CommandHandler('start',start)],
    states={
      ID:[MessageHandler(Filters.text & ~Filters.command, id)],
      PHOTO:[MessageHandler(Filters.photo, photo)],
      DESCRIPTION:[MessageHandler(Filters.text & ~Filters.command, description)]
    },
    fallbacks = [CommandHandler('cancel',cancel)],
  )
  dp.add_handler(conv_handler)

  # Start Bot
  updater.start_polling()

  # Run the bot until the user presse Ctrl-C
  updater.idle()

if __name__ == '__main__':
  main()