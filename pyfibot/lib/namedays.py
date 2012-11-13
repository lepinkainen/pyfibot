# Finnish name days by chiman 9/2004

import time

namedays = []
# January
namedays.append(['-', 'Aapeli', 'Elmo, Elmer', 'Ruut', 'Lea, Leea', 'Harri',
                 'Aukusti, Aku, August', 'Hilppa, Titta',
                 'Veikko, Veli, Veijo', 'Nyyrikki', 'Kari, Karri', 'Toini',
                 'Nuutti', 'Sakari, Saku', 'Solja', 'Ilmari, Ilmo',
                 'Toni, Anttoni, Antto, Anton', 'Laura',
                 'Heikki, Henrik, Henrikki, Henri', 'Henna, Henni, Henriikka',
                 'Aune, Oona, Auni', 'Visa', 'Eine, Eini, Enni', 'Senja',
                 'Paavo, Pauli, Paavali, Paul', 'Joonatan', 'Viljo',
                 'Kaarlo, Kalle, Kaarle, Mies', 'Valtteri', 'Irja', 'Alli'])
# February
namedays.append(['Riitta', 'Aamu', 'Valo', 'Armi', 'Asser',
                 'Terhi, Teija, Tiia, Tea, Terhikki', 'Riku, Rikhard',
                 'Laina', 'Raija, Raisa', 'Elina, Elna, Ella, Ellen',
                 'Talvikki', 'Elma, Elmi', 'Sulo, Sulho', 'Voitto, Tino',
                 'Sipi, Sippo', 'Kai', 'Väinö, Väinämö', 'Kaino', 'Eija',
                 'Heli, Helinä, Heljä, Hely', 'Keijo',
                 'Tuulikki, Tuuli, Tuulia', 'Aslak', 'Matti, Mattias',
                 'Tuija, Tuire', 'Nestori', 'Torsti', 'Onni', '-'])
# March
namedays.append(['Alpo, Alvi, Alpi', 'Virve, Virva', 'Kauko',
                 'Ari, Arsi, Atro', 'Laila, Leila', 'Tarmo', 'Tarja, Taru',
                 'Vilppu', 'Auvo', 'Aurora, Aura, Auri', 'Kalervo',
                 'Reijo, Reko', 'Erno, Tarvo, Ernesti', 'Matilda, Tilda',
                 'Risto', 'Ilkka', 'Kerttu, Kerttuli', 'Eetu, Edvard',
                 'Jooseppi, Juuso, Joosef, Josefiina',
                 'Aki, Joakim, Kim, Jaakkima', 'Pentti', 'Vihtori', 'Akseli',
                 'Kaapo, Gabriel, Kaapro, Kaappo', 'Aija',
                 'Manu, Immanuel, Manne, Immo', 'Sauli, Saul', 'Armas',
                 'Joonas, Jouni, Joni, Joona, Jonne, Jonni', 'Usko, Tage',
                 'Irma, Irmeli'])
# April
namedays.append(['Raita, Pulmu', 'Pellervo', 'Sampo', 'Ukko',
                 'Irene, Irina, Ira, Iro',
                 'Vilho, Ville, Viljami, Vilhelm, Vili', 'Allan, Ahvo',
                 'Suoma, Suometar', 'Elias, Eelis, Eljas', 'Tero', 'Verna',
                 'Julius, Julia', 'Tellervo', 'Taito', 'Linda, Tuomi',
                 'Jalo, Patrik', 'Otto', 'Valto, Valdemar', 'Pälvi, Pilvi',
                 'Lauha', 'Anssi, Anselmi', 'Alina',
                 'Yrjö, Jyrki, Jyri, Yrjänä, Jori', 'Pertti, Albert, Altti',
                 'Markku, Markus, Marko', 'Terttu, Teresa', 'Merja',
                 'Ilpo, Ilppo, Tuure', 'Teijo',
                 'Mirja, Mirva, Mira, Miia, Mirjami, Mirka, Mirkka'])
