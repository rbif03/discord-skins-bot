import boto3

ssm = boto3.client("ssm", "us-east-1")


# https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html
def get_parameter(key: str) -> str:
    response = ssm.get_parameters(Names=[key], WithDecryption=True)
    for parameter in response["Parameters"]:
        return parameter["Value"]
