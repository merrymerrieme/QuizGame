class Lobby :
    def __init__(self):
        self.player_list = []
        self.scoreboard = []

    def addPlayer(self, Player):
        self.player_list.append(Player)

    def createScoreboard(self):
        for player in self.player_list:
            self.scoreboard.append([player.name, player.score])

    def getScoreboard(self):
        return self.scoreboard


class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0

    def __name__(self):
        return self.name
    


