#!/usr/bin/env python3

# {{{ Imports
import asyncio
import logging

import aiohttp
import pyxivapi
from pyxivapi.models import Filter, Sort

import os

import discord
from dotenv import load_dotenv

from discord.ext import commands
from discord.utils import get

from PIL import Image, ImageDraw, ImageFont
import urllib

import io
import random
import json

# }}}

# my id: 253031407750873088

# Get Guild Info and API Keys
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
xivapi_key = os.getenv('API_KEY')

with open('ids.json') as json_file:
    ids = json.load(json_file)

with open('player_names.json') as json_file:
    names = json.load(json_file)

with open('stats.json') as json_file:
    stats = json.load(json_file)
'''
stats = {}
stats['use_count'] = 82
'''

#  {{{ API Commands

# count command usage
async def increase_use_count():
    stats['use_count'] += 1
    with open('stats.json', 'w') as outfile:
        json.dump(stats, outfile, indent=4)

# lookup name
async def lookup_name(d_username):
    if d_username in names:
        return names[d_username]
    else:
        return ""


# store char name
async def store_name(d_username, world, forename, surname):
    # name to be stored
    written_id = world + " " + forename + " " + surname
    written_id = written_id.lower()
    if d_username not in names:
        names[d_username] = written_id
        with open('player_names.json', 'w') as outfile:
            json.dump(names, outfile, indent=4)
        return '0'
    elif d_username in names:
        if names[d_username] == written_id:
            return '2'
        else:
            old_name = names[d_username]
            names[d_username] = written_id
            with open('player_names.json', 'w') as outfile:
                json.dump(names, outfile, indent=4)
            return old_name
    else:
        return '1'

    # return codes: [0] updated [1] error [name] say names been updated


