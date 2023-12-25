import pytest
from datetime import datetime, timedelta
from typing import List, Tuple
from algosdk import atomic_transaction_composer, encoding, transaction
from algosdk.v2client.algod import AlgodClient
from beaker import localnet
from beaker.client import ApplicationClient
from beaker.consts import algo
from beaker.localnet import LocalAccount
from tests.utils import build_contract
from smart_contracts.nfts import contract as nft_contract


@pytest.fixture(scope="session")
def app_client(test_accounts: List[LocalAccount]) -> ApplicationClient:
    build_contract("Aurally_NFT", "NFT")

    app_account = test_accounts[0]

    client = ApplicationClient(
        app=nft_contract.app,
        signer=app_account.signer,
        sender=app_account.address,
        client=localnet.get_algod_client(),
    )
    client.create()
    client.fund(2 * algo)
    return client


@pytest.fixture(scope="session")
def aura_index(app_client: ApplicationClient) -> int:
    result = app_client.call(
        nft_contract.create_aura_tokens,
        boxes=[(app_client.app_id, "aura".encode())],
    )
    assert list(result.return_value)[1] == "aura"
    return list(result.return_value)[0]


def test_create_aura_tokens(app_client: ApplicationClient):
    result = app_client.call(
        nft_contract.create_aura_tokens,
        boxes=[(app_client.app_id, "aura".encode())],
    )
    assert list(result.return_value)[1] == "aura"


def test_register_creator(
    app_client: ApplicationClient,
    test_account: LocalAccount,
    algod_client: AlgodClient,
    aura_index: int,
) -> None:
    sp = algod_client.suggested_params()
    opt_txn = transaction.AssetOptInTxn(
        sp=sp, sender=test_account.address, index=aura_index
    )
    txn = atomic_transaction_composer.TransactionWithSigner(
        txn=opt_txn, signer=test_account.signer
    )
    result = app_client.call(
        nft_contract.register_creator,
        txn=txn,
        fullname="Dev Ready",
        username="Dev2700",
        boxes=[
            (app_client.app_id, encoding.decode_address(txn.txn.sender)),
        ],
    )
    assert list(result.return_value)[3] == "Dev Ready"


@pytest.fixture(scope="session")
def test_create_sound_nft(
    algod_client: AlgodClient,
    app_client: ApplicationClient,
    test_account: LocalAccount,
    aura_index: int,
):
    asset_key = f"Dev Stockins_{datetime.utcnow()}"

    nft_name = "Dev Stockins"
    sp = algod_client.suggested_params()
    raw_txn = transaction.PaymentTxn(
        sender=test_account.address, receiver=test_account.address, amt=0, sp=sp
    )
    txn = atomic_transaction_composer.TransactionWithSigner(
        txn=raw_txn, signer=test_account.signer
    )

    result = app_client.call(
        nft_contract.create_sound_nft,
        txn=txn,
        nft_name=nft_name,
        asset_key=asset_key,
        title="Dev Tokens",
        label="Dev Reccords",
        artist="GigaChad",
        release_date=200023021,
        genre="Pop",
        price=20000,
        cover_image_ipfs="some_id",
        audio_sample_ipfs="some_other_id",
        full_track_ipfs="yet_another_id",
        aura=aura_index,
        creator=test_account.address,
        supply=20,
        boxes=[
            (app_client.app_id, asset_key.encode()),
            (app_client.app_id, "aura".encode()),
            (app_client.app_id, encoding.decode_address(txn.txn.sender)),
        ],
    )
    assert list(result.return_value)[3] == "Dev Tokens"
    return [result.return_value[0], asset_key]


