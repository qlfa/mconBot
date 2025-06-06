# Original work Copyright (c) 2022 Ray Nieport

import discord
from rcon import rcon
from os import getenv
from dotenv import load_dotenv
from json import load

instance = discord.Intents.default()
instance.guilds = True
instance.members = True
instance.message_content = True


# Override default Client class to allow messages from other bots
class UnfilteredClient(discord.Client):
    def __init__(self, **options):
        super().__init__(**options)


client = UnfilteredClient(intents=instance)
Help = None


async def send_rcon(cmd, args, message):
    try:
        with rcon(IP, PASS, PORT) as mcr:
            if args:
                resp = mcr.command(cmd + ' ' + args)
            else:
                resp = mcr.command(cmd)
    except Exception as e:
        print(f"RCON Error: {e}")
        resp = 'Connection from the bot to the server failed.'
    print(f'[{message.author}]: {cmd} {args}')
    if resp:
        await message.channel.send(resp)
        print(f'{resp}')


@client.event
async def on_message(message):
    if not message.content.startswith('/') or message.author == client.user:
        return
    try:
        cmd, args = message.content[+1:].split(None, 1)
    except ValueError:
        cmd = message.content[+1:]
        args = ''
    authLevel = 0
    if message.author.bot:
        authLevel = BOT_LEVEL
    else:
        if isinstance(message.author, discord.Member):
            for role in message.author.roles:
                if role.name == USER_ROLE:
                    authLevel += 1
                elif role.name == MOD_ROLE:
                    authLevel += 2
                elif role.name == ADMIN_ROLE:
                    authLevel += 4

    if cmd == 'help':
        if Help:
            await message.channel.send(embed=Help)
            print(f'Helped out {message.author}.')
        else:
            await message.channel.send('Help message is not available at the moment.')
    elif cmd == 'hi':
        await message.channel.send('Hello! I\'m the Minecraft RCON bot!')
        print(f'Said hi to {message.author}.')
    elif cmd == 'admin':
        if authLevel >= 4:
            # 'admin' コマンドの場合、argsが実際のコマンドになる
            actual_cmd = args
            actual_args = ''  # adminコマンドの引数は通常ここで分離しない
            # RCONに渡すコマンドと引数の形式を再考する必要があるかもしれません。
            # ここでは元のロジックに従い、args全体をコマンドとして扱います。
            await send_rcon(actual_cmd, actual_args, message)
        else:
            await message.channel.send('Sorry, you need the ' + (ADMIN_ROLE or "Admin") + ' role to use that command.')
    elif cmd in cmds['user_commands']:
        if authLevel >= 1:
            await send_rcon(cmd, args, message)
        else:
            await message.channel.send('Sorry, you need the ' + (USER_ROLE or "User") + ' role to use that command.')
    elif cmd in cmds['mod_commands']:
        if authLevel >= 2:
            await send_rcon(cmd, args, message)
        else:
            await message.channel.send('Sorry, you need the ' + (MOD_ROLE or "Mod") + ' role to use that command.')
    elif cmd in cmds['admin_commands']:
        if authLevel >= 4:
            await send_rcon(cmd, args, message)
        else:
            await message.channel.send('Sorry, you need the ' + (ADMIN_ROLE or "Admin") + ' role to use that command.')
    else:
        await message.channel.send('Invalid command.')


if __name__ == "__main__":
    # Get environment variables
    load_dotenv()
    TOKEN = getenv('DISCORD_TOKEN')
    USER_ROLE = getenv('DISCORD_USER_ROLE')
    MOD_ROLE = getenv('DISCORD_MOD_ROLE')
    ADMIN_ROLE = getenv('DISCORD_ADMIN_ROLE')
    IP = getenv('MINECRAFT_IP')
    PASS = getenv('MINECRAFT_PASS')
    PORT_STR = getenv('RCON_PORT')
    BOT_LEVEL_STR = getenv('BOT_LEVEL')

    if PORT_STR is None:
        PORT = 25575
    else:
        PORT = int(PORT_STR)

    if BOT_LEVEL_STR is None:
        BOT_LEVEL = 1
    else:
        BOT_LEVEL = int(BOT_LEVEL_STR)

    # Get dictionary of commands
    with open('commands.json') as cmd_file:
        cmds = load(cmd_file)

    Help = discord.Embed(title="mconBot Help",
                         description="A bot to interact with your Minecraft server - from Discord!")
    # User Commands
    user_cmds_text = ""
    for com, desc in cmds['user_commands'].items():
        user_cmds_text += f"**{com}**: {desc}\n"
    if user_cmds_text:  # コマンドが一つでもあればフィールドを追加
        Help.add_field(name='-------------------------' + (USER_ROLE or "User") + ' Commands-------------------------',
                       value=user_cmds_text.strip(), inline=False)

    # Mod Commands
    mod_cmds_text = ""
    for com, desc in cmds['mod_commands'].items():
        mod_cmds_text += f"**{com}**: {desc}\n"
    if mod_cmds_text:
        Help.add_field(
            name='-------------------------' + (MOD_ROLE or "Moderator") + ' Commands-------------------------',
            value=mod_cmds_text.strip(), inline=False)

    # Admin Commands
    admin_cmds_text = ""
    for com, desc in cmds['admin_commands'].items():
        admin_cmds_text += f"**{com}**: {desc}\n"
    if admin_cmds_text:
        Help.add_field(
            name='-------------------------' + (ADMIN_ROLE or "Administrator") + ' Commands-------------------------',
            value=admin_cmds_text.strip(), inline=False)

    Help.add_field(name='Custom Admin Command',
                   value='**admin <custom_command>**: Runs any command as admin (requires Administrator role)',
                   inline=False)

    if TOKEN is None:
        print("エラー: DISCORD_TOKENが設定されていません。.envファイルを確認してください。")
    else:
        try:
            client.run(TOKEN)
        except discord.PrivilegedIntentsRequired as e:
            print(
                f"エラー: Botに必要なインテントが有効になっていません。Discord Developer Portalで設定を確認してください: {e}")
        except Exception as e:
            print(f"ボットの起動中にエラーが発生しました: {e}")
