import os
import json
import time
import random
import pickle
import requests
import datetime
import threading
import configparser
from time import sleep
from classes.helper import url, path
from queue import Queue
import urllib.request


class Settings:
    def __init__(self, parser, make_absolute):
        ### login ###
        self._make_absolute = make_absolute
        self._username = parser.get('login', 'username')
        self._password = parser.get('login', 'password')
        ### paths ###
        self.conf_save_directory = parser.get('paths', 'save_directory')
        self.conf_wishlist_path = parser.get('paths', 'wishlist_path')
        ### settings ###
        self.run_interval_stories = parser.getint('settings', 'run_interval_stories')
        self.run_interval_timeline = parser.getint('settings', 'run_interval_timeline')
        self.save_video_stories = parser.getboolean('settings', 'save_video_stories')
        self.save_image_stories = parser.getboolean('settings', 'save_image_stories')
        self.save_image_posts = parser.getboolean('settings', 'save_timeline_images')
        self.save_video_posts = parser.getboolean('settings', 'save_timeline_videos')
        self.save_timeline_albums = parser.getboolean('settings', 'save_timeline_albums')
        self.save_profile_picture = parser.getboolean('settings', 'save_profile_picture')
        self.save_all_followed = parser.getboolean('settings', 'save_all_followed')
        self.threads = parser.getint('settings', 'threads')


    @property
    def save_directory(self):
        return self._make_absolute(self.conf_save_directory)

    @property
    def wishlist_path(self):
        return self._make_absolute(self.conf_wishlist_path)

    @property
    def request_session(self):
        return self._make_absolute(os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                        '.{}.browser_session.pickle'.format(self.username)))

    @property
    def username(self):
        return self._username


class Config:
    def __init__(self):
        self._lock = threading.Lock()
        self._config_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.conf')
        self._parser = configparser.ConfigParser()
        self.refresh()

    @property
    def settings(self):
        return self._settings

    def _make_absolute(self, path):
        if not path or os.path.isabs(path):
            return path
        return os.path.join(os.path.dirname(self._config_file_path), path)

    def refresh(self):
        '''load config again to get fresh values'''
        self._parse()
        self._settings = Settings(self._parser, self._make_absolute)

    def _parse(self):
        with self._lock:
            self._parser.read(self._config_file_path)


class Login():
    def __init__(self, config):
        self.config = config
        self.username = self.config.settings.username
        self.password = self.config.settings._password
        self.request_session = self.config.settings.request_session

    def check(self, r):
        result = r.get(url.home)
        if self.username in result.text:
            return True

    def login(self, r):
        if self.check(r):
            print("logged in as {}".format(self.username))
            return
        self.login_info = {
            'username':self.username,
            'password':self.password
        }
        print('logging in')
        result = r.get(url.home)
        r.headers.update({'X-CSRFToken': result.cookies['csrftoken']})
        sleep(5 * random.random())
        login = r.post(url.login, data=self.login_info, allow_redirects=True)
        r.headers.update({'X-CSRFToken': login.cookies['csrftoken']})
        csrftoken = login.cookies['csrftoken']
        sleep(5 * random.random())
        if login.status_code == 200:
            if self.check(r):
                print("\nlogged in as {}\n".format(self.username))
                with open(self.request_session, 'wb') as f:
                    pickle.dump(r, f)


class Wanted():
    def __init__(self):
        self._lock = threading.RLock()
        self._settings = Config().settings
        self._load()

    def _load(self):
        with self._lock:
            with open(self._settings.wishlist_path, 'r+') as file:
                self.wanted = [int(i) for i in file.readlines()]

    @property
    def wanted_users(self):
        with open(self._settings.wishlist_path, 'r+') as file:
            self.wanted = [int(m.strip('\n')) for m in file.readlines()]
            return self.wanted

    def add(self, user):
        with open(self._settings.wishlist_path, 'a+') as file:
            file.write(str(user)+'\n')


