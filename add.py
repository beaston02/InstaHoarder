import sys
from classes.insta import Get, Config, Wanted


def add(user):
    try:
        user_id = int(user)
    except ValueError:
        conf = Config()
        get = Get(conf)
        r = get.requests_session()
        user_id = get.id_from_username(r, user)

    if user_id in wanted:
        if str(user) != str(user_id):
            print('{} with id {} already in wanted list'.format(user, user_id))
        else:
            print('user id {} already in wanted list'.format(user, user_id))
    else:
        Wanted().add(user_id)
        if str(user) != str(user_id):
            print('{} with id {} has been added to the wanted list'.format(user, user_id))
        else:
            print('user id {} has been added to the wanted list'.format(user, user_id))

if __name__ == '__main__':
    try:
        user = sys.argv[1]
        wanted = Wanted().wanted_users
        if 'instagram.com/' in user:
            user = user.strip('/').split('/')[-1]
        add(user)
        exit()
    except IndexError:
        while True:
            print('enter username or id to add to wanted list')
            user = input()
            if 'instagram.com/' in user:
                user = user.strip('/').split('/')[-1]
            wanted = Wanted().wanted_users
            add(user)