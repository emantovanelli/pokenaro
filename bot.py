import os
import json
import tweepy
import requests
import sys
from time import sleep
from datetime import datetime, timezone, timedelta
from os.path import exists
from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler(timezone="america/sao_paulo")

RETRIES = 0

def log(message):
    print(message)
    sys.stdout.flush()


def get_remainig_days():
    diferenca = timedelta(hours=-3)
    fuso_horario = timezone(diferenca)
    date_with_timezone = datetime.now().astimezone(fuso_horario)
    dia_salvacao = datetime.fromisoformat("2023-01-01").astimezone(fuso_horario)
    diff = dia_salvacao - date_with_timezone
    return diff.days


def get_pokemon(pokemon_id):
    request_pokemon = requests.get(
        'https://pokeapi.co/api/v2/pokemon/{}'.format(pokemon_id))

    qual_e_esse_pokemon = json.loads(request_pokemon._content)
    return qual_e_esse_pokemon['name'].capitalize(), pokemon_id, qual_e_esse_pokemon['sprites']


def make_tweet(api, dias, pokemon_name, pokemon_id, pokemon_sprite):
    tweet_template = "O {} veio falar que faltam só mais {} dias para o Bolsonaro sair da presidência!\n\n #{} - {}"
    try:
        tweet = tweet_template.format(pokemon_name, dias, pokemon_name, pokemon_id)
        log('Subindo media')
        media = api.media_upload(filename=pokemon_sprite, file=open(pokemon_sprite, 'rb'))

        log('Enviando tweet')
        tweet_result = api.update_status(status=tweet, media_ids=[media.media_id])

        log("Tweet foi enviado")
    except Exception as e:
        log("Error ao criar o tweet")
        raise (e)


def get_pokemons_sprite(quantity):
    for i in range(quantity, 0, -1):
        path = 'pokemons_image/' + str(i) + '.png'
        file_exists = exists(path)
        if not file_exists:
            log('Baixando infos do pokemon: ' + str(i))
            request_pokemon = requests.get(
                'https://pokeapi.co/api/v2/pokemon/{}'.format(i))

            qual_e_esse_pokemon = json.loads(request_pokemon._content)
            log('Infos do {} baixadas'.format(qual_e_esse_pokemon['name']))

            with open(path, 'wb') as handler:
                log('Baixando imagem do {}'.format(qual_e_esse_pokemon['name']))

                if qual_e_esse_pokemon['sprites']['other']['official-artwork']['front_default'] is not None:
                    img_data = requests.get(
                        qual_e_esse_pokemon['sprites']['other']['official-artwork']['front_default']).content
                else:
                    img_data = requests.get(qual_e_esse_pokemon['sprites']['front-default']).content
                handler.write(img_data)
                handler.close()
                log('Imagem do {} baixada'.format(qual_e_esse_pokemon['name']))
        sleep(1)


def get_pokemon_sprite(pokemon_id):
    path = 'pokemons_image/' + str(pokemon_id) + '.png'
    file_exists = exists(path)
    if not file_exists:
        request_pokemon = requests.get(
            'https://pokeapi.co/api/v2/pokemon/{}'.format(pokemon_id))
        qual_e_esse_pokemon = json.loads(request_pokemon._content)
        with open(path, 'wb') as handler:
            img_data = requests.get(
                qual_e_esse_pokemon['sprites']['other']['official-artwork']['front_default']).content
            if img_data is None:
                img_data = requests.get(qual_e_esse_pokemon['sprites']['front-default']).content
            handler.write(img_data)
            handler.close()
    return path


def config_api():
    consumer_key = os.environ.get("CONSUMER_KEY")
    consumer_secret = os.environ.get("CONSUMER_SECRET")
    access_token = os.environ.get("ACCESS_TOKEN")
    access_token_secret = os.environ.get("ACCESS_TOKEN_SECRET")

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)
    return api


@sched.scheduled_job('interval', hours=24)
def main():
    api = config_api()
    log('API configurada')

    days = get_remainig_days()
    log('Dias restantes: {}'.format(days))

    pokemon = get_pokemon(days)
    log('Pokemon do dia: {}'.format(pokemon[0]))
    pokemon_sprite = get_pokemon_sprite(days)

    for tentativa in range(3):
        try:
            make_tweet(api, days, pokemon[0], pokemon[1], pokemon_sprite)
        except Exception as e:
            print(e)
        else:
            break
    else:
        log('make tweet error even with retries')


# if __name__ == '__main__':
#     main()

sched.start()
