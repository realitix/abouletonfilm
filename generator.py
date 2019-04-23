import os
import os.path
import json
import tmdbsimple as tmdb
from slugify import slugify
from requests import exceptions as rex
from multiprocessing.dummy import Pool as ThreadPool
import tqdm

HERE = os.path.dirname(os.path.abspath(__file__))

tmdb.API_KEY = os.environ['TMDB_API_KEY']
base_image_url = 'https://image.tmdb.org/t/p/w185_and_h278_bestv2'
latest_id = tmdb.Movies().latest()['id']


def main():
    print("latest id: {}".format(latest_id))
    progress = -1
    existing_ids = set()
    # List all id existing
    for _, _, files in os.walk(os.path.join(HERE, "content/movies")):
        for filename in files:
            if 'gitignore' in filename:
                continue
            id_filename = filename.split('_')[0]
            existing_ids.add(int(id_filename))

    all_ids = set(range(latest_id))
    non_existing_ids = all_ids - existing_ids
    compute_parrallel(non_existing_ids)


def compute_parrallel(ids, threads=4):
    pool = ThreadPool(threads)
    for _ in tqdm.tqdm(pool.imap_unordered(compute, ids), total=len(ids)):
        pass
    # pool.map(compute, ids)
    # pool.close()
    # pool.join()


def compute(i):
    data_notfound = {"draft": "true", "title": "not_found"}
    
    movie = tmdb.Movies(i)
    try:
        info = movie.info(append_to_response='credits,recommendations,videos,reviews', language="fr")
        credits = info['credits']
        reviews = info['reviews']
        recommandations_id = [x['id'] for x in info['recommendations']['results'][:4]]
        videos = info['videos']
        synopsis = info['overview']
        title = info['title']
        youtube_key = "notfound"
        if videos['results']:
            youtube_key = videos['results'][0]['key']

        # check fr
        info_fr = movie.info(language="fr")
        if info_fr['overview']:
            synopsis = info_fr['overview']
        if info_fr['title']:
            title = info_fr['title']
    except rex.HTTPError:
        movie_filename = '{}_{}.md'.format(i, "notfound")
        with open(os.path.join(HERE, 'content/movies', movie_filename), 'w') as outfile:
            json.dump(data_notfound, outfile)
        return
    except Exception:
        raise

    image_url = "/img/default-cover.png"
    if info['poster_path']:
        image_url = base_image_url + info['poster_path']    

    data = {
        'tmdb_id': info['id'],
        'title': title,
        'original_title': info['original_title'],
        'slug_title': slugify(title),
        'date': info['release_date'],
        'genre': ' / '.join([x['name'] for x in info['genres']]),
        'score': str(info['vote_average']) + '/10',
        'synopsis': info['overview'],
        'image': image_url,
        'actors': [x['name'] + " (" + x['character'] + ")" for x in credits['cast']],
        'comments': [
            {'pseudo': x['author'], 'content': x['content']} for x in reviews['results']
        ],
        'recommandations_id': recommandations_id,
        'youtube_key': youtube_key
    }

    movie_filename = '{}_{}.md'.format(data['tmdb_id'], data['slug_title'])
    with open(os.path.join(HERE, 'content/movies', movie_filename), 'w') as outfile:
        json.dump(data, outfile)


if __name__ == '__main__':
    main()