# May
namedays.append(['Vappu, Valpuri', 'Vuokko, Viivi', 'Outi', 'Ruusu, Roosa',
                 'Maini', 'Ylermi', 'Helmi, Kastehelmi', 'Heino', 'Timo',
                 'Aino, Aina, Aini, Ainikki', 'Osmo', 'Lotta',
                 'Kukka, Floora', 'Tuula', 'Sofia, Sonja, Sohvi',
                 'Esteri, Essi, Ester', 'Maila, Maili, Mailis',
                 'Erkki, Eero, Eerikki',
                 'Emilia, Milja, Emma, Emmi, Milla, Amalia',
                 'Lilja, Karoliina, Lilli', 'Kosti, Kosta, Konstantin',
                 'Hemminki, Hemmo', 'Lyydia, Lyyli', 'Tuukka, Touko',
                 'Urpo', 'Minna, Vilma, Vilhelmiina, Mimmi', 'Ritva',
                 'Alma', 'Oiva, Oivi', 'Pasi', 'Helka, Helga'])
# June
namedays.append(['Teemu, Nikodemus', 'Venla', 'Orvokki', 'Toivo', 'Sulevi',
                 'Kustaa, Kyösti, Kustavi', 'Suvi', 'Salomo, Salomon',
                 'Ensio', 'Seppo', 'Impi, Immi', 'Esko', 'Raili, Raila',
                 'Kielo', 'Vieno, Viena', 'Päivi, Päivikki, Päivä', 'Urho',
                 'Tapio', 'Siiri', 'Into', 'Ahti, Ahto',
                 'Paula, Liina, Pauliina', 'Aatto, Aatu, Aadolf',
                 'Johannes, Juhani, Juha, Juho, Jukka, Jussi, Janne, Jani,' +
                 ' Juhana', 'Uuno',
                 'Jorma, Jarmo, Jarkko, Jarno, Jere, Jeremias',
                 'Elviira, Elvi', 'Leo',
                 'Pietari, Pekka, Petri, Petra, Petteri, Pekko',
                 'Päiviö, Päivö'])
# July
namedays.append(['Aaro, Aaron', 'Maria, Mari, Maija, Meeri, Maaria, Marika,' +
                 ' Maiju, Maikki, Kukka-Maaria', 'Arvo', 'Ulla, Ulpu',
                 'Unto, Untamo', 'Esa, Esaias', 'Klaus, Launo',
                 'Turo, Turkka', 'Ilta, Jasmin', 'Saima, Saimi',
                 'Elli, Noora, Nelli, Eleonoora', 'Hermanni, Herkko, Herman',
                 'Ilari, Lari, Joel', 'Aliisa', 'Rauni, Rauna', 'Reino',
                 'Ossi, Ossian', 'Riikka', 'Saara, Sari, Salli, Salla, Sara',
                 'Marketta, Maarit, Reeta, Maaret, Reetta, Margareeta',
                 'Johanna, Hanna, Jenni, Jenna, Hannele, Hanne, Jonna',
                 'Leena, Leeni, Lenita, Mataleena', 'Oili, Olga',
                 'Kirsti, Tiina, Kirsi, Kristiina, Krista',
                 'Jaakko, Jaakoppi, Jaakob', 'Martta', 'Heidi', 'Atso',
                 'Olavi, Olli, Uolevi, Uoti', 'Asta', 'Helena, Elena'])
# August
namedays.append(['Maire', 'Kimmo', 'Linnea, Nea, Vanamo', 'Veera',
                 'Salme, Sanelma', 'Toimi, Keimo', 'Lahja',
                 'Sylvi, Sylvia, Silva', 'Erja, Eira', 'Lauri, Lasse, Lassi',
                 'Sanna, Susanna, Sanni', 'Klaara', 'Jesse',
                 'Onerva, Kanerva',
                 'Marjatta, Marja, Jaana, Marjo, Marjut, Marjaana, Marjukka' +
                 ', Marita, Maritta, Marianne, Marianna', 'Aulis', 'Verneri',
                 'Leevi', 'Mauno, Maunu', 'Samuli, Sami, Samuel, Samu',
                 'Soini, Veini', 'Iivari, Iivo', 'Varma, Signe', 'Perttu',
                 'Loviisa', 'Ilma, Ilmi, Ilmatar', 'Rauli', 'Tauno',
                 'Iines, Iina, Inari', 'Eemil, Eemeli', 'Arvi'])
# September
namedays.append(['Pirkka', 'Sinikka, Sini', 'Soili, Soile, Soila', 'Ansa',
                 'Mainio', 'Asko', 'Arho, Arhippa', 'Taimi', 'Eevert, Isto',
                 'Kalevi, Kaleva', 'Santeri, Ali, Ale, Aleksanteri',
                 'Valma, Vilja', 'Orvo', 'Iida', 'Sirpa',
                 'Hellevi, Hillevi, Hille, Hilla', 'Aili, Aila',
                 'Tyyne, Tytti, Tyyni', 'Reija', 'Varpu, Vaula', 'Mervi',
                 'Mauri', 'Mielikki', 'Alvar, Auno', 'Kullervo', 'Kuisma',
                 'Vesa', 'Arja', 'Mikko, Mika, Mikael, Miika, Miikka',
                 'Sorja, Sirja'])
