import os               # for work with files
import itertools        # for iterate through files in the directory
import telebot          # import library to make connection with telegram
import mysql.connector  # for connect to the mysql server
import time             # for sleep function
import threading        # we will use second thread to update our database
import config           # my config, there are global constans such as token, database data and so on

############################ GLOBAL VARIABLES ########################################

# telebot settings
telebot.apihelper.SESSION_TIME_TO_LIVE = 5 * 60

# create instanse of telebot
bot = telebot.TeleBot(config.TOKEN, parse_mode=None)

# dictionary, where we will store Pages instances
pages_dict = {}

# To avoid the "referenced before assignment" error, we can create a class in which we will write the current page and the maximum number of pages
class Pages:
    def __init__(self):
        # if in the database more than 10 files, we print 10 files per page and control buttons left-right
        self.currentPage = 0

        # max pages is a variable in which we store how many pages our bot can show
        # for example, if our database have 13 files, maxpages is equal (13 / 10 + 1) = 2. First page have 10 files, second page have 3 files.
        self.maxPages = 0

############################# MYSQL ##################################################
#           ADD VIDEOS TO THE DATABASE FROM THE DIRECTORY EVERY 5 MINUTES            #

# establishing the connection
mydb = mysql.connector.connect(
    host=config.HOST,
    user=config.USER,
    password=config.PASSWORD,
    database=config.DATABASE
)

# creating a cursor object using the cursor() method
cur = mydb.cursor(buffered=True)

# insert new file name to the database
def insertValueToDB(filename):
    cur.execute("INSERT INTO content (filename) VALUES (%s)", (filename,)) # insert new value to the database
    mydb.commit()   # apply changes

# check if exists such file in the database or not
def checkInDB(filename):
    cur.execute("SELECT filename FROM content WHERE filename = (%s)", (filename,))
    row_count = cur.rowcount # get count of rows with the same name in the database
    if row_count == 0:  # if row_count is equal 0, then in the database we haven't file with this name
        return False
    else:
        return True

# return count of files in the database
def getCountOfFilesInDB():
    cur.execute("SELECT COUNT(id) FROM content")
    row = cur.fetchone()
    return row[0]

# this is function which executes in the second thread
# in infinite loop we will check all files in the special directory and sleep for 5 min
def updateDatabase():
    # insert new videos to the database if they are
    while True:
        # iterate through files in the directory
        for path, dirs, files in os.walk(config.START_PATH):
            for f in files:
                # check file in the directory and if such file not exists in the db, we insert him into
                if not checkInDB(f):
                    insertValueToDB(f)
        
        # sleep 5 minutes 
        time.sleep(300) 

# create a Thread with a function
th = threading.Thread(target=updateDatabase)

# start the thread
th.start()

######################################################################################

# return full path specified file by id
def getFullPathById(index):
    cur.execute("SELECT filename FROM content WHERE id = (%s)", (index,))
    row = cur.fetchone()
    return config.START_PATH + row[0]

# print start message
def printStartMenu(message):
    bot.send_message(message.chat.id, config.START_MESSAGE);

# return full list of files from the database
def getListOfFilesFromDB():
    return cur.execute("SELECT * FROM content ORDER BY filename")

# choose with function to use according to filetype and send the file to the user
def sendFileByFileType(message, file, fileType):
    if fileType == ".mp4" or fileType == ".mkv":
        bot.send_video(message.chat.id, file)
    elif fileType == ".png" or fileType == ".jpg" or fileType == ".jpeg":
        bot.send_photo(message.chat.id, file)
    elif fileType == ".mp3" or fileType == ".ogg":
        bot.send_audio(message.chat.id, file)
    else:
        bot.send_document(message.chat.id, file)

# this function returns keyboard with files in the specified page
def sendNewPage(message, pageNumber):
    # we decrement this valuue because our variable pahesInstance.currentPage starts from 1, not 0
    pageNumber = pageNumber - 1
    pagesInstance = pages_dict[message.chat.id]
    
    # create inline keyboard
    keyboardTraceable = telebot.types.InlineKeyboardMarkup()
    getListOfFilesFromDB() # get list of files (we store them in 'cur' variable)
    amountOfRowsInTheDatabase = cur.rowcount # and get amount of files in the database
    
    # get tuple which looks like [id, fileName]
    row = cur.fetchall()
    
    # if pageNumber will be 1, for loop doesn't show 0 id element, so we should write check
    if pagesInstance.currentPage == 1:
        for i in range(0, pageNumber * 10 + 10):
            # add to the keyboard new inline buttons with name row[1] (fileName) and callback_data - row[0] (id)
            keyboardTraceable.add(
                    telebot.types.InlineKeyboardButton(row[i][1], callback_data=row[i][0])
            )
    else:
        maxFiles = pageNumber * 10 + 10 if getCountOfFilesInDB() > pageNumber * 10 + 10 else getCountOfFilesInDB() 
        for i in range(pageNumber * 10, maxFiles):
            # add to the keyboard new inline buttons with name row[1] (fileName) and callback_data - row[0] (id)
            keyboardTraceable.add(
                    telebot.types.InlineKeyboardButton(row[i][1], callback_data=row[i][0])
            )

    # in the end of the page we should add one or two control buttons
    # before call this function we change currentPage, so we can feel free to compare currentPage
    if pagesInstance.currentPage == 1:
        # add to the keyboard new right arrow button, which can help user to change page and see other files 
        keyboardTraceable.add(
                telebot.types.InlineKeyboardButton(u'\u27A1', callback_data='/right') # right arrow
        )
    elif pagesInstance.currentPage == pagesInstance.maxPages:
        # add to the keyboard only left arrow button, which can help user to change page back
        keyboardTraceable.add(
                telebot.types.InlineKeyboardButton(u'\u2B05', callback_data='/left') # left arrow
        )
    else:
        # in other variant we can change pages both ways
        keyboardTraceable.add(
                telebot.types.InlineKeyboardButton(u'\u2B05', callback_data='/left'), # left arrow
                telebot.types.InlineKeyboardButton(u'\u27A1', callback_data='/right') # right arrow
        )

    # edit message with buttons - change old buttons
    bot.edit_message_text("Current Page: " + str(pagesInstance.currentPage) + "/" + str(pagesInstance.maxPages) + "\nFiles:", message.chat.id, message.message_id, reply_markup=keyboardTraceable) 

