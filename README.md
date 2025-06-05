# Lost&Found Telegram Bot

Lots of schools face a problem with not having organised system for finding lost things. Our project proposes solution to it - Lost&Found bot which helps with filtering, storing and managing everything.

### HM

if you'll find my project interestnig or will end up using or **forking it**, or if you'll have any problems, questions or advice - text me in telegram [@miha19652010](https://t.me/miha19652010) or via mail mikhail.mezh@icloud.com

## Functionality

### User commands

| Command      | Front          | Back  |
| :------------- |:-------------:| :------:|
| `/start`     | sends user greeting and navigates to help bar | saves user id in database for stats and further commands|
| `/help`     | introduces list of commands user can use | nothing interesting |
| `/found` | guides user to fill out a form | sends consecutive messages and then saves submitted message info in database |
| `/lost` | asks user for category and time range, returns all corresponding results | sorts out all completed orders by date and category, returns list of message ids |
| `/notification` | lets user sub or unsub to particular category (sub means to get notifications if new order's added)| stores user id and category name he wants to get notified about|

#### Examples

`/start`

<img src="images/Screenshot 2025-06-05 at 15.37.09.png" alt="start command" width="500"/>

`/help`

<img src="images/Screenshot 2025-06-05 at 10.54.48.png" alt="help command" width="400"/>

`/found`

*completed form looks like this*

<img src="images/Screenshot 2025-06-05 at 15.52.53.png" alt="found command" width="400"/>

`/lost`

*category choice*

<img src="images/Screenshot 2025-06-05 at 11.33.03.png" alt="lost command" width="200"/>

*time frame*

<img src="images/Screenshot 2025-06-05 at 11.33.30.png" alt="lost command" width="300"/>

*returned results*

<img src="images/Screenshot 2025-06-05 at 15.22.05.png" alt="lost command" width="300"/>

`/notification`

<img src="images/Screenshot 2025-06-05 at 15.23.02.png" alt="notification command" width="400"/>

*subscribe*

<img src="images/Screenshot 2025-06-05 at 15.23.16.png" alt="subscribe command" width="300"/>

<img src="images/Screenshot 2025-06-05 at 15.23.35.png" alt="subscribe command" width="300"/>

*unsubscribe*

<img src="images/Screenshot 2025-06-05 at 15.23.49.png" alt="unsubscribe command" width="400"/>



### Admin commands

| Command      | Front          | Back  |
| :------------- |:-------------:| :------:|
| `/showall`     | sends admin all stored orders with delete button underneath (deletes order forever) | goes through all message ids as well as deletes the ones user chose|
| `/sendall`     | asks admin for text/photo to broadcast to all bot user | sends admin's message to all users stored |
| `/quickstart` | turns on a broadcast mode: all photos and photos with captions sent will be stored in daily broadcasts category  | stores all sent messages ids under daily broadcasts category |
|`/quickstop` | turns broadcasting mode off| nothing interesting |

`/showall` is pretty self explanatory

<img src="images/Screenshot 2025-06-05 at 16.16.08.png" alt="showall command" width="300"/>

each order is displayed this way, and you can delete it by clicking button below

`/sendall`

<img src="images/Screenshot 2025-06-05 at 11.07.17.png" alt="sendall command" width="400"/>

#### These commands are only included in letovo_edition

`/quickstart` and `/quickstop`

<img src="images/Screenshot 2025-06-05 at 15.25.55.png" alt="quick command" width="400"/>

after this message admin proceeds to send photos (captions are optional), until `/quickstop` is sent

all messages sent in this mode will be saved under daily broadcasts category. you can find it in *Обход дежурного менеджера* category in `/lost`

if user wants to look at these broadcasts, he will choose which date broadcast was made with interactive calendar and receive all broadcasts on this day

<img src="images/Screenshot 2025-06-05 at 15.26.17.png" alt="quick command" width="400"/>

*red crosses are the days without broadcasts*

## Set up your own bot

if you'll have any questions or problems regarding our bot, [contact me](https://t.me/miha19652010) via telegram

### 1. Create your bot

Go to https://t.me/BotFather

Send `/newbot` command:

* Fill name (you can change it later)
* Fill username
* Grab a token

Then send `/mybots` and choose your bot &rarr; *Bot settings* &rarr; *Inline mode* &rarr; *Turn on* &rarr; *Edit inline placeholder* &rarr; write a message which will be shown whenever user chooses category 

In Edit Bot you can set its picture, description, etc.

### 2. Set up a helper channel

Send `/start` command to your bot

In telegram, click New Channel. Make it Public

In Add members choose your bot, make it Admin and save

### 3. Run the bot

Run the following command in terminal

```bash
pip install -r https://raw.githubusercontent.com/CrazyMikha2010/lost_and_found_tg_bot/main/requirements.txt
```

Then copy the code from 

a) `bot_en.py` for english lang bot

b) `bot_rus.py` for russian lang bot

c) `bot_letovo_edition.py` for more commands (look into functionality documentation)


In code replace all

* `@help_channel_name` to channel username you created prior

* `yout_databse_name.db` to any name you want to call your databse file, just put .db at the end

* *YOUR BOT TOKEN HERE* to your actual bot token

**To add admins** you need to visit https://t.me/getmyid_bot from account you want to make admin and get their id. Then paste it into ```ADMIN_IDS``` list

You can run this code manually on your local machine (but it will stop whenever you turn off youe pc or stop the code)

Also you can run it on remote server 24/7, but you'll either have to pay for it or set up your own

## Contributing
 
1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D

# LICENSE

MIT License

Copyright (c) 2025 CrazyMikha2010

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## PS

more about the creation of my project you can read in my [process journal](https://docs.google.com/document/d/1UcnKw5sZ04-hRkM7zI_PcGi9VpnCoyG_O-wbGQ9x0KQ/edit?tab=t.0)
