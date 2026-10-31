"""Personal ten-track playlists; browser playback, shared server/CLI logic."""
from . import media, uploads
from .module_state import change


def playlist(owner, tracks=None):
    uploads.principal(owner)
    if tracks is not None:
        if not isinstance(tracks,list) or len(tracks)>10:raise ValueError('A playlist supports up to 10 tracks')
        saved=[]
        for track in tracks:
            if not isinstance(track,dict) or set(track)!={'title','settings'} or not isinstance(track['title'],str) or not 1<=len(track['title'].strip())<=100:raise ValueError('Invalid track')
            cfg=media.settings(track['settings']);descriptor=media.describe(owner,cfg,'audio')
            if descriptor['status']!='ok':raise ValueError('Select an audio source for every track')
            saved.append({'title':track['title'].strip(),'settings':cfg})
        change(owner,'music-player','playlist',[],lambda _:(saved,True))
    stored=change(owner,'music-player','playlist',[],lambda old:(old,False))
    result=[]
    for track in stored:
        item=dict(track)
        try:item['media']=media.describe(owner,track['settings'],'audio')
        except (ValueError,LookupError,PermissionError,OSError):item['media']=None
        result.append(item)
    return {'tracks':result,'max_tracks':10}


def run(data):
    if not isinstance(data,dict) or set(data)-{'action','tracks','_state_owner','_state_slot'}:raise ValueError('Invalid playlist input')
    owner=data.get('_state_owner')
    if not owner:raise PermissionError('Authenticated owner required')
    action=data.get('action','get')
    if action not in ('get','set') or (action=='get' and 'tracks' in data) or (action=='set' and 'tracks' not in data):raise ValueError('Use get or set with tracks')
    if action=='set' and not isinstance(data['tracks'],list):raise ValueError('Tracks must be a list')
    return playlist(owner,data['tracks']) if action=='set' else playlist(owner)
