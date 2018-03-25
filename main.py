from os import name
import sys
if name == 'nt':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
from classes import insta, helper
from time import sleep

if __name__ == '__main__':
    conf = insta.Config()
    r = insta.Get(conf).requests_session()
    insta.Login(conf).login(r)
    insta.History().start()
    for i in range(insta.Config().settings.threads):
        insta.DownloadThread().start()
    insta.Stories(r).start()
    insta.Timeline(r).start()
    info = insta.DownloadThread.downloaded
    while True:
        sys.stdout.write("\033[K")
        print(helper.LineFormat.format("stories:", info['stories']))
        sys.stdout.write("\033[K")
        print(helper.LineFormat.format("posts:", info['posts']))
        sys.stdout.write("\033[K")
        print(helper.LineFormat.format("total:", info['stories'] + info['posts']))
        sys.stdout.write("\033[K")
        print(helper.LineFormat.format("queued:", len(insta.DownloadThread.q.queue)), end="\r")
        sleep(1)
        sys.stdout.write("\033[F\033[F\033[F")