import discord
from discord import app_commands

import json

from pull_player_data_from_gsheet import get_objs, sync, get_discord_id_to_ign_map
from matchmaking import matchmake, match_quality

AUTH_TOKEN_PATH = "../gspread_auth_token.json"
BOT_TEST_GUILD_ID = 743294122567401503
BOT_TEST_GUILD = discord.Object(id=BOT_TEST_GUILD_ID)
AMA_PRES_GUILD_ID = 1034511626222706779
AMA_PRES_GUILD = discord.Object(id=AMA_PRES_GUILD_ID)


class SlashCommandClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.get_players_response = None
        self.discord_id_to_ign = None

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=BOT_TEST_GUILD)
        self.tree.copy_global_to(guild=AMA_PRES_GUILD)
        await self.tree.sync(guild=BOT_TEST_GUILD)
        await self.tree.sync(guild=AMA_PRES_GUILD)


if __name__ == "__main__":
    with open("../amas_presence_bot_token.txt", "r") as f:
        token = f.read()
    intents = discord.Intents.default()
    intents.members = True
    client = SlashCommandClient(intents=intents)

    @client.tree.command(
        name="syncids",
        description="dump all member objs as json",
        guilds=[AMA_PRES_GUILD],
    )
    @app_commands.describe(
        role="if not empty, only get members with the role of this name"
    )
    async def getdiscordids(interaction, role: str = ""):
        await interaction.response.defer(thinking=True)
        g = await client.fetch_guild(AMA_PRES_GUILD_ID)
        id_data = [
            {"name": x.name, "id": x.id, "nickname": x.display_name}
            async for x in g.fetch_members()
            if role == "" or role in [y.name for y in x.roles]
        ]
        with open("member_dump.json", "w+") as f:
            json.dump(
                id_data,
                f,
            )
        client.discord_id_to_ign, unfound_members = get_discord_id_to_ign_map(
            AUTH_TOKEN_PATH, id_data
        )
        await interaction.edit_original_response(
            content=f"Could not find the following names in the Season 1 Form Sheet\n```{json.dumps(unfound_members, indent=2)}```"
        )

    @client.tree.command(
        name="getplayers",
        description="post a message, then pull a list of reactors",
        guilds=[BOT_TEST_GUILD, AMA_PRES_GUILD],
    )
    async def getplayers(interaction):
        if client.get_players_response:
            client.get_players_response = await client.get_players_response.fetch()
            reactors = [
                client.discord_id_to_ign[x.id]
                for y in client.get_players_response.reactions
                async for x in y.users()
                if x.id in client.discord_id_to_ign
            ]
            await interaction.response.send_message(
                f"Use the following as the argument for `/matchmake`\n```{','.join(reactors)}```"
            )
            client.get_players_response = None
        else:
            await interaction.response.send_message(
                "Respond to this message to register for matchmaking"
            )
            client.get_players_response = await interaction.original_response()

    @client.tree.command(
        name="sync",
        description="pull data from the google sheet and discord",
        guilds=[BOT_TEST_GUILD, AMA_PRES_GUILD],
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
        guilds=[BOT_TEST_GUILD, AMA_PRES_GUILD],
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

    client.run(token)
