import logging

import algokit_utils
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

logger = logging.getLogger(__name__)


# define deployment behaviour based on supplied app spec
def deploy(
    algod_client: AlgodClient,
    indexer_client: IndexerClient,
    deployer: algokit_utils.Account,
) -> None:
    from smart_contracts.artifacts.Aurally_NFT.client import (
        AurallyNftClient,
    )

    app_client = AurallyNftClient(
        algod_client,
        creator=deployer,
        indexer_client=indexer_client,
    )
    is_mainnet = algokit_utils.is_mainnet(algod_client)
    app_client.deploy(
        on_schema_break=(
            algokit_utils.OnSchemaBreak.AppendApp
            if is_mainnet
            else algokit_utils.OnSchemaBreak.AppendApp
        ),
        on_update=algokit_utils.OnUpdate.AppendApp
        if is_mainnet
        else algokit_utils.OnUpdate.UpdateApp,
        # allow_delete=not is_mainnet,
        # allow_update=not is_mainnet,
    )
