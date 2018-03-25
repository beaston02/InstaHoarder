LineFormat = '{:>12} {:>12}'

class url:
    home = 'https://instagram.com'
    login = 'https://www.instagram.com/accounts/login/ajax/'
    user = 'https://www.instagram.com/{user}/?__a=1'
    shortcode = 'https://www.instagram.com/p/{shortcode}/?__a=1'
    media = 'https://www.instagram.com/graphql/query/?query_id=17888483320059182&variables={data}'
    stories = 'https://www.instagram.com/graphql/query/?query_hash=d15efd8c0c5b23f0ef71f18bf363c704' \
              '&variables=%7B%22only_stories%22%3Afalse%7D'
    users_stories = 'https://www.instagram.com/graphql/query/?query_hash=bf41e22b1c4ba4c9f31b844ebb7d9056' \
                    '&variables=%7B%22reel_ids%22%3A{user}%2C%22precomposed_overlay%22%3Afalse%7D'
    timeline_media = 'https://www.instagram.com/graphql/query/?query_hash=472f257a40c653c64c666ce877d59d2b' \
                     '&variables=%7B%22id%22%3A%22{user_id}%22%2C%22first%22%3A{count}%2C%22after%22%3A%22{after}%22%7D'
    username = 'https://www.instagram.com/graphql/query/?query_hash=7e1e0c68bbe459cf48cbd5533ddee9d4&variables=%7B%22user_id%22%3A%22{user_id}%22%2C%22include_chaining%22%3Afalse%2C%22include_reel%22%3Atrue%2C%22include_suggested_users%22%3Afalse%2C%22include_logged_out_extras%22%3Afalse%7D'
    following = 'https://www.instagram.com/graphql/query/?query_hash=58712303d941c6855d4e888c5f0cd22f&variables={variables}'
class path:
    post = '{path}/{username}/{year}.{month}.{day}_{hour}.{minute}.{second}.{ext}'
    album = '{path}/{username}/{year}.{month}.{day}_{hour}.{minute}.{second}-{i}.{ext}'
    story = '{path}/{username}/stories/{year}.{month}.{day}_{hour}.{minute}.{second}.{ext}'
    profile_picture = '{path}/{username}/{file_name}.{ext}'

#https://www.camsoda.com/sunnylinn
#https://www.camsoda.com/stalinda