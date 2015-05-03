# -*- coding: utf-8 -*-

# Copyright (c) 2014, KOL
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the <organization> nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from urllib import urlencode
from time import time

Video = SharedCodeService.video

PREFIX = '/video/youtubetv'

ART = 'art-default.jpg'
ICON = 'icon-default.png'
TITLE = u'%s' % L('Title')

YT_CLIENT_ID = (
    '29771278111-tmi3ipg0f8iqpahr3jppl05e8rtnen5b'
    '.apps.googleusercontent.com'
)
YT_SECRET = 'idCxu7tYAGbNqLMVr2mpicY7'
YT_SCOPE = 'https://www.googleapis.com/auth/youtube'
YT_VERSION = 'v3'


###############################################################################
# Init
###############################################################################

Plugin.AddViewGroup(
    'details',
    viewMode='InfoList',
    type=ViewType.List,
    summary=SummaryTextType.Long
)


def Start():
    HTTP.CacheTime = CACHE_1HOUR


###############################################################################
# Video
###############################################################################

@handler(PREFIX, TITLE, thumb=ICON)
def MainMenu(complete=False):

    oc = ObjectContainer(title2=TITLE, no_cache=True, replace_parent=False)
    if not CheckToken():
        oc.add(DirectoryObject(
            key=Callback(Authorization),
            title=u'%s' % L('Authorize'),
        ))
        if complete:
            oc.header = L('Authorize')
            oc.message = L('You must enter code for continue')
        return oc

    oc.add(DirectoryObject(
        key=Callback(MySubscriptions),
        title=u'%s' % L('My Subscriptions')
    ))
    oc.add(DirectoryObject(
        key=Callback(Category, title=L('What to Watch')),
        title=u'%s' % L('What to Watch')
    ))
    oc.add(DirectoryObject(
        key=Callback(Playlists, uid='me', title=L('Playlists')),
        title=u'%s' % L('Playlists')
    ))
    oc.add(DirectoryObject(
        key=Callback(Categories),
        title=u'%s' % L('Categories')
    ))
    oc.add(DirectoryObject(
        key=Callback(Channel, uid='me', title=L('My channel')),
        title=u'%s' % L('My channel')
    ))
    AddSystemPlaylists(oc, 'me', ('watchHistory', 'likes'))
    oc.add(InputDirectoryObject(
        key=Callback(
            Search,
            search_type='video',
            title=u'%s' % L('Search Video')
        ),
        title=u'%s' % L('Search'), prompt=u'%s' % L('Search Video')
    ))

    return AddSubscriptions(oc, uid='me')


@route(PREFIX + '/my/subscriptions')
def MySubscriptions(offset=None):
    if not CheckToken():
        return NoContents()

    params = {
        'access_token': Dict['access_token'],
        'ajax': 1,
    }
    if offset:
        params.update(JSON.ObjectFromString(offset))

    path = 'feed' if offset else 'feed/subscriptions'

    try:
        res = JSON.ObjectFromString(HTTP.Request(
            'https://m.youtube.com/%s?%s' % (path, urlencode(params)),
            headers={
                'User-Agent': (
                    'Mozilla/5.0 (iPad; CPU OS 7_0_4 like Mac OS X) '
                    'AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 '
                    'Mobile/11B554a Safari/9537.54'
                )
            }
        ).content[4:])['content']
    except:
        return NoContents()

    if 'single_column_browse_results' in res:
        res = res['single_column_browse_results']['tabs'][0]['content']
    else:
        res = res['continuation_contents']

    if not len(res['contents']):
        return NoContents()

    if 'continuations' in res:
        offset = JSON.StringFromObject({
            'itct': res['continuations'][0]['click_tracking_params'],
            'ctoken': res['continuations'][0]['continuation'],
        })
    else:
        offset = None

    ids = []
    for item in res['contents']:
        ids.append(item['contents'][0]['content']['items'][0]['encrypted_id'])

    oc = ObjectContainer(title2=L('My subscriptions'))
    AddVideos(oc, ids)

    if offset:
        oc.add(NextPageObject(
            key=Callback(
                MySubscriptions,
                offset=offset,
            ),
            title=u'%s' % L('Next page')
        ))

    return oc


@route(PREFIX + '/video/view')
def VideoView(url):
    return URLService.MetadataObjectForURL(url=url, in_container=True)


@indirect
@route(PREFIX + '/video/play')
def VideoPlay(url, fmt):
    return Video.PlayVideo(url, fmt)


@route(PREFIX + '/video/info')
def VideoInfo(url):
    return NotImplemented()


@route(PREFIX + '/channel')
def Channel(uid, title):
    oc = ObjectContainer(
        title2=u'%s' % title
    )

    # Add standart menu
    AddSystemPlaylists(oc, uid)
    if uid == 'me':
        return oc

    oc.add(DirectoryObject(
        key=Callback(
            Subscriptions,
            title=u'%s - %s' % (title, L('Channels')),
            uid=uid
        ),
        title=u'%s' % L('Channels')
    ))
    AddPlaylists(oc, uid=uid)

    return oc


