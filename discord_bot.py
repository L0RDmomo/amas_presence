import discord
from discord import app_commands

from pull_player_data_from_gsheet import get_objs, sync
from matchmaking import matchmake, match_quality

AUTH_TOKEN_PATH = "../gspread_auth_token.json"
BOT_TEST_GUILD = discord.Object(id=743294122567401503)
AMA_PRES_GUILD = discord.Object(id=1034511626222706779)


class SlashCommandClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=BOT_TEST_GUILD)
        # self.tree.copy_global_to(guild=AMA_PRES_GUILD)
        await self.tree.sync(guild=BOT_TEST_GUILD)
        # await self.tree.sync(guild=AMA_PRES_GUILD)


if __name__ == "__main__":
    intents = discord.Intents.default()
    client = SlashCommandClient(intents=intents)

    @client.tree.command(
        name="sync",
        description="pull data from the google sheet",
        guilds=[
            BOT_TEST_GUILD,
            # AMA_PRES_GUILD
        ],
    )
    async def syncdata(interaction):
        await interaction.response.defer(thinking=True)
        errs = sync(AUTH_TOKEN_PATH)

        response = "Sync Complete"
        if errs:
            response += "\n```" + "\n".join(errs) + "```"

        await interaction.edit_original_response(content=response)

    @client.tree.command(
        name="matchmake",
        description="generate optimal matches for a given list of player names",
        guilds=[
            BOT_TEST_GUILD,
            # AMA_PRES_GUILD
        ],
    )
    @app_commands.describe(igns="a csv list of igns to include in matchmaking")
    async def getmatches(interaction, igns: str):
        await interaction.response.defer(thinking=True)
        response = ""
        igns = [x.lower() for x in igns.split(",")]
        data = get_objs(AUTH_TOKEN_PATH)

        players = [x for x in data if x.player_id in igns]

        matches = matchmake(players)
        i = 0
        for match in matches:
            i += 1
            team_num = 0
            response += f"```Match {i}:\tMatch Score: {match_quality(match)}\n"
            response += f"\tTeam {team_num+1}:\n"
            response += f"\t\tSolo:     {[x.player_id for x in match[team_num] if x.role == 'solo'][0]}\n"
            response += f"\t\tJg:       {[x.player_id for x in match[team_num] if x.role == 'jg'][0]}\n"
            response += f"\t\tMid:      {[x.player_id for x in match[team_num] if x.role == 'mid'][0]}\n"
            response += f"\t\tSupport:  {[x.player_id for x in match[team_num] if x.role == 'support'][0]}\n"
            response += f"\t\tCarry:    {[x.player_id for x in match[team_num] if x.role == 'carry'][0]}\n"
            team_num = 1
            response += f"\tTeam {team_num+1}:\n"
            response += f"\t\tSolo:     {[x.player_id for x in match[team_num] if x.role == 'solo'][0]}\n"
            response += f"\t\tJg:       {[x.player_id for x in match[team_num] if x.role == 'jg'][0]}\n"
            response += f"\t\tMid:      {[x.player_id for x in match[team_num] if x.role == 'mid'][0]}\n"
            response += f"\t\tSupport:  {[x.player_id for x in match[team_num] if x.role == 'support'][0]}\n"
            response += f"\t\tCarry:    {[x.player_id for x in match[team_num] if x.role == 'carry'][0]}```"

        if not matches:
            response = "No matches found"

        await interaction.edit_original_response(content=response)

    client.run(
        "MTE1NzQxMDg4Mjk5Nzk4MTI3NQ.GLsrK1.Qytsd8zogQKwMO3yIJuYca-Fojmgi5bnSkmkrA"
    )