class Get():
    def __init__(self, config):
        self.config = config

    def requests_session(self):
        self.request_session = self.config.settings.request_session
        if os.path.exists(self.request_session):
            try:
                with open(self.request_session, 'rb') as f:
                    r = pickle.load(f)
                if Login(self.config).check(r):
                    return r
            except EOFError:
                pass
        r = requests.session()
        r.cookies.update({
            'sessionid': '',
            'mid': '',
            'ig_pr': '1',
            'ig_vw': '1920',
            'csrftoken': '',
            's_network': '',
            'ds_user_id': ''
        })

        r.headers.update({
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US;q=0.6,en;q=0.4',
            'Connection': 'keep-alive',
            'Content-Length': '0',
            'Host': 'www.instagram.com',
            'Origin': 'https://www.instagram.com',
            'Referer': 'https://www.instagram.com/',
            'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36",
            'X-Instagram-AJAX': '1',
            'X-Requested-With': 'XMLHttpRequest'
        })
        return r

    def timeline_data(self, r, user_id, data=None):
        if not data:
            user = r.get(url.username.format(user_id=user_id)).json()['data']['user']['reel']['user']['username']
            result = r.get(url.user.format(user=user)).json()['graphql']['user']
            img_data = {'user_id': str(user_id),
                        'username': user}
            img_data['type'] = 'profile_picture'
            img_data['src'] = result['profile_pic_url_hd']
            img_data['media_id'] = os.path.basename(img_data['src'])
            img_data['ext'] = os.path.splitext(img_data['src'])[-1].strip('.')
            if ShouldDownload().check(img_data):
                img_data['path'] = self.file_path(img_data)
                if not pickle.dumps(img_data) in DownloadThread.q.queue:
                    DownloadThread.q.put(pickle.dumps(img_data))
            result = result['edge_owner_to_timeline_media']
            result['username'] = user

        else:
            result = r.get(url.timeline_media.format(user_id=user_id, count=500,
                        after=data['page_info']['end_cursor'])).json()['data']['user']['edge_owner_to_timeline_media']
            result['username'] = data['username']
        result['user_id'] = user_id
        self.process_data(r, user_id, result)

    def process_data(self, r, user_id, data):
        for item in data['edges']:
            img_data = {'user_id':data['user_id'],
                        'username': data['username']}
            item = item['node']
            if item['__typename'] == 'GraphSidecar':
                img_data['type'] = 'timeline_album'
                img_data['time'] = item['taken_at_timestamp']
                i = 1
                for edge in r.get(url.shortcode.format(**item)).json()['graphql']['shortcode_media'][
                    'edge_sidecar_to_children']['edges']:
                    img_data['i'] = i
                    img_data['src'] = edge['node']['display_resources'][-1]['src']
                    img_data['media_id'] = edge['node']['id']
                    img_data['ext'] = os.path.splitext(img_data['src'])[-1].strip('.')
                    if ShouldDownload().check(img_data):
                        img_data['path'] = self.file_path(img_data)
                        if not pickle.dumps(img_data) in DownloadThread.q.queue:
                            DownloadThread.q.put(pickle.dumps(img_data))
                    i+=1
            else:
                if item['__typename'] == 'GraphImage':
                    img_data['type'] = 'timeline_image'
                    img_data['src'] = item['display_url']
                    img_data['media_id'] = item['id']
                    img_data['ext'] = os.path.splitext(img_data['src'])[-1].strip('.')
                elif item['is_video']:
                    img_data['type'] = 'timeline_video'
                    img_data['src'] = r.get(url.shortcode.format(**item)).json()['graphql']['shortcode_media']['video_url']
                    img_data['media_id'] = item['id']
                    img_data['ext'] = os.path.splitext(img_data['src'])[-1].strip('.')
                if ShouldDownload().check(img_data):
                    img_data['time'] = item['taken_at_timestamp']
                    img_data['path'] = self.file_path(img_data)
                    if not pickle.dumps(img_data) in DownloadThread.q.queue:
                        DownloadThread.q.put(pickle.dumps(img_data))
        if data['page_info']['has_next_page']:
            self.timeline_data(r, user_id, data=data)

    def users_with_stories(self, r):
        for i in range(0,3):
            try:
                response = r.get(url.stories).json()['data']['user']['feed_reels_tray']['edge_reels_tray_to_reel']['edges']
                users = [int(user['node']['id']) for user in response]
                return(users)
            except:pass

    def stories(self, users, r):
        while users:
            user_list = urllib.request.quote(str(users[:100]))
            users = users[100:]
            while True:
                try:
                    response = r.get(url.users_stories.format(user=user_list)).json()
                    break
                except json.decoder.JSONDecodeError:
                    pass
            if 'data' in response:
                for media in response['data']['reels_media']:
                    data= {'user_id':media['user']['id'],
                           'username':media['user']['username']}
                    for item in media['items']:
                        data['media_id'] = item['id']
                        data['time'] = item['taken_at_timestamp']
                        if item['is_video']:
                            data['type'] = 'story_video'
                            data['src'] = item['video_resources'][-1]['src']
                            data['ext'] = 'mp4'
                        else:
                            data['type'] = 'story_img'
                            data['src'] = item['display_resources'][-1]['src']
                            data['ext'] = 'jpg'
                        if ShouldDownload().check(data):
                            data['path'] = self.file_path(data)
                            if not pickle.dumps(data) in DownloadThread.q.queue:
                                DownloadThread.q.put(pickle.dumps(data))
            elif response['message'] == 'rate limited':
                print('going to fast, sleeping for 1 hour to prevent being banned from site')
                time.sleep(3600)

    def file_path(self, data):
        if data['type'] in ['story_img', 'story_video']:
            template = path.story
        elif data['type'] == 'timeline_album':
            template = path.album
        elif data['type'] == 'profile_picture':
            i=0
            while True:
                if i:
                    data['filename'] = 'profile_picture-{}'.format(i)
                else:
                    data['filename'] = 'profile_picture'
                file_path = path.profile_picture.format(path=self.config.settings.save_directory, user_id=data['user_id'],
                                                ext=data['ext'], username=data['username'], file_name=data['filename'])
                if os.path.exists(file_path):
                    i+=1
                else:
                    return file_path

        else:
            template = path.post
        if not 'i' in data: data['i'] = 0
        ct = datetime.datetime.fromtimestamp(int(data['time']))
        return template.format(path=self.config.settings.save_directory, user_id=data['user_id'],
                               second=ct.strftime("%S"), day=ct.strftime("%d"),
                               minute=ct.strftime("%M"), hour=ct.strftime("%H"),
                               month=ct.strftime("%m"), year=ct.strftime("%Y"), ext=data['ext'],
                               username=data['username'], i=data['i'])

    def following(self,r):
        user_id = self.id_from_username(r,self.config.settings.username)
        following = []
        variables = {'id':user_id,
                     'first':1000}
        v = '{'+'"id":"{id}","first":{first}'.format(**variables)+'}'
        while True:
            result = r.get(url.following.format(variables=v)).json()['data']['user']['edge_follow']
            for user in result['edges']:
                following.append(int(user['node']['id']))
            if result['page_info']['has_next_page']:
                variables = {"id": user_id, "first": 1000, "after": result['page_info']['end_cursor']}
                v = '{' + '"id":"{id}","first":{first}, "after":"{after}"'.format(**variables) + '}'
            else:
                return following

    def username_from_id(self, r, user_id):
        return r.get(url.username.format(user_id=user_id)).json()['data']['user']['reel']['user']['username']

    def id_from_username(self, r, username):
        return int(r.get(url.user.format(user=username)).json()['graphql']['user']['id'])