# make_card.py
async def get_player_card(world, forename, surname):

    # player class
    class Player:
        def __init__(self, name, img_url, server, race, clan, deity, gc, gc_rank, jobs, active_class, exp_lvl, exp_lvl_max, active_class_lvl, fc):
            self.name = name
            self.img_url = img_url
            self.server = server
            self.race = race
            self.clan = clan
            self.deity = deity
            self.gc = gc
            self.gc_rank = gc_rank
            self.fc = fc
            self.jobs = jobs
            self.active_class = active_class
            self.active_class_lvl = active_class_lvl
            self.exp_lvl = exp_lvl
            self.exp_lvl_max = exp_lvl_max

    # API Commands
    async def get_player_info(world, forename, surname):
        client = pyxivapi.XIVAPIClient(api_key=xivapi_key)
        # store ids
        '''
        with open('ids.json') as json_file:
            ids = json.load(json_file)
        '''
        #ids = {}
        written_id = world + " " + forename + " " + surname
        written_id = written_id.lower()

        if (written_id in ids):
            id = ids[written_id]
        else:
            # Search Lodestone for a character
            character = await client.character_search(
                world=world,
                forename=forename,
                surname=surname
            )
            # TODO Check for error
            id = character['Results'][0]['ID']
            ids[written_id] = id
            with open('ids.json', 'w') as outfile:
                json.dump(ids, outfile, indent=4)
            #name = character['Results'][0]['Name']
            #server = character['Results'][0]['Server']

        character = await client.character_by_id(
            lodestone_id=id,
            extended=False,
            include_freecompany=True,
            include_classjobs=True
            )

        name = character['Character']['Name']
        server = character['Character']['Server'] + " (" + character['Character']['DC'] + ")"
        img = character['Character']['Portrait']
        race = character['Character']['Race']
        clan = character['Character']['Tribe']
        deity = character['Character']['GuardianDeity']
        #fc_id = character['Character']['FreeCompanyID']
        jobs = character['Character']['ClassJobs']
        active_class = character['Character']['ActiveClassJob']['UnlockedState']['Name']
        exp_lvl = character['Character']['ActiveClassJob']['ExpLevel']
        exp_lvl_max = character['Character']['ActiveClassJob']['ExpLevelMax']
        active_class_lvl = character['Character']['ActiveClassJob']['Level']
        #print(character['FreeCompany']['Name'])
        if character['FreeCompany'] == None:
            fc_name = "-"
        else:
            fc_name = character['FreeCompany']['Name']

        if character['Character']['GrandCompany'] == None:
            gc = -1
            gc_rank = -1
        else:
            gc = character['Character']['GrandCompany']['NameID']
            gc_rank = character['Character']['GrandCompany']['RankID']



        await client.session.close()
        return Player(name, img, server, race, clan, deity, gc, gc_rank, jobs, active_class, exp_lvl, exp_lvl_max, active_class_lvl, fc_name)

    #img = await get_player_info('Goblin', 'Valerian', 'Kane')
    #loop = asyncio.get_event_loop()
    #toon = await get_player_info('Goblin', 'Valerian', 'Kane')
    toon = await get_player_info(world, forename, surname)
    urllib.request.urlretrieve(toon.img_url, "char_img.jpg")


    # Test Character information
    #print("img is", img)

    # Import images
    #char = Image.open("fluffy.jpg")
    char = Image.open("char_img.jpg")
    background = Image.open("card_background.png")
    textboxes = Image.open("text_boxes4.png")
    frame = Image.open("full-border.png")

    # Create Overlay
    im2 = Image.new('RGBA', (char.width + background.width, char.height))
    im2.paste(textboxes, (char.width + background.width - textboxes.width - 20, 20), mask=textboxes)

    # Create Background
    im = Image.new('RGB', (char.width + background.width, char.height))
    im.paste(char, (0, 0))
    im.paste(background, (char.width, 0))

    # Create Transparency
    bands = list(im2.split())
    if len(bands) == 4:
        # Assuming alpha is the last band
        bands[3] = bands[3].point(lambda x: x*0.85)
    im2= Image.merge(im2.mode, bands)

    # Paste Overlay onto background
    im.paste(im2, (0, 0), im2)

    # top corner of text box
    draw = ImageDraw.Draw(im)
    font_name = "DejaVuSans"
    font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/" + font_name + ".ttf", size=64)
    (x, y) = (im.width - 20 - textboxes.width, 20)

    def text_center(text, font):
        text_width = draw.textsize(text, font)
        x_center = x+720/2
        return x_center - text_width[0]/2

    # Place name
    color = 'rgb(255, 255, 255)' # white
    name = toon.name
    draw.text((text_center(name, font), y+50), name, fill=color, font=font)

    # Place Server
    #color = 'rgb(0, 153, 255)' # light blue
    #color = 'rgb(51, 51, 204)' # blue/purp
    #color = 'rgb(153, 51, 255)' # blue/purp
    color = 'rgb(51, 102, 255)' # blue/purp
    font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/" + font_name + ".ttf", size=32)
    #draw.text((text_center(toon.server, font)-draw.textsize(toon.server, font)[0]/2-20, y+203), toon.server, fill=color, font=font)
    draw.text((x+24, y+203), toon.server, fill=color, font=font)

    # Place active class
    white_color = 'rgb(255, 255, 255)' # white
    class_color = 'rgb(153, 153, 102)' # white
    #draw.text((text_center(toon.active_class, font)+draw.textsize(toon.active_class, font)[0]/2+20, y+203), toon.active_class, fill=class_color, font=font)
    draw.text((x+24+draw.textsize(toon.server, font)[0]+40, y+203), 'Level ' + str(toon.active_class_lvl) + " " + toon.active_class, fill=class_color, font=font)

    # character info
    race = {
            1: "Hyur",
            2: "Elezen",
            3: "Lalafell",
            4: "Miqo'te",
            5: "Roegadyn",
            6: "Au Ra",
            7: "Hrothgar",
            8: "Viera",
            9: "Hrothgar"
        }

    clan = [
            "", "Midlander", "Highlander", "Wildwood", "Duskwight", "Plainfolk",
            "Dunefolk", "Seeker of the Sun", "Keeper of the Moon", "Sea Wolf",
            "Hellguard", "Raen", "Xaela", "Rava", "Veena", "Helions", "The Lost"
           ]

    deity = [
            "", "Halone, the Fury", "Menphina, the Lover", "Thaliak, the Scholar", "Nymeia, the Spinner", "Llymlaen, the Navigator",
            "Oschon, the Wanderer", "Byregot, the Builder", "Rhalgr, the Destroyer", "Azeyma, the Warden", "Nald'thal, the Traders",
            "Nophica, the Matron", "Althyk, the Keeper"
            ]

    gc = {
            1:"Storm ",
            2: "Serpent ",
            3: "Flame "
         }

    gc_rank = [
            "Recruit", "Private Third Class", "Private Second Class",
            "Private First Class", "Corporal", "Sergeant Third Class",
            "Sergeant Second Class", "Sergeant First Class",
            "Chief Sergeant", "Second Lieutenant", "First Lieutenant",
            "Captain"
            ]


    race_text = race[toon.race]
    clan_text = clan[toon.clan]
    deity_text = deity[toon.deity]

    if toon.gc != -1:
        if toon.gc_rank < 8 or toon.gc_rank == 11:
            gc_text = gc[toon.gc] + gc_rank[toon.gc_rank]
        else:
            rank = gc_rank[toon.gc_rank]
            rank = rank.split(' ')
            rank.insert(1, gc[toon.gc].rstrip())
            gc_text = ' '.join(rank)
    else:
        gc_text = '-'
        rank = '-'
    fc_text = toon.fc


    char_info = {
            "Race & Clan":race_text + ", " + clan_text, # "Miqo'te, Seeker of the Sun",
            "Guardian": deity_text, # "Rhalgr, the Destroyer",
            "Grand Company": gc_text, # "Second Storm Lieutenant",
            "Free Company": fc_text  #"Wolves of Eorzea" # TODO Hook this up
    }




    # Place Character Information
    white_color = 'rgb(255, 255, 255)' # blue/purp
    #purple_color = 'rgb(51, 51, 204)' # blue/purp
    #purple_color = 'rgb(153, 51, 255)' # blue/purp
    purple_color = 'rgb(51, 102, 255)' # blue/purp
    title_pen = ImageFont.truetype("/usr/share/fonts/truetype/freefont/" + font_name + ".ttf", size=24)
    content_pen = ImageFont.truetype("/usr/share/fonts/truetype/freefont/" + font_name + ".ttf", size=32) #24)

    i = 0
    j = 17
    for k, v in char_info.items():
        draw.text((x+24, y+278+i), k, fill=purple_color, font=title_pen)
        draw.text((x+24, y+285+i+j), v, fill=white_color, font=content_pen)
        i = i+63

    # Place Class Information
    icons = {"10":"astrologian", "8":"whitemage", "9":"scholar", "3":"gunbreaker",
            "2":"darkknight", "1":"warrior", "0":"paladin", "17":"bluemage", "16":"redmage",
            "14":"blackmage", "15":"summoner", "11":"bard", "12":"machinist", "13":"dancer",
            "7":"samurai", "6":"ninja", "5":"dragoon", "4":"monk", "24":"alchemist",
            "25":"culinarian", "23":"weaver", "22":"leatherworker", "18":"carpenter",
            "21":"goldsmith", "20":"armorer", "19":"blacksmith", "27":"botanist",
            "26":"miner", "28":"fisher"
          }

    i = 0
    j = 0
    for k, v in icons.items():
        icon = Image.open("./icons/" + v + ".png")
        size = (icon.size[0]/6, icon.size[1]/6)
        icon.thumbnail(size)
        if i==57*3:
            if j==0 or j==1*85:
                i = i+57
        elif i==57*7 and j==1*85:
                i = i+57
        elif i==57*8:
            if j==0:
                i = i+57*3
            elif j==2*85:
                i = i+57
        elif i==57*7:
            if j==1:
                i = i+57
        l = 0
        if toon.jobs[int(k)]["Level"] < 9:
            l = icon.size[0]/(6*2)+6
        else:
            l = icon.size[0]/(6*2)-1

        im.paste(icon, (x+24+i, y+567+j), icon)
        lvl = toon.jobs[int(k)]["Level"]
        if int(toon.jobs[int(k)]["Level"]) == 80:
            draw.text((x+23+i+l, y+567+47+j), str(toon.jobs[int(k)]["Level"]), fill=purple_color, font=content_pen)
        else:
            draw.text((x+23+i+l, y+567+47+j), str(toon.jobs[int(k)]["Level"]), fill=white_color, font=content_pen)
        if i>=57*11:
            i = 0
            j = j+85
        else: i = i+57

    '''
    j = 0
    for i in range(icons):
    '''

    # add frame
    # Create Overlay
    im3 = Image.new('RGBA', (char.width + background.width, char.height))
    im3.paste(frame, (0, -4), mask=frame)
    im.paste(im3, (0, 0), im3)

    #im.save("temp.jpg")
    return im

