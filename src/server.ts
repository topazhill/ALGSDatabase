import * as express from 'express';
import * as cors from 'cors';
import * as sqlite3 from 'sqlite3';
import { open } from 'sqlite';

const clients: { [id:string]: any } = {};

const port: number = 8000;

const app = express();
app.use(cors());
app.use(express.json());

interface Player {
    id: string;
    name: string;
    points: number;
    tournamentsPlayed: number;
    cost: number;
}

interface TournamentPlayer {
    tournamentId: string;
    playerId: string;
    playerName: string;
    points: number;
    kills: number;
    damageDealt: number;
    damageTaken: number;
    ringDamage: number;
    assists: number;
    revivesGiven: number;
    gamesPlayed: number;
}

interface TournamentPerformance {
    tournamentId: string;
    playerId: string;
    playerName: string;
    points: number;
    kills: number;
    damageDealt: number;
    damageTaken: number;
    ringDamage: number;
    assists: number;
    revivesGiven: number;
    gamesPlayed: number;
    tournamentName: string;
    tournamentTimestamp: string;
}

interface Tournament {
    id: string;
    name: string;
    timestamp: string;
}

interface User {
    name: string;
    points: number;
    money: number;
}

let db = null;
(async () => {
    db = await open({
        filename: 'ALGSScrimData.db',
        driver: sqlite3.cached.Database
    })
})()

app.get('/players/:id', (req, res) => {
    const playerId = req.params.id;
    db.get('SELECT * FROM players WHERE id = ?', [playerId])
        .then((player: Player) => {
            if (player) {
                res.json(player);
            } else {
                res.status(404).json({ error: 'Player not found' });
            }
        })
        .catch((error) => {
            console.error('Error fetching player:', error);
            res.status(500).json({ error: 'Internal server error' });
        });
})

app.get('/players', (req, res) => {
    db.all('SELECT * FROM players')
        .then((players: Player[]) => {
            res.json(players);
        })
        .catch((error) => {
            console.error('Error fetching players:', error);
            res.status(500).json({ error: 'Internal server error' });
        });
})

app.get('/tournamentplayer/:id', (req, res) => {
    const playerId = req.params.id;
    db.all('SELECT * from (TournamentPlayers INNER JOIN Tournament ON TournamentPlayers.tournamentId == Tournament.tournamentId) WHERE playerId = ? ORDER BY Tournament.timestamp DESC', [playerId]).then((player: TournamentPerformance[]) => {
        if (player) {
            res.json(player);
        } else {
            res.status(404).json({ error: 'Player not found' });
        }
    })
        .catch((error) => {
            console.error('Error fetching player:', error);
            res.status(500).json({ error: 'Internal server error' });
        });
})

app.get('/tournament/:id/players', (req, res) => {
    const tournamentId = req.params.id;
    db.all('SELECT * FROM TournamentPlayers WHERE tournamentId = ?', [tournamentId])
        .then((players: TournamentPlayer[]) => {
            if (players.length === 0) {
                return res.status(404).json({ error: 'No players found for this tournament' });
            }
            res.json(players);
        })
        .catch((error) => {
            console.error('Error fetching tournament players:', error);
            res.status(500).json({ error: 'Internal server error' });
        });
})

app.post('/newuser', (req, res) => {
    const name = req.body.name;
    const points = req.body.points || 0; // Default points to 0 if not provided
    console.log(name, points);
    if (name === undefined || name === '' || points === undefined) {
        res.status(400).json({ error: 'Missing user data' });
    }
    else {
        db.run('INSERT INTO users (username, totalPoints) VALUES (?, ?)', [name, points])
            .then(() => {
                res.status(201).json({ message: 'New user created successfully', name, points });
            })
            .catch((error) => {
                console.error('Error creating new user:', error);
                res.status(500).json({ error: 'Internal server error' });
            });
    }
});

app.post('/changemoney', (req, res) => {
    const money = req.body.amount;
    const username = req.body.username;
    if (username === undefined || username === '' || money === undefined) {
        res.status(400).json({ error: 'Username and money are required' });
    }
    else {
        db.run('UPDATE users SET money = money + ? WHERE username = ?', [money, username])
            .then(() => {
                res.status(200).json({ message: 'Money updated successfully' });
            })
            .catch((error) => {
                console.error('Error updating user money:', error);
                res.status(500).json({ error: 'Internal server error' });
            });
    }
})

app.get('/money/:username', (req, res) => {
    const username = req.params.username;
    if (username === undefined || username === '') {
        res.status(400).json({ error: 'Username is required' });
    }
    else {
        db.get('SELECT money FROM users WHERE username = ?', [username])
            .then((user: { money: number }) => {
                if (user) {
                    res.json({ money: user.money });
                } else {
                    res.status(404).json({ error: 'User not found' });
                }
            })
            .catch((error) => {
                console.error('Error fetching user money:', error);
                res.status(500).json({ error: 'Internal server error' });
            });
    }
})

app.get('/users/:name', (req, res) => {
    const name = req.params.name;
    db.get('SELECT * FROM users WHERE username = ?', [name])
        .then((user: User) => {
            if (user) {
                res.json(user);
            } else {
                res.status(404).json({ error: 'User not found' });
            }
        })
        .catch((error) => {
            console.error('Error fetching user:', error);
            res.status(500).json({ error: 'Internal server error' });
        });
});

app.post('/addplayer', (req, res) => {
    const { username, playerID } = req.body;
    if (username === undefined || username === '' || playerID === undefined || playerID === '') {
        res.status(400).json({ error: 'Username and playerID are required' });
    }
    else {
        db.run('INSERT INTO UserPlayers (username, playerID) VALUES (?, ?)', [username, playerID])
            .then(() => {
                res.status(201).json({ message: 'Player added successfully' });
            })
            .catch((error) => {
                console.error('Error adding player to user:', error);
                res.status(500).json({ error: 'Internal server error' });
            });
    }
})

app.post('/removeplayer', (req, res) => {
    const { username, playerID } = req.body;
    if (username === undefined || username === '' || playerID === undefined || playerID === '') {
        res.status(400).json({ error: 'Username and playerID are required' });
    }
    else {
        db.run('DELETE FROM UserPlayers WHERE username = ? AND playerID = ?', [username, playerID])
            .then(() => {
                res.status(200).json({ message: 'Player removed successfully' });
            })
            .catch((error) => {
                console.error('Error removing player from user:', error);
                res.status(500).json({ error: 'Internal server error' });
            });
    }
})

app.get('/userplayers/:username', (req, res) => {
    const username = req.params.username;
    if (username === undefined || username === '') {
        res.status(400).json({ error: 'Username is required' });
    }
    else {
        db.all('SELECT players.* FROM (UserPlayers INNER JOIN players ON UserPlayers.PlayerID == players.id) WHERE UserPlayers.username = ?', [username])
            .then((players: { playerID: string }[]) => {
                if (players.length === 0) {
                    return res.status(404).json({ error: 'No players found for this user' });
                }
                res.json(players);
            })
            .catch((error) => {
                console.error('Error fetching user players:', error);
                res.status(500).json({ error: 'Internal server error' });
            });
    }
})

app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
})