class DownloadThread(threading.Thread):
    q = Queue()
    downloaded = {'stories':0,
                  'posts':0}
    def __init__(self):
        threading.Thread.__init__(self)
        self.config = Config().settings

    def run(self):
        while True:
            while self.q.empty():
                time.sleep(1)
            #print('{} - {}'.format(self.q.qsize(), len(set(self.q.queue))))
            self.data = pickle.loads(self.q.get())
            #print('downloading {}'.format(self.data['src']))
            os.makedirs(os.path.dirname(self.data['path']), exist_ok=True)
            try:
                urllib.request.urlretrieve(self.data['src'], self.data['path'])
                if self.data['type'] in ['story_img', 'story_video']:
                    self.downloaded['stories']+=1
                else:
                    self.downloaded['posts'] += 1
                History.q.put(pickle.dumps(self.data))
            except Exception as inst:
                #print(type(inst))
                #print(inst.args)  # arguments stored in .args
                #print(inst)  # __str__ allows args to printed directly
                pass
                #self.q.put(pickle.dumps(self.data))


class History(threading.Thread):
    history = {}
    q = Queue()

    def __init__(self):
        super().__init__()
        self.json_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.history.json')
        self.json_tmp = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.history.tmp')
        self.last_write = datetime.datetime.now()
        if not os.path.exists(self.json_file):
            self.history = {}
        else:
            with open(self.json_file, 'r') as self.j:
                History.history = json.load(self.j)

    def run(self):
        while True:
            while self.q.empty():
                time.sleep(.1)
            self.data = pickle.loads(self.q.get())
            self.data['user_id'] = str(self.data['user_id'])
            self.data['media_id'] = str(self.data['media_id'])
            if self.data['user_id'] not in History.history:
                History.history[self.data['user_id']] = []
            History.history[self.data['user_id']].append(self.data['media_id'])
            History.history[self.data['user_id']] = list(set(History.history[self.data['user_id']]))
            if self.q.empty() or self.last_write < datetime.datetime.now() - datetime.timedelta(seconds=20):
                self.write_to_file()

    def write_to_file(self):
            with open(self.json_tmp, 'w') as self.f:
                json.dump(History.history, self.f, indent=4)
            self.f.close()
            time.sleep(2)
            if os.name == 'nt':
                os.remove(self.json_file)
            os.rename(self.json_tmp, self.json_file)
            self.last_write = datetime.datetime.now()


