import os
from pathlib import Path
from typing import List

import pytest
from algokit_utils import get_algod_client, is_localnet
from algosdk.v2client.algod import AlgodClient
from beaker import localnet
from beaker.client import ApplicationClient
from beaker.consts import algo
from beaker.localnet import LocalAccount
from dotenv import load_dotenv
from smart_contracts.community import contract as community_contract
from smart_contracts.nfts import contract as nft_contract
from tests.utils import build_contract


@pytest.fixture(scope="session")
def test_accounts() -> List[LocalAccount]:
    return localnet.kmd.get_accounts()


@pytest.fixture(scope="session")
def test_account(test_accounts: List[LocalAccount]) -> LocalAccount:
    return test_accounts[0]


@pytest.fixture(scope="session")
def creator_account(test_accounts: List[LocalAccount]) -> LocalAccount:
    return test_accounts[1]


@pytest.fixture(autouse=True, scope="session")
def environment_fixture() -> None:
    env_path = Path(__file__).parent.parent.parent / ".env.localnet"
    load_dotenv(env_path)
    print(env_path)
    print(os.environ.get("ALGOD_SERVER") or None)


@pytest.fixture(scope="session")
def algod_client() -> AlgodClient:
    client = get_algod_client()

    # you can remove this assertion to test on other networks,
    # included here to prevent accidentally running against other networks
    assert is_localnet(client)
    return client


@pytest.fixture(scope="session")
def nft_app_client(creator_account: LocalAccount) -> ApplicationClient:
    build_contract("Aurally_NFT", "NFT")

    client = ApplicationClient(
        app=nft_contract.app,
        signer=creator_account.signer,
        sender=creator_account.address,
        client=localnet.get_algod_client(),
    )
    client.create()
    client.fund(2 * algo)
    return client


@pytest.fixture(scope="session")
def community_app_client(test_accounts: List[LocalAccount]) -> ApplicationClient:
    build_contract("Aurally_Community", "Community")

    app_creator_account = test_accounts[0]

    client = ApplicationClient(
        app=community_contract.app,
        signer=app_creator_account.signer,
        sender=app_creator_account.address,
        client=localnet.get_algod_client(),
    )
    client.create()
    client.fund(2 * algo)
    return client


@pytest.fixture(scope="session")
def aura_index(nft_app_client: ApplicationClient) -> int:
    result = nft_app_client.call(
        nft_contract.create_aura_tokens,
        boxes=[(nft_app_client.app_id, "aura".encode())],
    )
    assert list(result.return_value)[1] == "aura"
    return list(result.return_value)[0]