# October
namedays.append(['Rauno, Rainer, Raine, Raino', 'Valio', 'Raimo',
                 'Saila, Saija', 'Inkeri, Inka', 'Minttu, Pinja',
                 'Pirkko, Pirjo, Piritta, Pirita, Birgitta', 'Hilja',
                 'Ilona', 'Aleksi, Aleksis', 'Otso, Ohto', 'Aarre, Aarto',
                 'Taina, Tanja, Taija', 'Elsa, Else, Elsi', 'Helvi, Heta',
                 'Sirkka, Sirkku', 'Saini, Saana', 'Satu, Säde', 'Uljas',
                 'Kauno, Kasperi', 'Ursula', 'Anja, Anita, Anniina, Anitta',
                 'Severi', 'Asmo', 'Sointu', 'Amanda, Niina, Manta',
                 'Helli, Hellä, Hellin, Helle', 'Simo', 'Alfred, Urmas',
                 'Eila', 'Artturi, Arto, Arttu'])
# November
namedays.append(['Pyry, Lyly', 'Topi, Topias', 'Terho', 'Hertta', 'Reima',
                 'Kustaa Aadolf', 'Taisto', 'Aatos', 'Teuvo', 'Martti',
                 'Panu', 'Virpi', 'Ano, Kristian', 'Iiris',
                 'Janika, Janita, Janina', 'Aarne, Aarno, Aarni',
                 'Eino, Einar, Einari', 'Tenho, Jousia',
                 'Liisa, Eliisa, Elisa, Elisabet, Liisi', 'Jalmari, Jari',
                 'Hilma', 'Silja, Selja', 'Ismo', 'Lempi, Lemmikki, Sivi',
                 'Katri, Kaisa, Kaija, Katja, Kaarina, Katariina, Kati' +
                 ', Kaisu, Riina', 'Sisko', 'Hilkka', 'Heini', 'Aimo',
                 'Antti, Antero, Atte'])
# December
namedays.append(['Oskari', 'Anelma, Unelma', 'Vellamo, Meri', 'Airi, Aira',
                 'Selma', 'Niilo, Niko, Niklas', 'Sampsa', 'Kyllikki, Kylli',
                 'Anna, Anne, Anni, Anu, Annikki, Anneli, Annukka, Annika',
                 'Jutta', 'Taneli, Tatu, Daniel', 'Tuovi', 'Seija', 'Jouko',
                 'Heimo', 'Auli, Aulikki', 'Raakel', 'Aapo, Aappo, Rami',
                 'Iikka, Iiro, Iisakki, Isko', 'Benjamin, Kerkko',
                 'Tuomas, Tuomo, Tommi, Tomi', 'Raafael', 'Senni',
                 'Aatami, Eeva, Eevi, Eveliina', '-', 'Tapani, Teppo, Tahvo',
                 'Hannu, Hannes', 'Piia', 'Rauha', 'Daavid, Taavetti, Taavi',
                 'Sylvester, Silvo'])

def wday_str(i):
    i = i % 7
    return ['su', 'ma', 'ti', 'ke', 'to', 'pe', 'la'][i]

def get_nameday(month, day):
    return namedays[month - 1][day - 1]

def next_namedays(n):
    """Return list of nameday structs for n days

    Each struct has:
       - month
       - day
       - weekday abbreviation of two letters in Finnish
       - names for that date

    """
    
    secs = [86400 * x for x in range(n)]

    dates = [time.localtime(time.time() + x) for x in secs]

    month = [int(time.strftime('%m', x)) for x in dates]
    day = [int(time.strftime('%d', x)) for x in dates]
    wday = [int(time.strftime('%w', x)) for x in dates]

    names = [[] for x in range(n)]
    for i in range(n):
        names[i].append(month[i])
        names[i].append(day[i])
        names[i].append(wday_str(wday[i]))
        names[i].append(get_nameday(month[i], day[i]))
        
    return names

if __name__ == '__main__':

    # Output:
    # su: Valma, Vilja
    # ma: Orvo
    # ti: Iida

    for row in next_namedays(3):
        print '%s: %s' % (row[2], row[3])  # weekday and names
