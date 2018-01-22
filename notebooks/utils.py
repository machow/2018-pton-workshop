
# Billboard API ---------------------------------------------------------------

headers = {
        'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/63.0.3239.132 Safari/537.36'
                       )
        }

from requests import request

def get_billboard(url):
    """Get the billboard data from a URL.
    
    Example:
        get_billboard("http://billboard.modulo.site/search/artist?q=kanye")

    Note:
        See http://billboard.modulo.site/ for details.

    """
    r = request('GET',
            url = url,
            headers = headers
           )

    return r.json()


# Plots -----------------------------------------------------------------------

import pandas as pd
from plotnine import *

# Billboard ----

def plot_hits(songs):
    if isinstance(songs, dict) and (songs.get('songs') or songs.get('albums')):
        raise "Did you remember to get only the song data?"

    df = pd.DataFrame(songs)
    df['highest_rank'] = df['highest_rank'].astype(int)
    df['weeks_on_chart'] = df['weeks_on_chart'].astype(int)

    return ggplot(df, aes(x = 'weeks_on_chart', y = 'highest_rank')) \
        + geom_point() \
        + geom_text(aes(label = 'song_name'), nudge_x = .5, size = 6, ha = 'left')

# Spotify ----

def melt_features(feats, columns):
    columns = list(columns)
    df = pd.DataFrame(feats)
    melted = pd.melt(df, id_vars = 'name', value_vars = columns, var_name = 'feature')
    melted['name'] = melted['name'].apply(lambda s: s[:15] + (s[15:] and '...'))
    return melted

def plot_features(feats, columns = ('danceability', 'energy'), title = 'Add a Title'):
    """Plot features for every song in an album

    Arguments:
        feats: a list of song features returned by get_spotify_features
        columns: a list of names of features to plot
        title: a title for the plot
    """
    melted = melt_features(feats, columns)
    return ggplot(melted, aes('feature', 'value', fill = 'feature')) + \
        geom_bar(stat = 'identity') + \
        facet_wrap('~ name', ncol = 4) + \
        ggtitle(title) + \
        theme(axis_text_x = element_blank())

def plot_avg_features(feats, columns = ('danceability', 'energy'), title = 'Add a Title'):
    """Plot averaged features across songs in an album

    Arguments:
        feats: a list of song features returned by get_spotify_features
        columns: a list of names of features to plot
        title: a title for the plot
    """
    melted = melt_features(feats, columns)
    avg = melted.groupby('feature', as_index = False)['value'].mean()
    return ggplot(avg, aes('feature', 'value', fill = 'feature')) + \
        geom_bar(stat = 'identity') + \
        ggtitle(title) + \
        theme(axis_text_x = element_text(angle = 45))
    

# Spotify API -----------------------------------------------------------------

from requests import request, HTTPError
import spotipy
sp = None

# This is a special function called a wrapper ----
# it checks that the user ran login_to_spotify (which sets the global sp variable)
from functools import wraps

def check_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        assert sp is not None, "Did you use login_to_spotify() yet?"
        return f(*args, **kwargs)
    return wrapper
# ----

def login_to_spotify(auth = None):
    """
    Log in to spotify. You can just use login_to_spotify()
    
    Arguments:
        auth: a spotify authorization token (not needed during workshop)
    """
    if auth is None:
        try:
            r = request('GET', 'https://s3.amazonaws.com/mc-workshops/spotify_token.txt')
            r.raise_for_status()
            auth = r.text.strip()
        except HTTPError:
            raise HTTPError("Logging in to spotify requires a special token only available during workshop")
        
    global sp
    sp = spotipy.Spotify(auth = auth)
    return sp

@check_login
def search_spotify_album(album):
    """
    Print possible spotify matches for an album.
    
    Arguments:
        album: the name of the album

    Example:
        search_spotify_album("Faster Than the Speed of Night")
    """
    q = sp.search(album, type = 'album')
    for ii, item in enumerate(q['albums']['items']):
        print(ii + 1, '----')
        print('name: ', item['name'])
        print('artist: ', item['artists'][0]['name'])
        print('id: ', item['id'])

@check_login
def get_spotify_features(album_id):
    """Get features for all tracks in an album.

    Arguments:
        album_id: an album's id.

    Note:
        You can search for an album, using search_spotify_album
    """
    # get album tracks
    album_tracks = sp.album_tracks(album_id)
    item_ids = {item['id']: item['name'] for item in album_tracks['items']}
    feats = sp.audio_features(list(item_ids.keys()))
    for entry in feats:
        entry['name'] = item_ids[entry['id']]

    return feats



