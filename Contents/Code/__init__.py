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
from updater import Updater

Video = SharedCodeService.video

PREFIX = '/video/youtubetv'

ART = 'art-default.jpg'
ICON = 'icon-default.png'
TITLE = u'%s' % L('Title')

YT_CLIENT_ID = (
    '383749313750-e0fj400djq4lukahnfjfqg6ckdbets63'
    '.apps.googleusercontent.com'
)
YT_SECRET = 'rHHvL6tgl8Ej9KngduayT2ce'
YT_SCOPE = 'https://www.googleapis.com/auth/youtube'
YT_VERSION = 'v3'

ICONS = {
    'likes': R('q_ic_drawer_likes_playlist_normal.png'),
    'favorites': R('q_ic_drawer_favorites_normal.png'),
    'uploads': R('q_ic_drawer_uploads_normal.png'),
    'watchHistory': R('q_ic_drawer_watch_history_normal.png'),
    'watchLater': R('q_ic_drawer_watch_later_normal.png'),
    'subscriptions': R('q_ic_drawer_subscriptions_normal.png'),
    'browseChannels': R('q_ic_drawer_browse_channels_normal.png'),
    'playlists': R('q_ic_drawer_playlists_normal.png'),
    'whatToWhatch': R('q_ic_drawer_what_to_watch_normal.png'),
    'account': R('ic_account_switcher_sign_in.png'),
    'categories': R('q_ic_drawer_mix_normal.png'),
    'options': R('api_ic_options.png'),
    'suggestions': R('ic_edit_suggestion.png'),
    'remove': R('ic_offline_dialog_remove.png'),
    'next': R('q_ic_drawer_expand_normal.png'),
}

YT_EDITABLE = {
    'watchLater': L('watchLater'),
    'likes': L('I like this'),
    'favorites': L('Add to favorites'),
}

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