@route(PREFIX + '/categories')
def Categories():
    res = ApiRequest(
        'videoCategories',
        {'part': 'snippet', 'regionCode': GetRegion()}
    )

    if not res or not len(res['items']):
        return NoContents()

    oc = ObjectContainer(
        title2=u'%s' % L('Categories')
    )
    for item in res['items']:
        oc.add(DirectoryObject(
            key=Callback(
                Category,
                title=item['snippet']['title'],
                cid=item['id']
            ),
            title=u'%s' % item['snippet']['title']
        ))

    return oc


@route(PREFIX + '/category')
def Category(title, cid=0, offset=None):
    oc = ObjectContainer(
        title2=u'%s' % title,
        replace_parent=bool(offset)
    )
    AddVideos(
        oc,
        chart='mostPopular',
        limit=Prefs['items_per_page'],
        offset=offset,
        regionCode=GetRegion(),
        videoCategoryId=cid,
    )

    if not len(oc):
        return NoContents()

    return oc


@route(PREFIX + '/playlists')
def Playlists(uid, title, offset=None):
    oc = ObjectContainer(
        title2=u'%s' % title,
        replace_parent=bool(offset)
    )
    limit = Prefs['items_per_page']
    if not offset and uid == 'me':
        AddSystemPlaylists(oc, uid, ('watchLater', 'likes', 'favorites'))
        limit = limit - len(oc)

    return AddPlaylists(oc, uid=uid, limit=limit, offset=offset)


@route(PREFIX + '/playlist')
def Playlist(pid, title, offset=None):
    res = ApiRequest('playlistItems', ApiGetParams(
        part='contentDetails',
        playlistId=pid,
        offset=offset,
        limit=Prefs['items_per_page']
    ))

    if not res or not len(res['items']):
        return NoContents()

    oc = ObjectContainer(
        title2=u'%s' % title,
        replace_parent=bool(offset)
    )

    ids = []
    for item in res['items']:
        ids.append(item['contentDetails']['videoId'])

    AddVideos(oc, ids)

    if 'nextPageToken' in res:
        oc.add(NextPageObject(
            key=Callback(
                Playlist,
                title=oc.title2,
                pid=pid,
                offset=res['nextPageToken'],
            ),
            title=u'%s' % L('Nex page')
        ))

    return oc


@route(PREFIX + '/subscriptions')
def Subscriptions(uid, title, offset=None):
    oc = ObjectContainer(
        title2=u'%s' % L('Subscriptions'),
        replace_parent=bool(offset)
    )
    return AddSubscriptions(oc, uid=uid, offset=offset, limit=Prefs['items_per_page'])


def AddVideos(oc, ids=[], **kwargs):

    res = ApiRequest('videos', ApiGetParams(
        part='snippet,contentDetails',
        id=','.join(ids),
        **kwargs
    ))
    if not res or not len(res['items']):
        return oc

    for item in res['items']:
        url = 'http://tv.youtube.plugins.plex.com/%s' % item['id']
        snippet = item['snippet']
        oc.add(VideoClipObject(
            key=Callback(VideoView, url=url),
            rating_key=url,
            title=u'%s' % snippet['title'],
            summary=u'%s' % snippet['description'],
            thumb=snippet['thumbnails']['high']['url'],
            duration=(Video.ParseDuration(
                item['contentDetails']['duration']
            )*1000),
            originally_available_at=Datetime.ParseDate(
                snippet['publishedAt']
            ).date(),
            items=Video.GetMediaObjects(
                url=Video.GetUrlByVideoId(item['id']),
                play_callback=VideoPlay,
                definition=item['contentDetails']['definition']
            )
        ))

    if not ids and 'nextPageToken' in res:
        oc.add(NextPageObject(
            key=Callback(
                Category,
                title=oc.title2,
                cid=kwargs['videoCategoryId'] if 'videoCategoryId' in kwargs else '0',
                offset=res['nextPageToken'],
            ),
            title=u'%s' % L('More playlists')
        ))
    return oc


def AddSystemPlaylists(oc, uid, types=None):

    res = ApiRequest(
        'channels',
        ApiGetParams(
            part='contentDetails',
            uid=uid,
            id=uid if uid != 'me' else None
        )
    )

    if res and res['items']:
        items = res['items'][0]['contentDetails']['relatedPlaylists']

        if types is not None:
            items = dict(filter(lambda v: v[0] in types, items.items()))

        for key in sorted(
            items,
            key=lambda v: v != 'uploads'
        ):
            oc.add(DirectoryObject(
                key=Callback(
                    Playlist,
                    pid=items[key],
                    title=L(key)
                ),
                title=L(key),
            ))

    return oc


