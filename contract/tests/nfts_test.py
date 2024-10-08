from datetime import datetime, timedelta, timezone
from typing import List, Tuple

import algosdk
import pytest
from algokit_utils import Account
from algosdk import atomic_transaction_composer, encoding, transaction
from algosdk.v2client.algod import AlgodClient
from beaker.client import ApplicationClient
from beaker.localnet import LocalAccount
from smart_contracts.nfts import contract as nft_contract


@pytest.mark.skip
@pytest.mark.dependency()
def test_promote_to_admin(
    nft_app_client: ApplicationClient,
    test_account: LocalAccount,
    creator_account: LocalAccount,
):
    nft_app_client.call(
        nft_contract.promote_to_admin,
        address=test_account.address,
        sender=creator_account.address,
        boxes=[
            (nft_app_client.app_id, encoding.decode_address(test_account.address)),
        ],
    )


@pytest.mark.skip()
def test_reward_with_aura_tokens(
    test_account: LocalAccount,
    nft_app_client: ApplicationClient,
    aura_index: int,
    algod_client: AlgodClient,
):
    sp = algod_client.suggested_params()
    txn = transaction.AssetTransferTxn(
        sender=test_account.address,
        receiver=test_account.address,
        sp=sp,
        amt=0,
        index=aura_index,
    )
    txn = atomic_transaction_composer.TransactionWithSigner(
        txn=txn, signer=test_account.signer
    )
    nft_app_client.call(
        nft_contract.reward_with_aura_tokens,
        txn=txn,
        receiver=test_account.address,
        aura=aura_index,
        boxes=[
            (nft_app_client.app_id, b"aura"),
            (nft_app_client.app_id, encoding.decode_address(test_account.address)),
        ],
    )


@pytest.mark.skip
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
    print(aura_index, result.return_value, test_account.address)
    assert next(iter(result.return_value)) == test_account.address


@pytest.mark.skip
@pytest.mark.dependency()
@pytest.fixture(scope="session")
def test_create_sound_nft(
    algod_client: AlgodClient,
    nft_app_client: ApplicationClient,
    test_account: LocalAccount,
    aura_index: int,
) -> Tuple[int, str]:
    asset_key = f"Dev Stockins_{datetime.now(tz=timezone.utc)}"

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


@pytest.mark.skip
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
    return (next(iter(result.return_value)), url)


@pytest.mark.skip
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


@pytest.mark.skip
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


@pytest.mark.skip
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


@pytest.mark.skip
@pytest.mark.dependency(depends=["test_bid_on_auction"])
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
            (nft_app_client.app_id, b"aura"),
        ],
    )

    print(result.return_value)
    assert list(result.return_value)[-4] == bidder_account.address


@pytest.mark.skip
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


@pytest.mark.skip
def test_purchase_art_nft(
    algod_client: AlgodClient,
    nft_app_client: ApplicationClient,
    test_accounts: List[LocalAccount],
    test_create_art_nft: Tuple[int, str],
    aura_index: int,
):
    buyer_account = test_accounts[-1]
    seller_account = test_accounts[1]
    sp = algod_client.suggested_params()

    raw_txn = transaction.PaymentTxn(
        sender=buyer_account.address, receiver=nft_app_client.app_addr, amt=20000, sp=sp
    )
    txn = atomic_transaction_composer.TransactionWithSigner(
        txn=raw_txn, signer=buyer_account.signer
    )

    optin_txn = transaction.AssetOptInTxn(
        sender=buyer_account.address, index=test_create_art_nft[0], sp=sp
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
        asset_key=test_create_art_nft[1],
        asset_type="art",
        buyer=buyer_account.address,
        seller_account=seller_account.address,
        aura=aura_index,
        asset=test_create_art_nft[0],
        aura_optin_txn=aura_optin_txn,
        boxes=[
            (nft_app_client.app_id, b"aura"),
            (nft_app_client.app_id, test_create_art_nft[1].encode()),
        ],
    )


@pytest.mark.skip
def test_purchase_sound_nft(
    algod_client: AlgodClient,
    nft_app_client: ApplicationClient,
    test_account: LocalAccount,
    test_accounts: List[LocalAccount],
    test_create_sound_nft: Tuple[int, str],
    aura_index: int,
):
    buyer_account = test_accounts[-1]
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


@pytest.mark.skip()
def test_update_aura_rewards(
    nft_app_client: ApplicationClient,
):
    nft_app_client.call(
        nft_contract.update_aura_rewards,
    )


@pytest.mark.skip()
def test_withdraw_profits(
    nft_app_client: ApplicationClient,
    creator_account: LocalAccount,
):
    nft_app_client.call(
        nft_contract.withdraw_profits,
        amt=20,
        to=creator_account.address,
        sender=creator_account.address,
    )


@pytest.mark.skip()
def test_withdraw_auras(
    nft_app_client: ApplicationClient, creator_account: LocalAccount, aura_index: int
):
    nft_app_client.call(
        nft_contract.transfer_auras,
        amount=20,
        receiver=creator_account.address,
        aura=aura_index,
        boxes=[(nft_app_client.app_id, b"aura")],
    )


@pytest.mark.skip()
@pytest.fixture(scope="session")
def live_aura_index(live_client: ApplicationClient) -> int:
    result = live_client.call(
        nft_contract.create_aura_tokens,
        boxes=[(live_client.app_id, b"aura")],
    )
    assert list(result.return_value)[1] == "aura"
    return next(iter(result.return_value))


# @pytest.mark.skip(reason="I know it works")
def test_update_contract(live_client: ApplicationClient):
    live_client.call(nft_contract.update_commission_percentage, amt=15)
    res = live_client.update()
    print(res)


@pytest.mark.skip(reason="I know it works")
@pytest.mark.dependency()
def test_live_register_creator(
    live_client: ApplicationClient, live_aura_index: int
) -> None:
    account = Account(
        private_key=algosdk.mnemonic.to_private_key(
            "ranch swarm elephant enlist gauge basket census item vote drum bonus plunge barrel alarm mean romance leg speak interest soon priority chuckle patch absent armor"
        ),
        address="NEWNSTFUL6E3GXQYUN6CPUQVTQNSUKSLBPOPRRAM2IVIQEE5RAO6MWNL6I",
    )
    sp = live_client.client.suggested_params()
    opt_txn = transaction.AssetOptInTxn(
        sp=sp, sender=account.address, index=live_aura_index
    )
    txn = atomic_transaction_composer.TransactionWithSigner(
        txn=opt_txn, signer=account.signer
    )
    result = live_client.call(
        nft_contract.register_creator,
        txn=txn,
        boxes=[
            (live_client.app_id, encoding.decode_address(txn.txn.sender)),
        ],
    )
    assert list(result.return_value)[0] == account.address


@pytest.mark.skip(reason="I know it works")
def test_live_withdraw_auras(live_client: ApplicationClient, live_aura_index: int):
    live_client.call(
        nft_contract.transfer_auras,
        amount=55010,
        receiver="NEWNSTFUL6E3GXQYUN6CPUQVTQNSUKSLBPOPRRAM2IVIQEE5RAO6MWNL6I",
        aura=live_aura_index,
        boxes=[(live_client.app_id, b"aura")],
    )
