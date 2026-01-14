import config
from services.ssm import get_parameter

parameter_name = config.DISCORD_TOKEN_SSM_PATH
DISCORD_TOKEN = get_parameter(parameter_name)
print(DISCORD_TOKEN)