def AddPlaylists(oc, uid, offset=None, limit=5):
    res = ApiRequest(
        'playlists',
        ApiGetParams(uid=uid, limit=limit, offset=offset)
    )

    if res:
        if 'items' in res:
            for item in res['items']:
                pid = item['id']
                item = item['snippet']
                title = u'%s' % item['title']
                try:
                    thumb = item['thumbnails']['high']['url']
                except:
                    thumb = ''

                oc.add(DirectoryObject(
                    key=Callback(
                        Playlist,
                        pid=pid,
                        title=title
                    ),
                    title=title,
                    summary=u'%s' % item['description'],
                    thumb=thumb,
                ))

        if 'nextPageToken' in res:
            oc.add(NextPageObject(
                key=Callback(
                    Playlists,
                    uid=uid,
                    title=oc.title2,
                    offset=res['nextPageToken'],
                ),
                title=u'%s' % L('More playlists')
            ))

    if not len(oc):
        return NoContents()

    return oc


def AddSubscriptions(oc, uid, offset=None, limit=5):

    res = ApiRequest(
        'subscriptions',
        ApiGetParams(uid=uid, limit=limit, offset=offset, order='relevance')
    )

    if res:
        if 'items' in res:
            for item in res['items']:
                item = item['snippet']
                title = u'%s' % item['title']
                try:
                    thumb = item['thumbnails']['high']['url']
                except:
                    thumb = ''

                oc.add(DirectoryObject(
                    key=Callback(
                        Channel,
                        uid=item['resourceId']['channelId'],
                        title=title
                    ),
                    title=title,
                    summary=u'%s' % item['description'],
                    thumb=thumb,
                ))


        if 'nextPageToken' in res:
            oc.add(NextPageObject(
                key=Callback(
                    Subscriptions,
                    uid=uid,
                    title=oc.title2,
                    offset=res['nextPageToken'],
                ),
                title=u'%s' % L('More subscriptions')
            ))

    if not len(oc):
        return NoContents()

    return oc


def Search(query, title=u'%s' % L('Search'), offset=0):
    return NotImplemented()


@route(PREFIX + '/authorization')
def Authorization():

    code = None
    if CheckAccessData('device_code'):
        code = Dict['user_code']
        url = Dict['verification_url']
    else:
        res = OAuthRequest({'scope': YT_SCOPE}, 'device/code')
        if res:
            code = res['user_code']
            url = res['verification_url']
            StoreAccessData(res)

    if code:
        oc = ObjectContainer(
            header=u'%s' % L('Authorize'),
            message=L('Please enter code'),
            view_group='details',
            no_cache=True,
            objects=[
                DirectoryObject(
                    key=Callback(MainMenu, complete=True),
                    title=F('Code: %s', code),
                    summary=F('Please, enter code "%s" in %s', code, url),
                    tagline=url,
                ),
                DirectoryObject(
                    key=Callback(MainMenu, complete=True),
                    title=L('Authorize'),
                    summary=L('Complete authorization'),
                ),            ]
        )
        return oc

    return ObjectContainer(
        header=u'%s' % L('Error'),
        message=u'%s' % L('Service temporary unavaliable')
    )


###############################################################################
# Common
###############################################################################

def NoContents():
    return ObjectContainer(
        header=u'%s' % L('Error'),
        message=u'%s' % L('No entries found')
    )


def NotImplemented(**kwargs):
    return ObjectContainer(
        header=u'%s' % L('Not Implemented'),
        message=u'%s' % L('This function not implemented yet')
    )


def GetRegion():
    return Prefs['region'].split('/')[1]


def ApiRequest(method, params):
    if not CheckToken():
        return None

    params['access_token'] = Dict['access_token']
    try:
        res = JSON.ObjectFromURL(
            'https://www.googleapis.com/youtube/%s/%s?%s' % (
                YT_VERSION,
                method,
                urlencode(params)
            )
        )
        if 'error' in res:
            return None
    except:
        return None

    return res


def ApiGetParams(part='snippet', offset=None, limit=None, uid=None, **kwargs):
    params = {
        'part': part,
    }
    if uid is not None:
        if uid == 'me':
            params['mine'] = 'true'
        else:
            params['channelId'] = uid

    if offset:
        params['pageToken'] = offset

    if limit:
        params['maxResults'] = limit

    params.update(filter(lambda v: v[1], kwargs.items()))
    return params


def CheckToken():

    if CheckAccessData('access_token'):
        return True

    if 'refresh_token' in Dict:
        res = OAuthRequest({
            'refresh_token': Dict['refresh_token'],
            'grant_type': 'refresh_token',
        })
        if res:
            StoreAccessData(res)
            return True

    if CheckAccessData('device_code'):
        res = OAuthRequest({
            'code': Dict['device_code'],
            'grant_type': 'http://oauth.net/grant_type/device/1.0',
        })
        if res:
            StoreAccessData(res)
            return True

    return False


def OAuthRequest(params, rtype='token'):
    params['client_id'] = YT_CLIENT_ID
    if rtype == 'token':
        params['client_secret'] = YT_SECRET

    try:
        res = JSON.ObjectFromURL(
            'https://accounts.google.com/o/oauth2/' + rtype,
            values=params,
            cacheTime=0
        )
        if 'error' in res:
            res = False
    except:
        res = False

    return res


def CheckAccessData(key):
    return (key in Dict and Dict['expires'] >= int(time()))


def StoreAccessData(data):
    if 'expires_in' in data:
        data['expires'] = int(time()) + int(data['expires_in'])

    for key, val in data.items():
        Dict[key] = val