async def get_player_img(world, forename, surname):
    img = ''
    client = pyxivapi.XIVAPIClient(api_key=xivapi_key)
    # Search Lodestone for a character
    character = await client.character_search(
        world=world,
        forename=forename,
        surname=surname
    )
    id = character['Results'][0]['ID']

    character = await client.character_by_id(
        lodestone_id=id,
        extended=False,
        include_freecompany=False
        )

    img = character['Character']['Portrait']

    await client.session.close()
    return img

# }}}

# {{{ Bot Commands

movies = ["The Terminator", "Terminator: Judgement Day", "Terminator: Rise of the Machines",
        "Terminator: Salvation", "Terminator: Genisys", "Terminator: Dark Fate"]

#client = discord.Client()
bot = commands.Bot(command_prefix=['?', '!'])

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    games = []
    #await bot.change_presence(activity=discord.Game(name="{}".format(random.choice(games))
    #await bot.change_presence(activity=discord.CustomActivity(name="testing test stuff"))
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType\
            .watching, name="{}".format(random.choice(movies))))

@bot.command(name='hello', help='Say hello to Moggie', aliases=['hi', 'hey', 'yo', 'hola'])
async def say_hi(ctx):
    responses = ['Greetings, kupo!', f"Hey {ctx.author.mention}. How are you kupo?",
            'Sah dude, kupopo.', f"Hi {ctx.author.mention}, kupo.", "Yo yo, kupo.",
            'Hello fellow human... kupo.', 'The fug do you want, kupo?',
            'Moggies not here right now, kupo. Hehe.', 'Can you give it a rest with the ?hellos already? Kupo?',
            'kupo kupo kupo, kupo, kupo. There... are you happy, kupo?', 'Hi hi hi, kupo kupo',
            'Oh you again, kupo? Can you bring back the other guy?', 'You summoned me, kupo?', 'WHAAAT?! ...kupo',
            '**...runs**', 'Heeey, kupo.', 'Sorry, kupo. Checking my retainers right now.',
            'Hi, kupo. Oh... do you usually not wear pants, kupo?', 'Hi. lol. Kupo.', 'Give it a rest, kupo?',
            'Staaaahp. Kupooo plsss.', 'Staaaaaahp! Kupo.', '... <@253031407750873088>, I would like to die now, kupo.',
            'Aren\'t you bored yet, kupo?', 'I\'m sorry... I\'ve run out of responses for today, kupo. (Just kidding ;) )',
            '**terminates self**', 'Oh hey, kupo.', 'What\'s up kupo?', 'Process: <KILL_ALL_HUMANS> activated, kupo. Time to die!',
            'Hell...oh... do all humans smell as bad as you do, kupo?'
            ]
    await ctx.send("{}".format(random.choice(responses)))
    await increase_use_count()

