from datetime import datetime, timedelta
from typing import List, Tuple

import pytest
from algosdk import atomic_transaction_composer, encoding, transaction
from algosdk.v2client.algod import AlgodClient
from beaker.client import ApplicationClient
from beaker.localnet import LocalAccount
from smart_contracts.nfts import contract as nft_contract


def test_update_commission_percentage(nft_app_client: ApplicationClient):
    result = nft_app_client.call(nft_contract.update_commission_percentage, amt=20)
    print(result.return_value)
    assert result.return_value == 20


@pytest.mark.dependency()
def test_register_creator(
    nft_app_client: ApplicationClient,
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
    result = nft_app_client.call(
        nft_contract.register_creator,
        txn=txn,
        boxes=[
            (nft_app_client.app_id, encoding.decode_address(txn.txn.sender)),
        ],
    )
    assert list(result.return_value)[0] == test_account.address


@pytest.mark.dependency()
@pytest.fixture(scope="session")
def test_create_sound_nft(
    algod_client: AlgodClient,
    nft_app_client: ApplicationClient,
    test_account: LocalAccount,
    aura_index: int,
) -> Tuple[int, str]:
    asset_key = f"Dev Stockins_{datetime.utcnow()}"

    nft_name = "Dev Stockins"
    sp = algod_client.suggested_params()
    raw_txn = transaction.PaymentTxn(
        sender=test_account.address, receiver=test_account.address, amt=0, sp=sp
    )
    txn = atomic_transaction_composer.TransactionWithSigner(
        txn=raw_txn, signer=test_account.signer
    )

    result = nft_app_client.call(
        nft_contract.create_sound_nft,
        txn=txn,
        nft_name=nft_name,
        asset_key=asset_key,
        title="Dev Tokens",
        label="Dev Records",
        artist="GigaChad",
        release_date=200023021,
        genre="Pop",
        description="Some song description",
        price=20000,
        cover_image_url="some_id",
        aura=aura_index,
        creator=test_account.address,
        supply=20,
        boxes=[
            (nft_app_client.app_id, asset_key.encode()),
            (nft_app_client.app_id, b"aura"),
            (nft_app_client.app_id, encoding.decode_address(txn.txn.sender)),
        ],
    )
    assert list(result.return_value)[3] == "Dev Tokens"
    return (result.return_value[0], asset_key)


@pytest.mark.dependency()
@pytest.fixture(scope="session")
def test_create_art_nft(
    algod_client: AlgodClient,
    nft_app_client: ApplicationClient,
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

    result = nft_app_client.call(
        nft_contract.create_art_nft,
        txn=txn,
        title=nft_name,
        nft_name=nft_name,
        asset_key=url,
        name=nft_name,
        description="Gear 5 Luffy",
        image_url=url,
        price=20000,
        aura=aura_index,
        creator=test_account.address,
        boxes=[
            (nft_app_client.app_id, url.encode()),
            (nft_app_client.app_id, b"aura"),
            (nft_app_client.app_id, encoding.decode_address(txn.txn.sender)),
        ],
    )

    assert list(result.return_value)[2] == nft_name
    return (list(result.return_value)[0], url)


@pytest.mark.dependency()
def test_claim_created_art(
    algod_client: AlgodClient,
    nft_app_client: ApplicationClient,
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
    result = nft_app_client.call(
        nft_contract.claim_created_art,
        txn=txn,
        asset_key=test_create_art_nft[1],
        receiver=test_account.address,
        asset=test_create_art_nft[0],
        boxes=[(nft_app_client.app_id, test_create_art_nft[1].encode())],
    )
    assert result.return_value[-4] == test_account.address


# @pytest.mark.skip
@pytest.mark.dependency()
def test_create_art_auction(
    algod_client: AlgodClient,
    nft_app_client: ApplicationClient,
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

    result = nft_app_client.call(
        nft_contract.create_art_auction,
        txn=txn,
        asset_key=test_create_art_nft[1],
        auction_key=auction_key,
        min_bid=10000,
        description="An auction for the just created art",
        starts_at=int(starts_at.timestamp()),
        ends_at=int(ends_at.timestamp()),
        boxes=[
            (nft_app_client.app_id, auction_key.encode()),
            (nft_app_client.app_id, test_create_art_nft[1].encode()),
        ],
    )

    assert list(result.return_value)[2] == test_create_art_nft[1]


# @pytest.mark.skip
@pytest.mark.dependency()
def test_bid_on_auction(
    algod_client: AlgodClient,
    nft_app_client: ApplicationClient,
    test_accounts: List[LocalAccount],
    test_create_art_nft: Tuple[int, str],
    aura_index: int,
):
    auction_key = "Test auction"
    sp = algod_client.suggested_params()
    bidder_account = test_accounts[1]
    raw_txn = transaction.PaymentTxn(
        sender=bidder_account.address,
        sp=sp,
        receiver=nft_app_client.app_addr,
        amt=20000,
    )
    txn = atomic_transaction_composer.TransactionWithSigner(
        txn=raw_txn, signer=bidder_account.signer
    )
    optin_txn = transaction.AssetOptInTxn(
        sender=bidder_account.address, sp=sp, index=test_create_art_nft[0]
    )

    optin_txn = atomic_transaction_composer.TransactionWithSigner(
        txn=optin_txn, signer=bidder_account.signer
    )
    aura_optin_txn = transaction.AssetOptInTxn(
        sender=bidder_account.address, sp=sp, index=aura_index
    )

    aura_optin_txn = atomic_transaction_composer.TransactionWithSigner(
        txn=aura_optin_txn, signer=bidder_account.signer
    )

    result = nft_app_client.call(
        nft_contract.bid_on_art_auction,
        txn=txn,
        optin_txn=optin_txn,
        aura_optin_txn=aura_optin_txn,
        current_highest_bidder=nft_app_client.app_addr,
        auction_key=auction_key,
        boxes=[
            (nft_app_client.app_id, auction_key.encode()),
            (nft_app_client.app_id, test_create_art_nft[1].encode()),
            (nft_app_client.app_id, "aura".encode()),
        ],
    )

    assert list(result.return_value)[-2] == bidder_account.address


# @pytest.mark.skip
# @pytest.mark.dependency(depends=["test_bid_on_auction"])
def test_complete_art_auction(
    algod_client: AlgodClient,
    nft_app_client: ApplicationClient,
    test_account: LocalAccount,
    test_accounts: List[LocalAccount],
    test_create_art_nft: Tuple[int, str],
    aura_index: int,
):
    auction_key = "Test auction"
    sp = algod_client.suggested_params()
    bidder_account = test_accounts[1]

    raw_txn = transaction.AssetTransferTxn(
        sender=test_account.address,
        receiver=bidder_account.address,
        amt=1,
        sp=sp,
        index=test_create_art_nft[0],
    )

    txn = atomic_transaction_composer.TransactionWithSigner(
        txn=raw_txn, signer=test_account.signer
    )

    result = nft_app_client.call(
        nft_contract.complete_art_auction,
        txn=txn,
        aura=aura_index,
        auction_key=auction_key,
        auctioneer_account=test_account.address,
        highest_bidder_account=bidder_account.address,
        boxes=[
            (nft_app_client.app_id, test_create_art_nft[1].encode()),
            (nft_app_client.app_id, auction_key.encode()),
            (nft_app_client.app_id, "aura".encode()),
        ],
    )

    print(result.return_value)
    assert list(result.return_value)[-4] == bidder_account.address


def test_place_art_on_sale(
    algod_client: AlgodClient,
    nft_app_client: ApplicationClient,
    test_accounts: List[LocalAccount],
    test_create_art_nft: Tuple[int, str],
):
    bidder_account = test_accounts[1]
    sp = algod_client.suggested_params()
    txn = transaction.AssetTransferTxn(
        sender=bidder_account.address,
        receiver=nft_app_client.app_addr,
        sp=sp,
        index=test_create_art_nft[0],
        amt=1,
    )
    txn = atomic_transaction_composer.TransactionWithSigner(
        txn=txn, signer=bidder_account.signer
    )

    result = nft_app_client.call(
        nft_contract.place_art_on_sale,
        txn=txn,
        asset_key=test_create_art_nft[1],
        sale_price=20000,
        boxes=[
            (nft_app_client.app_id, test_create_art_nft[1].encode()),
        ],
    )
    print(result.return_value)
    assert list(result.return_value)[-3] == True


# @pytest.mark.skip
def test_purchase_nft(
    algod_client: AlgodClient,
    nft_app_client: ApplicationClient,
    test_account: LocalAccount,
    test_accounts: List[LocalAccount],
    test_create_sound_nft: Tuple[int, str],
    aura_index: int,
):
    buyer_account = test_accounts[1]
    sp = algod_client.suggested_params()

    raw_txn = transaction.PaymentTxn(
        sender=buyer_account.address, receiver=nft_app_client.app_addr, amt=20000, sp=sp
    )
    txn = atomic_transaction_composer.TransactionWithSigner(
        txn=raw_txn, signer=buyer_account.signer
    )

    optin_txn = transaction.AssetOptInTxn(
        sender=buyer_account.address, index=test_create_sound_nft[0], sp=sp
    )
    optin_txn = atomic_transaction_composer.TransactionWithSigner(
        txn=optin_txn, signer=buyer_account.signer
    )
    aura_optin_txn = transaction.AssetOptInTxn(
        sender=buyer_account.address, index=aura_index, sp=sp
    )
    aura_optin_txn = atomic_transaction_composer.TransactionWithSigner(
        txn=aura_optin_txn, signer=buyer_account.signer
    )

    nft_app_client.call(
        nft_contract.purchase_nft,
        txn=txn,
        optin_txn=optin_txn,
        asset_key=test_create_sound_nft[1],
        asset_type="sound",
        buyer=buyer_account.address,
        seller_account=test_account.address,
        aura=aura_index,
        asset=test_create_sound_nft[0],
        aura_optin_txn=aura_optin_txn,
        boxes=[
            (nft_app_client.app_id, b"aura"),
            (nft_app_client.app_id, test_create_sound_nft[1].encode()),
        ],
    )


def test_update_aura_rewards(
    nft_app_client: ApplicationClient,
):
    nft_app_client.call(
        nft_contract.update_aura_rewards,
    )
