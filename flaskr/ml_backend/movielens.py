"""
Scripts to help load the movielens dataset into Python classes
"""
#!/bin/python
import re

# Read data/README to get more info on these data structures
class User:
    def __init__(self, id, age, sex, occupation, zip, cluster_num=None, rating_clusters=None, pcs_score=None):
        self.id = int(id)
        self.age = int(age)
        self.sex = sex
        self.occupation = occupation
        self.zip = zip
        self.avg_r = 0.0
        if pcs_score:
            self.pcs_score = pcs_score
        if cluster_num:
            self.cluster_num = cluster_num
        if rating_clusters:
            self.rating_clusters = rating_clusters

    def __str__(self) -> str:
        return f""" User ID: {self.id}, Age: {self.age}, Sex: {self.sex}, Occupation: {self.occupation}, Zip: {self.zip}, Average Rating: {self.avg_r} \n"""

class ModernUser:
    def __init__(self, id, pcs_score=None, rating_clusters=None):
        self.id = int(id)
        self.avg_r = 0.0
        if rating_clusters:
            self.rating_clusters = rating_clusters
        if pcs_score:
            self.pcs_score = pcs_score

    def __str__(self) -> str:
        return f""" User ID: {self.id}, Average ID: {self.avg_r} \n"""

# Read data/README to get more info on these data structures
class Item:
    def __init__(self, id=None, title=None, release_date=None, video_release_date=None, imdb_url=None, \
    unknown=None, action=None, adventure=None, animation=None, childrens=None, comedy=None, crime=None, documentary=None, \
    drama=None, fantasy=None, film_noir=None, horror=None, musical=None, mystery=None, romance=None, sci_fi=None, thriller=None, war=None, western=None, arg_list=None):
        if arg_list != None:
            self.id = int(arg_list[0])
            self.cluster_num = int(arg_list[1])
            self.title = arg_list[2]
            self.release_date = arg_list[3]
            self.video_release_date = arg_list[4]
            self.imdb_url = arg_list[5]
            self.unknown = int(arg_list[6])
            self.action = int(arg_list[7])
            self.adventure = int(arg_list[8])
            self.animation = int(arg_list[9])
            self.childrens = int(arg_list[10])
            self.comedy = int(arg_list[11])
            self.crime = int(arg_list[12])
            self.documentary = int(arg_list[13])
            self.drama = int(arg_list[14])
            self.fantasy = int(arg_list[15])
            self.film_noir = int(arg_list[16])
            self.horror = int(arg_list[17])
            self.musical = int(arg_list[18])
            self.romance = int(arg_list[19])
            self.sci_fi = int(arg_list[20])
            self.thriller = int(arg_list[21])
            self.war = int(arg_list[22])
            self.western = int(arg_list[23])
            return

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


    def __str__(self) -> str:
        return f""" Movie ID: {self.id}, Movie Title: {self.title} \n"""


class ModernItem:
    def __init__(self, id=None, title=None, action=None, adventure=None, animation=None, childrens=None, comedy=None, crime=None, documentary=None, drama=None,\
    fantasy=None, film_noir=None, horror=None, musical=None, mystery=None, romance=None, sci_fi=None, thriller=None, war=None, western=None, no_genre=None, arg_list=None):
        if arg_list != None:
            self.id = int(arg_list[0])
            self.cluster_num = int(arg_list[1])
            self.title = arg_list[2]
            self.action = int(arg_list[3])
            self.adventure = int(arg_list[4])
            self.animation = int(arg_list[5])
            self.childrens = int(arg_list[6])
            self.comedy = int(arg_list[7])
            self.crime = int(arg_list[8])
            self.documentary = int(arg_list[9])
            self.drama = int(arg_list[10])
            self.fantasy = int(arg_list[11])
            self.film_noir = int(arg_list[12])
            self.horror = int(arg_list[13])
            self.imax = int(arg_list[14])
            self.musical = int(arg_list[15])
            self.mystery = int(arg_list[16])
            self.romance = int(arg_list[17])
            self.sci_fi = int(arg_list[18])
            self.thriller = int(arg_list[19])
            self.war = int(arg_list[20])
            self.western = int(arg_list[21])
            self.no_genre = int(arg_list[22])
            return
        
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
        #self.imax = int(imax)
        self.musical = int(musical)
        self.mystery = int(mystery)
        self.romance = int(romance)
        self.sci_fi = int(sci_fi)
        self.thriller = int(thriller)
        self.war = int(war)
        self.western = int(western)
        self.no_genre = int(no_genre)

    def __str__(self) -> str:
        return f"""Modern Movie ID: {self.id}, Modern Movie Title: {self.title}"""

# Read data/README to get more info on these data structures
class Rating:
    def __init__(self, user_id, item_id, rating, time, rating_id=None):
        self.user_id = int(user_id)
        self.item_id = int(item_id)
        self.rating = float(rating)
        self.time = time
        if rating_id != None:
            self.rating_id = rating_id
    
    def __str__(self) -> str:
        return f""" User ID: {self.user_id}, Item ID: {self.item_id}, Rating: {self.rating}, Time: {self.time}, Rating ID: {self.rating_id}\n"""

class Link:
    id_links = {}
    def __init__(self, movie_id, imdb_id, tmdb_id, link_id=None):
        self.movie_id = int(movie_id)
        if imdb_id == '':
            imdb_id  = 0
        self.imdb_id = int(imdb_id)
        if tmdb_id == '':
            tmdb_id = 0
        self.tmdb_id = int(tmdb_id)
        self.id_links[int(movie_id)] = int(imdb_id)
        self.link_id = link_id
    
    def __str__(self) -> str:
        return f"""Movie ID: {self.movie_id}, IMDB ID: {self.imdb_id}, TMDB ID: {self.tmdb_id}, Link ID: {self.link_id} \n"""

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
