from pathlib import Path
from typing import List
from beaker import localnet
from beaker.localnet import LocalAccount
from beaker.client import ApplicationClient
from beaker.consts import algo
from tests.utils import build_contract
from smart_contracts.nfts import contract as nft_contract

import pytest
from algokit_utils import (
    get_algod_client,
    is_localnet,
)
from algosdk.v2client.algod import AlgodClient
from dotenv import load_dotenv


@pytest.fixture(scope="session")
def test_accounts() -> List[LocalAccount]:
    return localnet.kmd.get_accounts()


@pytest.fixture(scope="session")
def test_account(test_accounts: List[LocalAccount]) -> LocalAccount:
    return test_accounts[-1]


@pytest.fixture(autouse=True, scope="session")
def environment_fixture() -> None:
    env_path = Path(__file__).parent.parent / ".env.localnet"
    load_dotenv(env_path)


@pytest.fixture(scope="session")
def algod_client() -> AlgodClient:
    client = get_algod_client()

    # you can remove this assertion to test on other networks,
    # included here to prevent accidentally running against other networks
    assert is_localnet(client)
    return client


@pytest.fixture(scope="session")
def nft_app_client(test_accounts: List[LocalAccount]) -> ApplicationClient:
    build_contract("Aurally_NFT", "NFT")

    app_creator_account = test_accounts[0]

    client = ApplicationClient(
        app=nft_contract.app,
        signer=app_creator_account.signer,
        sender=app_creator_account.address,
        client=localnet.get_algod_client(),
    )
    client.create()
    client.fund(2 * algo)
    return client
