WARNING!!! Use at your own risk. It seems Instagram is flagging accounts which use scripts to login. I am not responsible for any issues you may run into.

You can put in info other than your own to still download posts from public (non private) users. set the config to something similar:

username = a
password = a

this will cause the login to fail, and will throw an error, but the script will continue to run and download public posts (no stories though). 


This will simply automatically check for new posts or stories from instagram users ever X minutes (set in the config file).

I quickly threw this together, and I know it can be cleaned up a lot. If you want to improve on it, feel free. I may get around to cleaning it up myself later on.

It requires python3.5+, and I believe the only required non default module required is requests which you can install using pip.

Configure it to only check users provided in the wanted file, or any user you are following.

The wanted file should only contain the ID of the user, and not the username. I included a script to add users based off of their username, this script is called "add.py". There are a couple of ways it can be ran. You can either pass the users name as an argument - "python3.5 add.py usersname" - where "usersname is the display name of the user", or running it without an argument will run it in a loop, prompting for the name of the user you wish to add to the wanted file.

Fill out the config file to your desired settings, and run it with python3.5 main.py