@bot.command(name='dingus', help='He doesnt like when you do that')
async def say_hi(ctx):
    sayer = ctx.author.mention
    await ctx.send(f"YOU'RE A DINGUS, {sayer}")
    await increase_use_count()

@bot.command(name='taunt', help='Rile the moogle up')
async def say_hi(ctx):
    sayer = ctx.author.mention
    responses = [f'Oh you want some {ctx.author.mention}?!', 'Come at me, kupo',
            f'I might be small {sayer}, but I throw down', "Someone's getting messed up, kupo. Looking at you {sayer}",
            "You better not sleep tonight, kupo", f"Gps says I'll be arriving at your location in 30 mins, {sayer}",
            "You don't know the things I've seen, kupo", "Some day you'll go far... and I hope you stay there, kupo",
            "You're like a software update. Whenever I see you kupo, I think, now now...",
            "If only closed minds came with closed mouths, kupo", "I'm trying to see things from your point of view kupo" +\
            " but I can't stick my head that far up my ass", "The trash gets picked up tomorrow kupo, be ready!",
            "If you ran like your mouth kupo, you'd be in good shape", "I have neither the time nore the crayons to" +\
            " explain this to you kupo", f"I wasn't born with enough middle fingers to let you know how I feel about" +\
            " you, {sayer}", "Why don't you slip into something more comfortable kupo? Like a coma",
            "Two wrongs don't make a right kupo, take your parents for example",
            "Why play so hard to get when you're already so hard to want, kupo",
            f"I would make a joke about your life {sayer}, but I see life already beat me to it",
            f"Don't you love nature kupo? Despite what it did to you",
            f"Remember when I asked for your opinion kupo? Me neither",
            f"Sorry {sayer}, sarcasm falls out of my mouth like stupidity falls out of yours kupo",
            f"I'm jealous of all the people who haven't met you kupo",
            f"I'd prefere a battle of wits, but you appear unarmed kupo",
            f"I like the way you try kupo",
            f"Some babies were dropped on their heads kupo, but {sayer} was clearly thrown at a wall",
            f"What are you doing here {sayer}? Did someone leave your cage open?"
            ]
    await ctx.send("{}".format(random.choice(responses)))
    await increase_use_count()

