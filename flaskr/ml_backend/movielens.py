"""
Scripts to help load the movielens dataset into Python classes
"""
#!/bin/python
import re

# Read data/README to get more info on these data structures
class User:
    def __init__(self, id, age, sex, occupation, zip):
        self.id = int(id)
        self.age = int(age)
        self.sex = sex
        self.occupation = occupation
        self.zip = zip
        self.avg_r = 0.0

class ModernUser:
    def __init__(self, id):
        self.id = int(id)
        self.avg_r = 0.0

# Read data/README to get more info on these data structures
class Item:
    def __init__(self, id, title, release_date, video_release_date, imdb_url, \
    unknown, action, adventure, animation, childrens, comedy, crime, documentary, \
    drama, fantasy, film_noir, horror, musical, mystery ,romance, sci_fi, thriller, war, western):
        self.id = int(id)
        self.title = title
        self.release_date = release_date
        self.video_release_date = video_release_date
        self.imdb_url = imdb_url
        self.unknown = int(unknown)
        self.action = int(action)
        self.adventure = int(adventure)
        self.animation = int(animation)
        self.childrens = int(childrens)
        self.comedy = int(comedy)
        self.crime = int(crime)
        self.documentary = int(documentary)
        self.drama = int(drama)
        self.fantasy = int(fantasy)
        self.film_noir = int(film_noir)
        self.horror = int(horror)
        self.musical = int(musical)
        self.mystery = int(mystery)
        self.romance = int(romance)
        self.sci_fi = int(sci_fi)
        self.thriller = int(thriller)
        self.war = int(war)
        self.western = int(western)

class ModernItem:
    def __init__(self, id, title, action, adventure, animation, childrens, comedy, crime, documentary, drama,\
    fantasy, film_noir, horror, musical, mystery ,romance, sci_fi, thriller, war, western, no_genre):
        self.id = int(id)
        self.title = title
        self.action = int(action)
        self.adventure = int(adventure)
        self.animation = int(animation)
        self.childrens = int(childrens)
        self.comedy = int(comedy)
        self.crime = int(crime)
        self.documentary = int(documentary)
        self.drama = int(drama)
        self.fantasy = int(fantasy)
        self.film_noir = int(film_noir)
        self.horror = int(horror)
        self.musical = int(musical)
        self.mystery = int(mystery)
        self.romance = int(romance)
        self.sci_fi = int(sci_fi)
        self.thriller = int(thriller)
        self.war = int(war)
        self.western = int(western)
        self.no_genre = int(no_genre)

# Read data/README to get more info on these data structures
class Rating:
    def __init__(self, user_id, item_id, rating, time):
        self.user_id = int(user_id)
        self.item_id = int(item_id)
        self.rating = float(rating)
        self.time = time

class Link:
    id_links = {}
    def __init__(self, movie_id, imdb_id, tmdb_id):
        self.movie_id = int(movie_id)
        if imdb_id == '':
            imdb_id  = 0
        self.item_id = int(imdb_id)
        if tmdb_id == '':
            tmdb_id = 0
        self.tmdb_id = int(tmdb_id)
        self.id_links[int(movie_id)] = int(imdb_id)

# The dataset class helps you to load files and create User, Item and Rating objects
class Dataset:
    def load_users(self, file, u):
        f = open(file, "r", encoding="latin-1")
        text = f.read()
        entries = re.split("\n+", text)
        for entry in entries:
            e = entry.split('|', 5)
            if len(e) == 5:
                u.append(User(e[0], e[1], e[2], e[3], e[4]))
        f.close()

    def load_items(self, file, i):
        f = open(file, "r", encoding="latin-1")
        text = f.read()
        entries = re.split("\n+", text)
        for entry in entries:
            e = entry.split('|', 24)
            if len(e) == 24:
                i.append(Item(e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7], e[8], e[9], e[10], \
                e[11], e[12], e[13], e[14], e[15], e[16], e[17], e[18], e[19], e[20], e[21], \
                e[22], e[23]))
        f.close()
    def load_new_items(self, file, i):
        genres = {"Action":0, "Adventure":0, "Animation":0, "Children's":0, "Comedy":0, "Crime":0, "Documentary":0, "Drama":0, \
        "Fantasy":0, "Film-Noir":0, "Horror":0, "Musical":0, "Mystery":0, "Romance":0, "Sci-Fi":0, "Thriller":0, "War":0, "Western":0, "(no genres listed)":0
        }
        f = open(file, "r", encoding="latin-1")
        text = f.read()
        entries = re.split("\n+", text)
        count = 0
        for entry in entries:
            e = entry.split('\t', 3)
            if len(e) == 3:
                genre = e[2].split('|')
                for g in genre:
                    genres[g] = 1
                val = [value for (key,value) in sorted(genres.items())]
                if e[0] != 'movieId':
                    #print(count)
                    i.append(ModernItem(e[0], e[1], val[0], val[1], val[2], val[3], val[4], val[5], val[6], val[7], val[8], val[9], val[10], \
                    val[11], val[12], val[13], val[14], val[15], val[16], val[17], val[18]))
                    #count += 1
        f.close()


    def load_ratings(self, file, r):
        f = open(file, "r")
        text = f.read()
        entries = re.split("\n+", text)
        for entry in entries:
            e = entry.split('\t', 4)
            if len(e) == 4:
                r.append(Rating(e[0], e[1], e[2], e[3]))
        f.close()

    def load_new_users(self, file, u):
        users = {}
        f = open(file,"r")
        text = f.read()
        entries = re.split("\n+", text)
        for entry in entries:
            e = entry.split(',', 4)
            if len(e) == 4 and e[0] not in users.keys():
                users[e[0]] = 1
                u.append(ModernUser(e[0]))
        f.close()

    def load_links(self, file, l):
        f = open(file, "r")
        text = f.read()
        entries = re.split("\n+", text)
        for entry in entries:
            e = entry.split(',', 3)
            if len(e) == 3 and e[0] != "movieId":
                l.append(Link(e[0], e[1], e[2]))
        f.close()
