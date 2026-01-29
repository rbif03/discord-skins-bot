import boto3

dynamodb_client = boto3.resource("dynamodb")
tracked_skins_table = dynamodb_client.Table("skinsbot.tracked_skins")


def handler(event, context):
    unique_tracked_skins = set()
    LastEvaluatedKey = None
    while True:
        kwargs = {"ProjectionExpression": "hash_name"}
        if LastEvaluatedKey is not None:
            kwargs["ExclusiveStartKey"] = LastEvaluatedKey

        response = tracked_skins_table.scan(**kwargs)
        for item in response.get("Items"):
            unique_tracked_skins.add(item.get("hash_name", None))

        if not response.get("LastEvaluatedKey"):
            # all the data has been scanned
            break

        LastEvaluatedKey = response.get("LastEvaluatedKey")

    # if, for some reason, None has been added, it will be removed
    unique_tracked_skins.add(None)  # adding to avoid a KeyError
    unique_tracked_skins.remove(None)
    return [{"hash_name": hn} for hn in unique_tracked_skins]


if __name__ == "__main__":
    print(handler(None, None))
