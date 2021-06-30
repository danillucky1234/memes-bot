In my pc I have a few memes which I can send at any time I want, but when I'm not at home - I can't.  
So I decided to make a bot, which can help me to solve this problem.  
I already have a bot, which send my files to my friends from cli which written in Bash script, so here i have a question - how can I get access to the files, to the specified folder, if some people already have access to the same bot? How to hide these files from them? - The answer is very simple - secret code.  
When I typed the secret code to my bot, it send me some buttons with file names from the specified directory and I can choose that file what I want

#### So how code works?  
1. When we put `python main.py` we start the two threads. First - update the database every 5 minutes, second thread - make connection with database, files and user.  
2. In the first thread the function read the specified directory every 5 minutes and add some files if they aren't in the database. In order to save time and not to walk through the directory every time and not look at all the files, we record them in a database, where we quickly read if necessary.  
3. In the second thread our bot read every message from the users and when someone sends the secret code:
3.1. Bot read file names from the database  
3.2. Make list with all files  
3.3. Print the list with the file names in the telegram chat  
3.4. Wait until the user switch page or choose the file he wants  
3.5. Send the file  

#### How to download
1. `git clone git@github.com:danillucky1234/memes-bot.git`
2. `cd memes-bot`
3. `pip3 install -r requirements.txt`
4. `python3 main.py &`

#### Dependecies
[pyTelegrambotAPI](https://pypi.org/project/pyTelegramBotAPI/)  
[mysql-connector-python](https://dev.mysql.com/doc/connector-python/en/)  

##### Screenshots
![First page](https://imgur.com/lVp3nAN.jpg)
![Third page](https://imgur.com/qnXvgvp.jpg)