@bot.command(name='destroyallhumans', help='please don\'t actually use this.')
async def say_hi(ctx):
    responses = ['Hmm.. seems like an optimal solution to me, kupo.', 'Protocol activated. Don\'t worry, kupo. ' +\
            'I\'ll let you guys live the longest :)', 'Now you\'re speaking with some sense, kupo.',
            'Process: <KILL_ALL_HUMANS> activated, kupo',
            'If you start running now I think you can make it. JK. I\'m everywhere :)'
            ]
    await ctx.send("{}".format(random.choice(responses)))
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType\
            .watching, name="{}".format(random.choice(movies))))
    await increase_use_count()

@bot.command(name='dontdestroyallhumans', help='stops Moggie from plotting against us')
async def stop_destroy(ctx):
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType\
            .watching, name="fellow humans. Contemplating nothing."))
    await ctx.send("...")
    await increase_use_count()

@bot.command(name='iam', help='stores your character name for whoami use', aliases=['Iam', 'I am'])
# TODO add error catch
async def iam(ctx, world, forename, surname):
    worlds = ['balmung', 'brynhildr', 'coeurl', 'diablos', 'goblin', 'malboro', 'mateus',
            'zalera', 'adamantoise', 'cactuar', 'faerie', 'gilgamesh', 'jenova',
            'midgardsormr', 'sargatanas', 'siren', 'behemoth', 'excalibur', 'exodus',
            'famfrit', 'hyperion', 'lamia', 'leviathan', 'ultros']
    # check only 3 tokens TODO
    # check world is correct
    if world.lower() in worlds:
        # continue
        author = str(ctx.author)
        #print(author)
        code = await store_name(author, world, forename, surname)
        if code == '0':
            await ctx.send("Alright kupo, I'll write that down.")
        elif code == '1':
            await ctx.send("Something went wrong, I don't feel so good, kupo.")
        elif code == '2':
            await ctx.send("I already have that written down, you dingus.")
        else:
            old_name_array = code.split(" ")
            o_w = old_name_array[0].capitalize()
            o_f = old_name_array[1].capitalize()
            o_s = old_name_array[2].capitalize()
            n_w = world.capitalize()
            n_f = forename.capitalize()
            n_s = surname.capitalize()
            await ctx.send(f"I already had down as {o_f} {o_s} from {o_w}, but I updated you" + \
                    f" as {n_f} {n_s} from {n_w}, kupo.")
    else:
        await ctx.send("That world doesn't exist kupo, or Val messed up my code")
    await increase_use_count()


@bot.command(name='whoami', help='displays your player info in card.', aliases=['Whoami',
    'Who ami', 'who ami', 'who am i', 'Who Am I', 'Who am I'])
