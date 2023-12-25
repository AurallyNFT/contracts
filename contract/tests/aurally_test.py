# from datetime import datetime, timedelta
# import os
# from pathlib import Path
# from typing import List, Tuple
# from algosdk import atomic_transaction_composer, encoding, transaction
# from beaker import localnet
# from beaker.client import ApplicationClient
# from beaker.consts import algo
# from beaker.localnet.kmd import LocalAccount
# import pytest
# from algosdk.v2client.algod import AlgodClient
#
# from smart_contracts.aurally import contract as aurally_contract
#
#
# @pytest.fixture(scope="session")
# def aurally_client(test_accounts: List[LocalAccount]) -> ApplicationClient:
#     artifacts_dir = (
#         Path(__file__)
#         .resolve()
#         .parent.parent.joinpath("smart_contracts")
#         .joinpath("artifacts")
#         .joinpath("Aurally")
#     )
#     if not artifacts_dir.is_dir():
#         os.makedirs(artifacts_dir, exist_ok=True)
#     aurally_contract.app.build().export(artifacts_dir)
#
#     app_account = test_accounts[0]
#
#     client = ApplicationClient(
#         app=aurally_contract.app,
#         signer=app_account.signer,
#         sender=app_account.address,
#         client=localnet.get_algod_client(),
#     )
#     client.create(extra_pages=3)
#     client.fund(2 * algo)
#     return client
#
#
# @pytest.fixture(scope="session")
# def auction_key() -> str:
#     return f"The Auction _ {datetime.utcnow()}"
#
#
# def test_says_hello(aurally_client: ApplicationClient) -> None:
#     result = aurally_client.call(aurally_contract.hello, name="Hello")
#     assert result.return_value == "Hello World"
#
#
# def test_get_registered_creative(
#     aurally_client: ApplicationClient, test_account: LocalAccount
# ):
#     res = aurally_client.call(
#         aurally_contract.get_registered_creative,
#         addr=test_account.address,
#         boxes=[(aurally_client.app_id, encoding.decode_address(test_account.address))],
#     )
#
#     print(res.return_value)
#     assert list(res.return_value)[3] == "Dev Ready"