def ValidatePrefs():
    loc = GetLanguage()
    if Core.storage.file_exists(Core.storage.abs_path(
        Core.storage.join_path(
            Core.bundle_path,
            'Contents',
            'Strings',
            '%s.json' % loc
        )
    )):
        Locale.DefaultLocale = GetLanguage()
    else:
        Locale.DefaultLocale = 'en-us'


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
            thumb=ICONS['options'],
        ))
        if complete:
            oc.header = L('Authorize')
            oc.message = L('You must enter code for continue')
        return oc

    Updater(PREFIX+'/update', oc)

    oc.add(DirectoryObject(
        key=Callback(MySubscriptions),
        title=u'%s' % L('My Subscriptions'),
        thumb=ICONS['subscriptions'],
    ))
    oc.add(DirectoryObject(
        key=Callback(Category, title=L('What to Watch')),
        title=u'%s' % L('What to Watch'),
        thumb=ICONS['whatToWhatch'],
    ))
    oc.add(DirectoryObject(
        key=Callback(Playlists, uid='me', title=L('Playlists')),
        title=u'%s' % L('Playlists'),
        thumb=ICONS['playlists'],
    ))
    oc.add(DirectoryObject(
        key=Callback(Categories, title=L('Categories'), c_type='video'),
        title=u'%s' % L('Categories'),
        thumb=ICONS['categories'],
    ))
    oc.add(DirectoryObject(
        key=Callback(Categories, title=L('Browse channels'), c_type='guide'),
        title=u'%s' % L('Browse channels'),
        thumb=ICONS['browseChannels'],
    ))
    oc.add(DirectoryObject(
        key=Callback(Channel, oid='me', title=L('My channel')),
        title=u'%s' % L('My channel'),
        thumb=ICONS['account'],
    ))
    AddSystemPlaylists(oc, 'me', ('watchLater', 'watchHistory', 'likes'))
    oc.add(InputDirectoryObject(
        key=Callback(
            Search,
            s_type='video',
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
                'User-Agent': Video.USER_AGENT
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
    AddVideos(
        oc,
        ApiGetVideos(ids=ids),
        extended=Prefs['my_subscriptions_extened']
    )

    if offset:
        oc.add(NextPageObject(
            key=Callback(
                MySubscriptions,
                offset=offset,
            ),
            title=u'%s' % L('Next page'),
            thumb=ICONS['next']
        ))

    return oc


@route(PREFIX + '/video/view')
def VideoView(url):
    return URLService.MetadataObjectForURL(url=url, in_container=True)


@route(PREFIX + '/video/info')
def VideoInfo(vid, pl_item_id=None):

    oc = ObjectContainer()
    res = ApiGetVideos(ids=[vid])

    AddVideos(oc, res, title=L('Play video'))

    if not len(oc):
        return NoContents()

    item = res['items'][0]

    oc.title2 = u'%s' % item['snippet']['title']

    oc.add(DirectoryObject(
        key=Callback(
            Channel,
            oid=item['snippet']['channelId'],
            title=item['snippet']['channelTitle']
        ),
        title=u'%s' % item['snippet']['channelTitle'],
        thumb=ICONS['account'],
    ))

    oc.add(DirectoryObject(
        key=Callback(
            Search,
            title=L('Related videos'),
            query=None,
            relatedToVideoId=item['id']
        ),
        title=u'%s' % L('Related videos'),
        thumb=ICONS['suggestions'],
    ))

    for key, title in YT_EDITABLE.items():
        oc.add(DirectoryObject(
            key=Callback(PlaylistAdd, aid=item['id'], key=key),
            title=u'%s' % title,
            thumb=ICONS[key],
        ))

    if pl_item_id:
        oc.add(DirectoryObject(
            key=Callback(PlaylistRemove, pl_item_id=pl_item_id),
            title=u'%s' % L('Remove from playlist'),
            thumb=ICONS['remove'],
        ))

    return oc


@route(PREFIX + '/channels')
def Channels(oid, title, offset=None):
    res = ApiRequest('channels', ApiGetParams(
        categoryId=oid,
        hl=GetLanguage(),
        limit=Prefs['items_per_page'],
        offset=offset
    ))

    if not res or not len(res['items']):
        return NoContents()

    oc = ObjectContainer(
        title2=u'%s' % title,
        replace_parent=bool(offset)
    )

    for item in res['items']:
        oid = item['id']
        item = item['snippet']

        oc.add(DirectoryObject(
            key=Callback(
                Channel,
                oid=oid,
                title=item['title']
            ),
            title=u'%s' % item['title'],
            summary=u'%s' % item['description'],
            thumb=GetThumbFromSnippet(item),
        ))

    if 'nextPageToken' in res:
        oc.add(NextPageObject(
            key=Callback(
                Channels,
                oid=oid,
                title=title,
                offset=res['nextPageToken'],
            ),
            title=u'%s' % L('Next page'),
            thumb=ICONS['next']
        ))

    return oc


@route(PREFIX + '/channel')
def Channel(oid, title):
    oc = ObjectContainer(
        title2=u'%s' % title
    )

    # Add standart menu
    AddSystemPlaylists(oc, oid)
    if oid == 'me':
        return oc

    oc.add(DirectoryObject(
        key=Callback(
            Subscriptions,
            title=u'%s - %s' % (title, L('Subscriptions')),
            uid=oid
        ),
        title=u'%s' % L('Subscriptions'),
        thumb=ICONS['subscriptions'],
    ))
    AddPlaylists(oc, uid=oid)

    return oc


@route(PREFIX + '/categories')
def Categories(title, c_type):
    res = ApiRequest('%sCategories' % c_type, ApiGetParams(
        regionCode=GetRegion(),
        hl=GetLanguage()
    ))

    if not res or not len(res['items']):
        return NoContents()

    oc = ObjectContainer(
        title2=u'%s' % title
    )

    if c_type == 'guide':
        c_callback = Channels
        oc.add(InputDirectoryObject(
            key=Callback(
                Search,
                s_type='channel',
                title=u'%s' % L('Search channels')
            ),
            title=u'%s' % L('Search'), prompt=u'%s' % L('Search channels')
        ))
    else:
        c_callback = Category

    for item in res['items']:
        oc.add(DirectoryObject(
            key=Callback(
                c_callback,
                title=item['snippet']['title'],
                oid=item['id']
            ),
            title=u'%s' % item['snippet']['title']
        ))

    return oc


@route(PREFIX + '/category')
def Category(title, oid=0, offset=None):
    oc = ObjectContainer(
        title2=u'%s' % title,
        replace_parent=bool(offset)
    )
    res = ApiGetVideos(
        chart='mostPopular',
        limit=Prefs['items_per_page'],
        offset=offset,
        regionCode=GetRegion(),
        videoCategoryId=oid
    )
    AddVideos(oc, res)

    if not len(oc):
        return NoContents()

    if 'nextPageToken' in res:
        oc.add(NextPageObject(
            key=Callback(
                Category,
                title=oc.title2,
                oid=oid,
                offset=res['nextPageToken'],
            ),
            title=u'%s' % L('Next page'),
            thumb=ICONS['next']
        ))

    return oc


@route(PREFIX + '/playlists')
def Playlists(uid, title, offset=None):
    oc = ObjectContainer(
        title2=u'%s' % title,
        replace_parent=bool(offset)
    )

    if not offset and uid == 'me':
        AddSystemPlaylists(oc, uid, ('watchLater', 'likes', 'favorites'))
        oc.add(InputDirectoryObject(
            key=Callback(
                Search,
                s_type='playlist',
                title=u'%s' % L('Search playlists')
            ),
            title=u'%s' % L('Search'), prompt=u'%s' % L('Search playlists')
        ))

    return AddPlaylists(oc, uid=uid, offset=offset)


@route(PREFIX + '/playlist')
def Playlist(oid, title, can_edit=False, offset=None):
    res = ApiRequest('playlistItems', ApiGetParams(
        part='contentDetails',
        playlistId=oid,
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
    pl_map = {}
    can_edit = can_edit and can_edit != 'False'

    for item in res['items']:
        ids.append(item['contentDetails']['videoId'])
        if can_edit:
            pl_map[item['contentDetails']['videoId']] = item['id']

    AddVideos(
        oc,
        ApiGetVideos(ids=ids),
        extended=Prefs['playlists_extened'],
        pl_map=pl_map
    )

    if 'nextPageToken' in res:
        oc.add(NextPageObject(
            key=Callback(
                Playlist,
                title=oc.title2,
                oid=oid,
                offset=res['nextPageToken'],
            ),
            title=u'%s' % L('Next page'),
            thumb=ICONS['next']
        ))

    return oc


@route(PREFIX + '/playlist/add')
def PlaylistAdd(aid, key=None, oid=None, a_type='video'):
    if key is not None:
        items = ApiGetSystemPlayLists('me')
        if key in items:
            oid = items[key]

    if not oid:
        return ErrorMessage()

    res = ApiRequest('playlistItems', {'part': 'snippet'}, data={
        'snippet': {
            'playlistId': oid,
            'resourceId': {
                'kind': 'youtube#'+a_type,
                a_type+'Id': aid,
            }
        }
    })

    if not res:
        return ErrorMessage()

    return SuccessMessage()


def PlaylistRemove(pl_item_id):
    if ApiRequest('playlistItems', {'id': pl_item_id}, rmethod='DELETE'):
        return SuccessMessage()

    return ErrorMessage()


@route(PREFIX + '/subscriptions')
def Subscriptions(uid, title, offset=None):
    oc = ObjectContainer(
        title2=u'%s' % L('Subscriptions'),
        replace_parent=bool(offset)
    )
    return AddSubscriptions(oc, uid=uid, offset=offset)


def AddVideos(oc, res, title=None, extended=False, pl_map={}):
    if not res or not len(res['items']):
        return oc

    for item in res['items']:
        snippet = item['snippet']
        duration = Video.ParseDuration(
            item['contentDetails']['duration']
        )*1000
        summary = u'%s\n%s' % (snippet['channelTitle'], snippet['description'])

        if extended:
            pl_item_id = pl_map[item['id']] if item['id'] in pl_map else None
            oc.add(DirectoryObject(
                key=Callback(VideoInfo, vid=item['id'], pl_item_id=pl_item_id),
                title=u'%s' % snippet['title'],
                summary=summary,
                thumb=GetThumbFromSnippet(snippet),
                duration=duration,
            ))
        else:
            url = Video.GetServiceURL(item['id'])
            oc.add(VideoClipObject(
                key=Callback(VideoView, url=url),
                rating_key=url,
                title=u'%s' % snippet['title'] if title is None else title,
                summary=summary,
                thumb=GetThumbFromSnippet(snippet),
                duration=duration,
                originally_available_at=Datetime.ParseDate(
                    snippet['publishedAt']
                ).date(),
                items=URLService.MediaObjectsForURL(url)
            ))

    return oc


def AddSystemPlaylists(oc, uid, types=None):

    items = ApiGetSystemPlayLists(uid)

    if items:
        if types is not None:
            items = dict(filter(lambda v: v[0] in types, items.items()))

        for key in sorted(
            items,
            key=lambda v: v != 'uploads'
        ):
            oc.add(DirectoryObject(
                key=Callback(
                    Playlist,
                    oid=items[key],
                    title=L(key),
                    can_edit=uid == 'me' and key in YT_EDITABLE
                ),
                title=u'%s' % L(key),
                thumb=ICONS[key] if key in ICONS else None,
            ))

    return oc


def AddPlaylists(oc, uid, offset=None):

    res = ApiRequest('playlists', ApiGetParams(
        uid=uid,
        limit=GetLimitForOC(oc),
        offset=offset,
        hl=GetLanguage()
    ))

    if res:
        if 'items' in res:
            for item in res['items']:
                oid = item['id']
                item = item['snippet']

                oc.add(DirectoryObject(
                    key=Callback(
                        Playlist,
                        oid=oid,
                        title=item['localized']['title'],
                        can_edit=uid == 'me'
                    ),
                    title=u'%s' % item['localized']['title'],
                    summary=u'%s' % item['localized']['description'],
                    thumb=GetThumbFromSnippet(item),
                ))

        if 'nextPageToken' in res:
            oc.add(NextPageObject(
                key=Callback(
                    Playlists,
                    uid=uid,
                    title=oc.title2,
                    offset=res['nextPageToken'],
                ),
                title=u'%s' % L('More playlists'),
                thumb=ICONS['next']
            ))

    if not len(oc):
        return NoContents()

    return oc


def AddSubscriptions(oc, uid, offset=None):

    res = ApiRequest('subscriptions', ApiGetParams(
        uid=uid,
        limit=GetLimitForOC(oc),
        offset=offset, order='relevance'
    ))

    if res:
        if 'items' in res:
            for item in res['items']:
                item = item['snippet']
                oc.add(DirectoryObject(
                    key=Callback(
                        Channel,
                        oid=item['resourceId']['channelId'],
                        title=item['title']
                    ),
                    title=u'%s' % item['title'],
                    summary=u'%s' % item['description'],
                    thumb=GetThumbFromSnippet(item),
                ))

        if 'nextPageToken' in res:
            oc.add(NextPageObject(
                key=Callback(
                    Subscriptions,
                    uid=uid,
                    title=oc.title2,
                    offset=res['nextPageToken'],
                ),
                title=u'%s' % L('More subscriptions'),
                thumb=ICONS['next']
            ))

    if not len(oc):
        return NoContents()

    return oc


def Search(query, title=L('Search'), s_type='video', offset=0, **kwargs):
    is_video = s_type == 'video'
    res = ApiRequest('search', ApiGetParams(
        part='id' if is_video else 'snippet',
        q=query,
        type=s_type,
        regionCode=GetRegion(),
        videoDefinition='high' if is_video and Prefs['search_hd'] else '',
        offset=offset,
        limit=Prefs['items_per_page'],
        **kwargs
    ))

    if not res or not len(res['items']):
        return NoContents()

    oc = ObjectContainer(
        title2=u'%s' % title,
        replace_parent=bool(offset)
    )

    if is_video:
        ids = []
        for item in res['items']:
            ids.append(item['id']['videoId'])

        AddVideos(oc, ApiGetVideos(ids=ids), extended=Prefs['search_extened'])
    else:
        s_callback = Channel if s_type == 'channel' else Playlist
        s_key = s_type+'Id'

        for item in res['items']:
            oid = item['id'][s_key]
            item = item['snippet']
            oc.add(DirectoryObject(
                key=Callback(
                    s_callback,
                    title=item['title'],
                    oid=oid
                ),
                title=u'%s' % item['title'],
                summary=u'%s' % item['description'],
                thumb=GetThumbFromSnippet(item),
            ))

    if 'nextPageToken' in res:
        oc.add(NextPageObject(
            key=Callback(
                Search,
                query=query,
                title=oc.title2,
                s_type=s_type,
                offset=res['nextPageToken'],
            ),
            title=u'%s' % L('Next page'),
            thumb=ICONS['next']
        ))

    return oc


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
            view_group='details',
            no_cache=True,
            objects=[
                DirectoryObject(
                    key=Callback(MainMenu, complete=True),
                    title=u'%s' % F('codeIs', code),
                    summary=u'%s' % F('enterCodeSite', code, url),
                    tagline=url,
                ),
                DirectoryObject(
                    key=Callback(MainMenu, complete=True),
                    title=u'%s' % L('Authorize'),
                    summary=u'%s' % L('Complete authorization'),
                ),            ]
        )
        return oc

    return ObjectContainer(
        header=u'%s' % L('Error'),
        message=u'%s' % L('Service temporarily unavailable')
    )


###############################################################################
# Common
###############################################################################

def NoContents():
    return ObjectContainer(
        header=u'%s' % L('Error'),
        message=u'%s' % L('No entries found')
    )


def SuccessMessage():
    return ObjectContainer(
        header=u'%s' % L('Success'),
        message=u'%s' % L('Action complete')
    )


def ErrorMessage():
    return ObjectContainer(
        header=u'%s' % L('Error'),
        message=u'%s' % L('An error has occurred')
    )


def NotImplemented(**kwargs):
    return ObjectContainer(
        header=u'%s' % L('Not Implemented'),
        message=u'%s' % L('This function not implemented yet')
    )


def GetRegion():
    return Prefs['region'].split('/')[1]


def GetLanguage():
    return Prefs['language'].split('/')[1]


def GetLimitForOC(oc):
    ret = int(Prefs['items_per_page'])-len(oc)
    return 8 if ret <= 0 else ret


def GetThumbFromSnippet(snippet):
    try:
        return snippet['thumbnails']['high']['url']
    except:
        return ''


def ApiGetVideos(ids=[], title=None, extended=False, **kwargs):
    return ApiRequest('videos', ApiGetParams(
        part='snippet,contentDetails',
        hl=GetLanguage(),
        id=','.join(ids),
        **kwargs
    ))


def ApiGetSystemPlayLists(uid):
    res = ApiRequest('channels', ApiGetParams(
        part='contentDetails',
        hl=GetLanguage(),
        uid=uid,
        id=uid if uid != 'me' else None
    ))

    if res and res['items']:
        return res['items'][0]['contentDetails']['relatedPlaylists']

    return {}


def ApiRequest(method, params, data=None, rmethod=None):
    if not CheckToken():
        return None

    params['access_token'] = Dict['access_token']

    is_change = data or rmethod == 'DELETE'

    try:
        res = HTTP.Request(
            'https://www.googleapis.com/youtube/%s/%s?%s' % (
                YT_VERSION,
                method,
                urlencode(params)
            ),
            headers={'Content-Type': 'application/json; charset=UTF-8'},
            data=None if not data else JSON.StringFromObject(data),
            method=rmethod,
            cacheTime=0 if is_change else CACHE_1HOUR
        ).content
    except Exception as e:
        Log.Debug(str(e))
        return None

    if is_change:
        HTTP.ClearCache()
        return True

    try:
        res = JSON.ObjectFromString(res)
    except:
        return None

    if 'error' in res:
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
