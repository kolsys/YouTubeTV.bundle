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
YT_LIMIT = 50


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
        key=Callback(NotImplemented),
        title=u'%s' % L('What to Watch')
    ))
    oc.add(DirectoryObject(
        key=Callback(NotImplemented),
        title=u'%s' % L('Playlists')
    ))
    oc.add(DirectoryObject(
        key=Callback(NotImplemented),
        title=u'%s' % L('My channel')
    ))
    oc.add(DirectoryObject(
        key=Callback(NotImplemented),
        title=u'%s' % L('History')
    ))
    oc.add(DirectoryObject(
        key=Callback(NotImplemented),
        title=u'%s' % L('Music')
    ))
    oc.add(DirectoryObject(
        key=Callback(NotImplemented),
        title=u'%s' % L('Liked videos')
    ))
    oc.add(InputDirectoryObject(
        key=Callback(
            Search,
            search_type='video',
            title=u'%s' % L('Search Video')
        ),
        title=u'%s' % L('Search'), prompt=u'%s' % L('Search Video')
    ))

    return AddSubscriptions(oc)


@route(PREFIX + '/my/subscriptions')
def MySubscriptions():
    return NotImplemented()


@route(PREFIX + '/channel')
def Channel(id, title):
    return NotImplemented()


@route(PREFIX + '/subscriptions')
def Subscriptions(offset=None):
    oc = ObjectContainer(
        title2=u'%s' % L('Subscriptions'),
        replace_parent=bool(offset)
    )
    return AddSubscriptions(oc, offset, YT_LIMIT)


def AddSubscriptions(oc, offset=None, limit=5):
    res = ApiRequest('subscriptions', {
        'part': 'snippet',
        'mine': 'true',
        'maxResults': limit,
        'order': 'relevance',
        'pageToken': offset if offset else '',
    })

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
                        id=item['resourceId']['channelId'],
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


def ApiRequest(method, params):
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

    Log.Debug(urlencode(params))

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
    Log.Debug(data)
    if 'expires_in' in data:
        data['expires'] = int(time()) + int(data['expires_in'])

    for key, val in data.items():
        Dict[key] = val