# # @pytest.mark.skip
# def test_bid_on_auction(
#     algod_client: AlgodClient,
#     aurally_client: ApplicationClient,
#     test_account: LocalAccount,
#     auction_key: str,
# ):
#     sp = algod_client.suggested_params()
#     raw_txn = transaction.PaymentTxn(
#         sender=test_account.address, sp=sp, receiver=test_account.address, amt=0
#     )
#     txn = atomic_transaction_composer.TransactionWithSigner(
#         txn=raw_txn, signer=test_account.signer
#     )
#
#     result = aurally_client.call(
#         aurally_contract.bid_on_art_auction,
#         txn=txn,
#         auction_key=auction_key,
#         bid_ammount=20000,
#         boxes=[(aurally_client.app_id, auction_key.encode())],
#     )
#
#     assert list(result.return_value)[6] == 20000
#
#
# # @pytest.mark.skip
# def test_complete_art_auction(
#     algod_client: AlgodClient,
#     aurally_client: ApplicationClient,
#     test_account: LocalAccount,
#     auction_key: str,
# ):
#     nft_name = "Sun God Nika"
#     sp = algod_client.suggested_params()
#     url = "https://ipfs.io/ipfs/" + nft_name
#     raw_txn = transaction.PaymentTxn(
#         sender=test_account.address, receiver=test_account.address, amt=0, sp=sp
#     )
#
#     txn = atomic_transaction_composer.TransactionWithSigner(
#         txn=raw_txn, signer=test_account.signer
#     )
#
#     result = aurally_client.call(
#         aurally_contract.complete_art_auction,
#         txn=txn,
#         auction_key=auction_key,
#         boxes=[
#             (aurally_client.app_id, url.encode()),
#             (aurally_client.app_id, auction_key.encode()),
#         ],
#     )
#
#     assert list(result.return_value)[2] == nft_name
#
#
# def test_place_nft_on_sale(
#     algod_client: AlgodClient,
#     aurally_client: ApplicationClient,
#     test_account: LocalAccount,
#     test_create_sound_nft: Tuple[str, int],
# ):
#     print(test_account.address, aurally_client.app_addr)
#     sp = algod_client.suggested_params()
#     txn = transaction.PaymentTxn(
#         sender=test_account.address,
#         receiver=aurally_client.app_addr,
#         sp=sp,
#         amt=0,
#     )
#     txn = atomic_transaction_composer.TransactionWithSigner(
#         txn=txn, signer=test_account.signer
#     )
#     aurally_client.call(
#         aurally_contract.place_nft_on_sale,
#         txn=txn,
#         asset=test_create_sound_nft[1],
#         asset_key=test_create_sound_nft[0],
#         nft_type="sound",
#         boxes=[(aurally_client.app_id, test_create_sound_nft[0].encode())],
#     )
#
#
# # @pytest.mark.skip
# def test_purchase_nft(
#     algod_client: AlgodClient,
#     aurally_client: ApplicationClient,
#     test_account: LocalAccount,
#     test_accounts: List[LocalAccount],
#     test_create_sound_nft: Tuple[str, int],
#     aura_token: int,
# ):
#     buyer_account = test_accounts[1]
#     sp = algod_client.suggested_params()
#
#     raw_txn = transaction.PaymentTxn(
#         sender=buyer_account.address, receiver=aurally_client.app_addr, amt=20000, sp=sp
#     )
#     txn = atomic_transaction_composer.TransactionWithSigner(
#         txn=raw_txn, signer=buyer_account.signer
#     )
#
#     optin_txn = transaction.AssetOptInTxn(
#         sender=buyer_account.address, index=test_create_sound_nft[1], sp=sp
#     )
#     optin_txn = atomic_transaction_composer.TransactionWithSigner(
#         txn=optin_txn, signer=buyer_account.signer
#     )
#     aura_optin_txn = transaction.AssetOptInTxn(
#         sender=buyer_account.address, index=aura_token, sp=sp
#     )
#     aura_optin_txn = atomic_transaction_composer.TransactionWithSigner(
#         txn=aura_optin_txn, signer=buyer_account.signer
#     )
#
#     aurally_client.call(
#         aurally_contract.purchase_nft,
#         txn=txn,
#         asset_key=test_create_sound_nft[0],
#         nft_type="sound",
#         seller=test_account.address,
#         optin_txn=optin_txn,
#         buyer=buyer_account.address,
#         aura_optin_txn=aura_optin_txn,
#         nft_id=test_create_sound_nft[1],
#         aura_id=aura_token,
#         boxes=[
#             (aurally_client.app_id, "aura".encode()),
#             (aurally_client.app_id, test_create_sound_nft[0].encode()),
#         ],
#     )
#
#
# # @pytest.mark.skip
# def test_transfer_nft(
#     algod_client: AlgodClient,
#     aurally_client: ApplicationClient,
#     test_accounts: List[LocalAccount],
#     test_account: LocalAccount,
#     test_create_art_nft: Tuple[str, int],
# ):
#     sp = algod_client.suggested_params()
#     raw_txn = transaction.PaymentTxn(
#         sender=test_account.address, receiver=test_account.address, sp=sp, amt=0
#     )
#     txn = atomic_transaction_composer.TransactionWithSigner(
#         txn=raw_txn, signer=test_account.signer
#     )
#
#     aurally_client.call(
#         aurally_contract.transfer_nft,
#         txn=txn,
#         to=test_accounts[1].address,
#         asset_key=test_create_art_nft[0],
#         nft_type="art",
#         boxes=[(aurally_client.app_id, test_create_art_nft[0].encode())],
#     )
#
#
# # @pytest.mark.skip
# def test_create_proposal(
#     algod_client: AlgodClient,
#     aurally_client: ApplicationClient,
#     test_account: LocalAccount,
# ):
#     sp = algod_client.suggested_params()
#     raw_txn = transaction.PaymentTxn(
#         sender=test_account.address, receiver=test_account.address, sp=sp, amt=0
#     )
#     txn = atomic_transaction_composer.TransactionWithSigner(
#         txn=raw_txn, signer=test_account.signer
#     )
#
#     proposal_key = "Proposal to bring Gojo back"
#     proposal_detail = """
#             Gojo is the GOAT, and deserves to be brought back.
#             But I also like Sukuna, so I have mixed feeligs
#         """
#
#     result = aurally_client.call(
#         aurally_contract.create_proposal,
#         txn=txn,
#         title=proposal_key,
#         proposal_key=proposal_key,
#         proposal_detail=proposal_detail,
#         end_date=int(datetime.now().timestamp()),
#         boxes=[
#             (aurally_client.app_id, proposal_key.encode()),
#             (aurally_client.app_id, encoding.decode_address(test_account.address)),
#         ],
#     )
#
#     assert list(result.return_value)[0] == proposal_key
#
#
# # @pytest.mark.skip
# def test_vote_on_proposal(
#     algod_client: AlgodClient,
#     aurally_client: ApplicationClient,
#     test_account: LocalAccount,
#     aura_token: int,
# ):
#     sp = algod_client.suggested_params()
#     raw_txn = transaction.PaymentTxn(
#         sender=test_account.address, receiver=test_account.address, sp=sp, amt=0
#     )
#     txn = atomic_transaction_composer.TransactionWithSigner(
#         txn=raw_txn, signer=test_account.signer
#     )
#
#     proposal_key = "Proposal to bring Gojo back"
#
#     result = aurally_client.call(
#         aurally_contract.vote_on_proposal,
#         txn=txn,
#         vote_for=True,
#         proposal_key=proposal_key,
#         aura_id=aura_token,
#         voter=test_account.address,
#         boxes=[
#             (aurally_client.app_id, "aura".encode()),
#             (aurally_client.app_id, proposal_key.encode()),
#             (aurally_client.app_id, encoding.decode_address(test_account.address)),
#         ],
#     )
#
#     assert list(result.return_value)[2] > 0
#
#
# def test_end_proposal_voting(
#     algod_client: AlgodClient,
#     aurally_client: ApplicationClient,
#     test_account: LocalAccount,
# ):
#     sp = algod_client.suggested_params()
#     raw_txn = transaction.PaymentTxn(
#         sender=test_account.address, receiver=test_account.address, sp=sp, amt=0
#     )
#     txn = atomic_transaction_composer.TransactionWithSigner(
#         txn=raw_txn, signer=test_account.signer
#     )
#
#     proposal_key = "Proposal to bring Gojo back"
#
#     result = aurally_client.call(
#         aurally_contract.end_proposal_voting,
#         txn=txn,
#         proposal_key=proposal_key,
#         boxes=[
#             (aurally_client.app_id, proposal_key.encode()),
#             (aurally_client.app_id, encoding.decode_address(test_account.address)),
#         ],
#     )
#
#     assert list(result.return_value)[0] == proposal_key
#
#
# def test_unfreeze_auras(
#     algod_client: AlgodClient,
#     aurally_client: ApplicationClient,
#     test_account: LocalAccount,
#     aura_token: int,
# ):
#     sp = algod_client.suggested_params()
#     raw_txn = transaction.PaymentTxn(
#         sender=test_account.address, receiver=test_account.address, sp=sp, amt=0
#     )
#     txn = atomic_transaction_composer.TransactionWithSigner(
#         txn=raw_txn, signer=test_account.signer
#     )
#
#     aurally_client.call(
#         aurally_contract.unfreeze_auras,
#         txn=txn,
#         aura=aura_token,
#         acc=test_account.address,
#         boxes=[(aurally_client.app_id, "aura".encode())],
#     )
#
#
# def test_promote_to_admin(
#     algod_client: AlgodClient,
#     aurally_client: ApplicationClient,
#     test_accounts: List[LocalAccount],
# ):
#     test_account = test_accounts[0]
#     sp = algod_client.suggested_params()
#     raw_txn = transaction.PaymentTxn(
#         sender=test_account.address, receiver=test_account.address, sp=sp, amt=0
#     )
#     txn = atomic_transaction_composer.TransactionWithSigner(
#         txn=raw_txn, signer=test_account.signer
#     )
#
#     result = aurally_client.call(
#         aurally_contract.promote_to_admin,
#         txn=txn,
#         acc=test_account.address,
#         boxes=[(aurally_client.app_id, encoding.decode_address(test_account.address))],
#     )
#     is_admin = result.return_value
#
#     assert is_admin == "True"
#
#
# def test_demote_from_admin(
#     algod_client: AlgodClient,
#     aurally_client: ApplicationClient,
#     test_accounts: List[LocalAccount],
# ):
#     test_account = test_accounts[0]
#     sp = algod_client.suggested_params()
#     raw_txn = transaction.PaymentTxn(
#         sender=test_account.address, receiver=test_account.address, sp=sp, amt=0
#     )
#     txn = atomic_transaction_composer.TransactionWithSigner(
#         txn=raw_txn, signer=test_account.signer
#     )
#
#     result = aurally_client.call(
#         aurally_contract.demote_from_admin,
#         txn=txn,
#         acc=test_account.address,
#         boxes=[(aurally_client.app_id, encoding.decode_address(test_account.address))],
#     )
#     is_admin = result.return_value
#
#     assert is_admin == "False"
#
#
# def test_create_event(
#     aurally_client: ApplicationClient,
#     algod_client: AlgodClient,
#     test_account: LocalAccount,
# ):
#     sp = algod_client.suggested_params()
#     txn = transaction.PaymentTxn(
#         amt=0, sender=test_account.address, receiver=test_account.address, sp=sp
#     )
#     txn = atomic_transaction_composer.TransactionWithSigner(
#         txn=txn, signer=test_account.signer
#     )
#
#     start_date = int(datetime.utcnow().timestamp())
#     end_date = int(datetime.utcnow().timestamp())
#
#     result = aurally_client.call(
#         aurally_contract.create_event,
#         txn=txn,
#         key="Test Event",
#         name="Test Event",
#         start_date=start_date,
#         end_date=end_date,
#         cover_image_ipfs="image.url",
#         ticket_price=20000,
#         boxes=[(aurally_client.app_id, "Test Event".encode())],
#     )
#     assert list(result.return_value)[1] == "Test Event"
#
#
# def test_purchase_event_ticket(
#     aurally_client: ApplicationClient,
#     algod_client: AlgodClient,
#     test_account: LocalAccount,
#     test_accounts: List[LocalAccount],
# ):
#     buyer_account = test_accounts[0]
#
#     sp = algod_client.suggested_params()
#     txn = transaction.PaymentTxn(
#         sender=buyer_account.address, receiver=aurally_client.app_addr, amt=20000, sp=sp
#     )
#     txn = atomic_transaction_composer.TransactionWithSigner(
#         txn=txn, signer=buyer_account.signer
#     )
#
#     result = aurally_client.call(
#         aurally_contract.purchase_event_ticket,
#         txn=txn,
#         event_key="Test Event",
#         ticket_key="Test Event Key",
#         event_owner=test_account.address,
#         boxes=[
#             (aurally_client.app_id, "Test Event".encode()),
#             (aurally_client.app_id, "Test Event Key".encode()),
#         ],
#     )
#     assert list(result.return_value)[1] == "Test Event Key"