# if user writes special command in the bot-chat this function will be called
@bot.message_handler(commands=[config.SECRET_COMMAND])
def getListOfFiles(message):
    pagesInstance = Pages()
    
    # change max pages
    pagesInstance.maxPages = int(getCountOfFilesInDB() / 10) + 1 if getCountOfFilesInDB() % 10 != 0 else int(getCountOfFilesInDB() / 10)
    pagesInstance.currentPage = 1

    # create inline keyboard
    keyboardTraceable = telebot.types.InlineKeyboardMarkup()
    getListOfFilesFromDB() # get list of files (we store them in 'cur' variable)
    amountOfRowsInTheDatabase = cur.rowcount # and get amount of files in the database
    
    if amountOfRowsInTheDatabase <= 10:
        for i in range(0, amountOfRowsInTheDatabase):
            # get tuple which looks like [id, fileName]
            row = cur.fetchone()
        
            # add to the keyboard new inline buttons with name row[1] (fileName) and callback_data - row[0] (id)
            keyboardTraceable.add(
                    telebot.types.InlineKeyboardButton(row[1], callback_data=row[0])
            )
    else: # if amount of rows in the db more than 10
        for i in range(0, 10):
            # get tuple which looks like [id, fileName]
            row = cur.fetchone()
            
            # add to the keyboard new inline buttons with name row[1] (fileName) and callback_data - row[0] (id)
            keyboardTraceable.add(
                    telebot.types.InlineKeyboardButton(row[1], callback_data=row[0])
            )

        # in the end of the page we should add one or two control buttons
        if pagesInstance.currentPage == 1:
            # add to the keyboard new right arrow button, which can help user to change page and see other files 
            keyboardTraceable.add(
                    telebot.types.InlineKeyboardButton('\u27A1', callback_data='/right') # right arrow
            )
        elif pagesInstance.currentPage == pagesInstance.maxPages:
            # add to the keyboard only left arrow button, which can help user to change page back
            keyboardTraceable.add(
                    telebot.types.InlineKeyboardButton('\u2B05', callback_data='/left') # left arrow
            )
        else:
            # in other variant we can change pages both ways
            keyboardTraceable.add(
                    telebot.types.InlineKeyboardButton('\u2B05', callback_data='/left'), # left arrow
                    telebot.types.InlineKeyboardButton('\u27A1', callback_data='/right') # right arrow
            )
    
    if amountOfRowsInTheDatabase <= 10:
        # send the message with inline keyboard
        bot.send_message(message.chat.id, "Files:", reply_markup=keyboardTraceable) 
    else:
        # send the message with inline keyboard and current pages
        bot.send_message(message.chat.id, "Current Page: " + str(pagesInstance.currentPage) + "/" + str(pagesInstance.maxPages) + "\nFiles:", reply_markup=keyboardTraceable)

    pages_dict[message.chat.id] = pagesInstance


# when user choose on of the files from inline keyboard this function is called
@bot.callback_query_handler(func=lambda call: True)
def threatCallback(query):
    # create instance of Pages class and change max pages
    pagesInstance = pages_dict[query.message.chat.id]
    data = query.data # in this variable we store the id of the file, which will be sent or the button direction 
    if data == '/left':
        if pagesInstance.currentPage != 1:
            pagesInstance.currentPage = pagesInstance.currentPage - 1
            sendNewPage(query.message, pagesInstance.currentPage) 
    elif data == '/right':
        if pagesInstance.currentPage != pagesInstance.maxPages:
            pagesInstance.currentPage = pagesInstance.currentPage + 1
            sendNewPage(query.message, pagesInstance.currentPage)
    else:
        fullPath = getFullPathById(data)   # get full path to the file
        file = open(fullPath, 'rb') # open file for reading in binary mode
        split_tup = os.path.splitext(fullPath)  # split the full path which can help us to get file type of the file
        fileType=split_tup[1]
        sendFileByFileType(query.message, file, fileType)

@bot.message_handler(commands=['start'])
def start_message(message):
    if message.text == '/start':
        printStartMenu(message)

bot.polling()
