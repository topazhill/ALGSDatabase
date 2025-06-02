import requests
import json
import sqlite3
import time
# This script fetches data from the Apex Legends tournament API, processes player and team statistics, 
scrim_ids = [8413, 8414, 8423, 8424, 8433, 8434, 8351, 8352, 8357, 8358, 8364, 8365, 8371, 8372, 8377, 8378, 8389, 8390, 8394, 8395, 8400, 8401, 8406, 8407]

def get_info(id):
    url = f'https://apexlegendsstatus.com/tournament/ingram/?qt=getScores&tournamentId={id}'
    url2 = 'https://apexlegendsstatus.com/tournament/ingram/?qt=getTournaments&allGames=1'
    headers = {"Content-Type": "application/json; charset=utf-8", "Authorization": 'b3fd68938c43d39e77bf47a77a7b752569ed5313f07ac481ad5169e6bc64699f'}

    try:

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            posts = response.json()
            return posts
        else:
            print('Error:', response.status_code)
            return None

    except requests.exceptions.RequestException as e:
        print("Error: ", e)
        return None

class Player():
    def __init__(self, name, id, kills, damageDealt, damageTaken, ringDamage, assists, revivesGiven, gamesPlayed):
        self.__name = name
        self.__id = id
        self.__kills = kills
        self.__damageDealt = damageDealt
        self.__damageTaken = damageTaken
        self.__ringDamage = ringDamage
        self.__assists = assists
        self.__revivesGiven = revivesGiven
        self.__gamesPlayed = gamesPlayed
    

        self.__points = 0
        self.CalculatePoints()
    
    def CalculatePoints(self):
        self.__points += round((self.__kills * 3) + (self.__damageDealt * 0.001) + (self.__assists * 1) + (self.__revivesGiven * 0.5))

    def GetPoints(self):
        return self.__points, self.__name, self.__id

    def GetInfo(self):
        return {
            'name': self.__name,
            'id': self.__id,
            'points': self.__points,
            'kills': self.__kills,
            'damageDealt': self.__damageDealt,
            'damageTaken': self.__damageTaken,
            'ringDamage': self.__ringDamage,
            'assists': self.__assists,
            'revivesGiven': self.__revivesGiven,
            'gamesPlayed': self.__gamesPlayed
        }
    def __repr__(self):
        return f"Player Name: {self.__name}, Points: {self.__points}, id: {self.__id}, Kills: {self.__kills}, Damage Dealt: {self.__damageDealt}"

class Coach():
    def __init__(self, teamName, points, wins):
        self.__teamName = teamName
        self.__teamPoints = points
        self.__points = 0
        self.__wins = wins
        self.CalculatePoints()

    def GetPoints(self):
        return self.__points, self.__teamName
    def CalculatePoints(self):
        self.__points += round(self.__teamPoints + self.__wins * 10)

    def GetInfo(self):
        return {
            'teamName': self.__teamName,
            'points': self.__points,
            'wins': self.__wins
        }

    def __repr__(self):
        return f"Coach Team: {self.__teamName}, Points: {self.__points}"