class Stories(threading.Thread):

    def __init__(self, r):
        super().__init__()
        self.r = r
        self.conf = Config()

    def run(self):
        while True:
            if self.conf.settings.save_all_followed:
                users = Wanted().wanted_users
                following = Get(self.conf).following(self.r)
                users.extend([u for u in following if u not in users])
            else:
                users = Wanted().wanted_users
            self.next = datetime.datetime.now() + datetime.timedelta(minutes=self.conf.settings.run_interval_stories)
            Get(self.conf).stories(users, self.r)
            while self.next > datetime.datetime.now():
                time.sleep(5)


class Timeline(threading.Thread):

    def __init__(self, r):
        super().__init__()
        self.r = r
        self.conf = Config()

    def run(self):
        while True:
            if self.conf.settings.save_all_followed:
                users = Wanted().wanted_users
                following = Get(self.conf).following(self.r)
                users.extend([u for u in following if u not in users])
            else:
                users = Wanted().wanted_users
            self.next = datetime.datetime.now() + datetime.timedelta(minutes=self.conf.settings.run_interval_timeline)
            for user in users:
                attempt = 0
                while attempt < 3:
                    try:
                        Get(self.conf).timeline_data(self.r, user)
                        break
                    except:attempt+=1
            while self.next > datetime.datetime.now():
                time.sleep(5)


class ShouldDownload:
    def __init__(self):
        self.settings = Config().settings

    def check(self, data):
        user_history = History.history.get(str(data['user_id']))
        #print(user_history)
        if user_history and str(data['media_id']) in user_history:
            return False
        if not self.settings.save_all_followed and data['user_id'] in Wanted().wanted_users:
            return False
        if self.settings.save_image_stories and data['type'] == 'story_img':
            return True
        if self.settings.save_video_stories and data['type'] == 'story_video':
            return True
        if self.settings.save_image_posts and data['type'] == 'timeline_image':
            return True
        if self.settings.save_video_posts and data['type'] == 'timeline_video':
            return True
        if self.settings.save_timeline_albums and data['type'] == 'timeline_album':
            return True
        if self.settings.save_profile_picture and data['type'] == 'profile_picture':
            return True
        return False