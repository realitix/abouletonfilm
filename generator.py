import os
import os.path
import json
import tmdbsimple as tmdb
from slugify import slugify
from requests import exceptions as rex

HERE = os.path.dirname(os.path.abspath(__file__))

tmdb.API_KEY = os.environ['TMDB_API_KEY']
base_image_url = 'https://image.tmdb.org/t/p/w185_and_h278_bestv2'
latest_id = tmdb.Movies().latest()['id']


def main():
    progress = -1
    # List all id existing
    existing_ids = set()
    for _, _, files in os.walk(os.path.join(HERE, "content/movies")):
        for filename in files:
            if 'gitignore' in filename:
                continue
            id_filename = filename.split('_')[0]
            existing_ids.add(int(id_filename))

    data_notfound = {"draft": "true", "title": "not_found"}

    # Loop througt all movies
    for i in range(latest_id):
        # Check if id exists (don't request in that case)
        if i in existing_ids:
            continue

        current_progress = int(i/latest_id*100)
        if current_progress != progress:
            progress = current_progress
            print("Progress {}%".format(progress))
        
        movie = tmdb.Movies(i)
        try:
            info = movie.info(append_to_response='credits,recommendations,videos', language="fr")
            credits = info['credits']
            reviews = movie.reviews() # need another request because of the language
            recommandations_id = [x['id'] for x in info['recommendations']['results'][:4]]
            videos = info['videos']
        except rex.HTTPError:
            movie_filename = '{}_{}.md'.format(i, "notfound")
            with open(os.path.join(HERE, 'content/movies', movie_filename), 'w') as outfile:
                json.dump(data_notfound, outfile)
            continue
        except Exception:
            raise

        image_url = "/img/default-cover.png"
        if info['poster_path']:
            image_url = base_image_url + info['poster_path']    

        data = {
            'tmdb_id': info['id'],
            'title': info['title'],
            'original_title': info['original_title'],
            'slug_title': slugify(info['title']),
            'date': info['release_date'],
            'genre': ' / '.join([x['name'] for x in info['genres']]),
            'score': str(info['vote_average']) + '/10',
            'synopsis': info['overview'],
            'image': image_url,
            'actors': [x['name'] + " (" + x['character'] + ")" for x in credits['cast']],
            'comments': [
                {'pseudo': x['author'], 'content': x['content']} for x in reviews['results']
            ],
            'recommandations_id': recommandations_id
        }

        movie_filename = '{}_{}.md'.format(data['tmdb_id'], data['slug_title'])
        with open(os.path.join(HERE, 'content/movies', movie_filename), 'w') as outfile:
            json.dump(data, outfile)


if __name__ == '__main__':
    main()