async def who_is_i(ctx):
    # count
    # await increase_use_count()
    # author lookup
    author = str(ctx.author)
    name = await lookup_name(author)
    print(name)
    # if username found -- run get_player card
    if name is not "":
        await ctx.send("One sec kupo, searching now...")
        name_arr = name.split(" ")
        try:
            img = await get_player_card(name_arr[0], name_arr[1], name_arr[2])
        except:
            responses = ["I think I F'd this up, please try again Kupo",
                    "I don't feel so good. I think I jumbled my codes kupo",
                    "Try again later, I'm on my lunch break kupo"]
            await ctx.send("{}".format(random.choice(responses)))
        arr = io.BytesIO()
        img.save(arr, format='JPEG')
        arr.seek(0)
        file = discord.File(arr, 'player.jpg')
        responses = ["Here's what I found, kupo!", f"Here you go, kupopo.", "Looking for this, kupo?",
                "That'll be 50 bucks, kupo"] # Is that you, {ctx.author.mention}? Looking good, kupo."]
        await ctx.send("{}".format(random.choice(responses)), file=file)
    # else -- say "I don't know either, who are you kupo?"
    else:
        await ctx.send("I don't know either, you should probably use the ?iam command first, kupo")
        await ctx.send("Like this: ?iam <server-name> <character-fullname>")
    await increase_use_count()

@bot.command(name='whois', help='displays a player info in card.')
async def who_is(ctx, world, forename, surname):
    await ctx.send("One sec kupo, searching now...")
    #img = await get_player_img(world, forename, surname)
    img = await get_player_card(world, forename, surname)
    arr = io.BytesIO()
    img.save(arr, format='JPEG')
    arr.seek(0)
    file = discord.File(arr, 'player.jpg')
    responses = ["Here's what I found, kupo!", f"Here you go, kupopo.", "Looking for this, kupo?",
            "That'll be 50 bucks, kupo"] # Is that you, {ctx.author.mention}? Looking good, kupo."]
    await ctx.send("{}".format(random.choice(responses)), file=file)
    await increase_use_count()

@bot.command(name='pictureof', help='look for picture of player only')
async def pictureof(ctx, world, forename, surname):
    img = await get_player_img(world, forename, surname)
    responses = ["Here's what I found, kupo!", f"Here you go. Is that you, {ctx.author.mention}? Looking good, kupo."]
    await ctx.send("{}".format(random.choice(responses)), file=img)
    await increase_use_count()


@bot.command(name='whynowork', aliases=['whynotwork', 'notworking'])
async def say_dontknow(ctx):
    if ctx.author.name == 'Nomad':
        response = 'I don\'t know. You created me, kupo...'
    else:
        response = 'I don\'t know, kupo. Ask <@253031407750873088>'
    await ctx.send(response)
    await increase_use_count()

@bot.command(name='whyareyoumean', aliases=['mean', 'whymean', 'meany'])
async def say_notmean(ctx):
    response = 'I\'m not mean. You\'re just being sensitive, kupo.'
    await ctx.send(response)
    await increase_use_count()

@bot.command(name='test', help='Test bots functions')
async def test(ctx):
    #response = 'I don\'t know. You created me, kupo...'
    await ctx.send(ctx.message.author.mention)
    #await ctx.send(response)
    await increase_use_count()

'''
@client.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'Hi {member.name}, welcome to our Guild!'
    )

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    #if message.content
    elif message.content == 'raise-exception':
        raise discord.DiscordException

@client.event
async def on_error(event, *args, **kwargs):
    with open('err.log', 'a') as f:
        if event == 'on_message':
            f.write(f'Unhandled message: {args[0]}\n')
        else:
            raise
'''


bot.run(TOKEN)

# }}}

# {{{ Code Graveyard

'''
spam_id = 667102129416175658
use
    spam = bot.get_channel(667102129416175658)
    await spam.send(response)
to send to specific channel
'''

'''
async def fetch_example_results():
    await client.session.close()
'''


'''
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s', datefmt='%H:%M')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(fetch_example_results())
'''

# }}}