def add_tournament(id):
    data = get_info(id)

    print(data)

    teamdata = data['teamData']
    teams = {}
    players = []

    coaches = []
    playerobjects = []

    for team in teamdata:
        teamname = team['teamName'].split("@")[0]
        wins = 0
        for score in team['ranking']:
            if score == 1:
                wins += 1
        if teamname not in teams:
            teams[teamname] = [teamname, team['points'], wins]
        else:
            teams[teamname][1] += team['points']
            teams[teamname][2] += wins
        
        playerdata = team['playersData']
        for p in playerdata:
            players.append(p['playerName'])
            playerobjects.append(Player(p['playerName'], p['playerId'], p['kills'], p['damageDealt'], p['damageTaken'], p['ringDamage'], p['assists'], p['revivesGiven'], p['gamesPlayed']))

    for teaminfo in teams.items():
        coaches.append(Coach(teaminfo[0], teaminfo[1][1], teaminfo[1][2]))

    print(teams)
    print(players)

    playerobjects.sort(key=lambda x: x.GetPoints()[0], reverse=True)
    for player in playerobjects:
        print(repr(player))
    coaches.sort(key=lambda x: x.GetPoints()[0], reverse=True)
    for coach in coaches:
        print(repr(coach))

    conn = sqlite3.connect('ALGSScrimData.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS players (
        id TEXT PRIMARY KEY,
        name TEXT,
        points INTEGER,
        tournamentsPlayed INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS coaches (
        teamName TEXT PRIMARY KEY,
        points INTEGER,
        tournamentsPlayed INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS Tournament (
        tournamentId INTEGER PRIMARY KEY,
        tournamentName TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS TournamentPlayers (
        tournamentId INTEGER,
        playerId TEXT,
        playerName TEXT,
        points INTEGER,
        kills INTEGER,
        damageDealt INTEGER,
        damageTaken INTEGER,
        ringDamage INTEGER,
        assists INTEGER,
        revivesGiven INTEGER,
        gamesPlayed INTEGER,
        FOREIGN KEY (tournamentId) REFERENCES Tournament(tournamentId),
        FOREIGN KEY (playerId) REFERENCES players(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS TournamentCoaches (
        tournamentId INTEGER,
        teamName TEXT,
        points INTEGER,
        wins INTEGER,
        FOREIGN KEY (tournamentId) REFERENCES Tournament(tournamentId),
        FOREIGN KEY (teamName) REFERENCES coaches(teamName)
    )''')

    # Insert tournament data
    tournament_id = data['ALSData']['tournamentId']
    tournament_name = data['ALSData']['name']
    timestamp = data['gamesPlayed'][0].split(":")[-1]
    c.execute('''INSERT OR REPLACE INTO Tournament (tournamentId, tournamentName, timestamp) 
                VALUES (?, ?, ?)''', 
                    (tournament_id, tournament_name, timestamp))

    for player in playerobjects:
        info = player.GetInfo()
        c.execute('''SELECT id FROM players WHERE id = ?''', (info['id'],))
        if c.fetchone() is None:
            c.execute('''INSERT INTO players (id, name, points, tournamentsPlayed) 
                        VALUES (?, ?, ?, 1)''', 
                            (info['id'], info['name'], info['points']))
        else:
            c.execute('''UPDATE players SET tournamentsPlayed = tournamentsPlayed + 1 WHERE id = ?''', (info['id'],))
            c.execute('''UPDATE players SET points = points + ? WHERE id = ?''', (info['points'], info['id']))

        # Insert player data into TournamentPlayers
        c.execute('''INSERT INTO TournamentPlayers (tournamentId, playerId, playerName, points, kills, damageDealt, damageTaken, ringDamage, assists, revivesGiven, gamesPlayed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                        (tournament_id, info['id'], info['name'], info['points'], info['kills'], info['damageDealt'], info['damageTaken'], info['ringDamage'], info['assists'], info['revivesGiven'], info['gamesPlayed']))

    for coach in coaches:
        info = coach.GetInfo()
        c.execute('''SELECT teamName FROM coaches WHERE teamName = ?''', (info['teamName'],))
        if c.fetchone() is None:
            c.execute('''INSERT INTO coaches (teamName, points, tournamentsPlayed) 
                        VALUES (?, ?, ?)''', 
                            (info['teamName'], info['points'], 1))
        else:
            c.execute('''UPDATE coaches SET points = points + ? WHERE teamName = ?''', (info['points'], info['teamName']))
            c.execute('''UPDATE coaches SET tournamentsPlayed = tournamentsPlayed + 1 WHERE teamName = ?''', (info['teamName'],))
        # Insert coach data into TournamentCoaches
        c.execute('''INSERT INTO TournamentCoaches (tournamentId, teamName, points, wins)
                    VALUES (?, ?, ?, ?)''', 
                        (tournament_id, info['teamName'], info['points'], info['wins']))

    conn.commit()

    c.execute('''SELECT * FROM UserPlayers''')
    user_players = c.fetchall()
    for user_player in user_players:
        player_id = user_player[1]
        user_id = user_player[0]

        c.execute('''SELECT points FROM TournamentPlayers WHERE (playerId = ? AND tournamentId = ?)''', (player_id, tournament_id))
        player_data = c.fetchone()
        if player_data:
            points = player_data[0]
            c.execute('''UPDATE Users SET totalPoints = totalPoints + ? WHERE username = ?''', (points, user_id))
        else:
            print(f"Player {player_id} not found in tournament {tournament_id}")

    conn.commit()
    conn.close()
    time.sleep(1)  # To avoid hitting the API too fast

id = int(input("Enter tournament ID: "))
add_tournament(id)
print("Tournament data added successfully.")