def test_claim_created_sound(
    algod_client: AlgodClient,
    app_client: ApplicationClient,
    test_account: LocalAccount,
    test_create_sound_nft: Tuple[int, str],
):
    sp = algod_client.suggested_params()
    raw_txn = transaction.AssetTransferTxn(
        sender=test_account.address,
        receiver=test_account.address,
        amt=0,
        sp=sp,
        index=test_create_sound_nft[0],
    )
    txn = atomic_transaction_composer.TransactionWithSigner(
        txn=raw_txn, signer=test_account.signer
    )
    result = app_client.call(
        nft_contract.claim_created_sound,
        txn=txn,
        asset_key=test_create_sound_nft[1],
        reciever=test_account.address,
        asset=test_create_sound_nft[0],
        boxes=[(app_client.app_id, test_create_sound_nft[1].encode())],
    )
    assert result.return_value[-1] == True


@pytest.fixture(scope="session")
def test_create_art_nft(
    algod_client: AlgodClient,
    app_client: ApplicationClient,
    test_account: LocalAccount,
    aura_index: int,
) -> Tuple[int, str]:
    sp = algod_client.suggested_params()
    nft_name = "Sun God Nika"
    url = "https://ipfs.io/ipfs/" + nft_name

    raw_txn = transaction.PaymentTxn(
        sender=test_account.address, receiver=test_account.address, amt=0, sp=sp
    )

    txn = atomic_transaction_composer.TransactionWithSigner(
        txn=raw_txn, signer=test_account.signer
    )

    result = app_client.call(
        nft_contract.create_art_nft,
        txn=txn,
        title=nft_name,
        nft_name=nft_name,
        asset_key=url,
        name=nft_name,
        description="Gear 5 Luffy",
        ipfs_location=url,
        price=20000,
        aura=aura_index,
        creator=test_account.address,
        boxes=[
            (app_client.app_id, url.encode()),
            (app_client.app_id, "aura".encode()),
            (app_client.app_id, encoding.decode_address(txn.txn.sender)),
        ],
    )

    assert list(result.return_value)[2] == nft_name
    return (list(result.return_value)[0], url)


def test_claim_created_art(
    algod_client: AlgodClient,
    app_client: ApplicationClient,
    test_account: LocalAccount,
    test_create_art_nft: Tuple[int, str],
):
    sp = algod_client.suggested_params()

    raw_txn = transaction.AssetTransferTxn(
        sender=test_account.address,
        receiver=test_account.address,
        amt=0,
        sp=sp,
        index=test_create_art_nft[0],
    )
    txn = atomic_transaction_composer.TransactionWithSigner(
        txn=raw_txn, signer=test_account.signer
    )
    result = app_client.call(
        nft_contract.claim_created_art,
        txn=txn,
        asset_key=test_create_art_nft[1],
        reciever=test_account.address,
        asset=test_create_art_nft[0],
        boxes=[(app_client.app_id, test_create_art_nft[1].encode())],
    )
    assert result.return_value[-3] == test_account.address


# @pytest.mark.skip
def test_create_art_auction(
    algod_client: AlgodClient,
    app_client: ApplicationClient,
    test_account: LocalAccount,
    test_create_art_nft: Tuple[int, str],
):
    sp = algod_client.suggested_params()
    raw_txn = transaction.PaymentTxn(
        sender=test_account.address, sp=sp, receiver=test_account.address, amt=0
    )
    txn = atomic_transaction_composer.TransactionWithSigner(
        txn=raw_txn, signer=test_account.signer
    )

    auction_key = "Test auction"
    starts_at = datetime.now() - timedelta(weeks=2)
    ends_at = datetime.now() + timedelta(days=2)

    result = app_client.call(
        nft_contract.create_art_auction,
        txn=txn,
        asset_key=test_create_art_nft[1],
        auction_key=auction_key,
        min_bid=10000,
        description="An auction for the just created art",
        starts_at=int(starts_at.timestamp()),
        ends_at=int(ends_at.timestamp()),
        boxes=[
            (app_client.app_id, auction_key.encode()),
            (app_client.app_id, test_create_art_nft[1].encode()),
        ],
    )

    assert list(result.return_value)[1] == test_create_art_nft[1]
