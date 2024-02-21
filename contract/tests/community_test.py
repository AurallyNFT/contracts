from algosdk import encoding
from beaker.client import ApplicationClient
from beaker.localnet import LocalAccount
from smart_contracts.community import contract as community_contract


def test_promote_to_admin(
    community_app_client: ApplicationClient,
    test_account: LocalAccount,
) -> None:
    community_app_client.call(
        community_contract.promote_to_admin,
        acc=test_account.address,
        boxes=[
            (community_app_client.app_id, encoding.decode_address(test_account.address))
        ],
    )


# def test_set_nft_app(
#     nft_app_client: ApplicationClient,
#     community_app_client: ApplicationClient,
# ):
#     community_app_client.call(
#         community_contract.set_nft_app, app_id=nft_app_client.app_id
#     )
#
#
# def test_set_aura_token(
#     aura_index: int,
#     community_app_client: ApplicationClient,
# ):
#     community_app_client.call(
#         community_contract.set_aura_token,
#         aura=aura_index,
#     )
#
#
# def test_create_proposal(
#     community_app_client: ApplicationClient,
#     test_account: LocalAccount,
#     algod_client: AlgodClient,
# ):
#     sp = algod_client.suggested_params()
#     txn = transaction.PaymentTxn(
#         amt=0,
#         sp=sp,
#         sender=test_account.address,
#         receiver=test_account.address,
#     )
#     txn = atomic_transaction_composer.TransactionWithSigner(
#         txn=txn, signer=test_account.signer
#     )
#     community_app_client.call(
#         community_contract.create_proposal,
#         txn=txn,
#         title="test",
#         proposal_key="test",
#         proposal_detail="test",
#         end_date=70,
#         boxes=[
#             (community_app_client.app_id, "test".encode()),
#             (
#                 community_app_client.app_id,
#                 encoding.decode_address(test_account.address),
#             ),
#         ],
#     )


#
# def test_create_proposal(
#     community_app_client: ApplicationClient,
#     test_account: LocalAccount,
#     algod_client: AlgodClient,
# ):
#     sp = algod_client.suggested_params()
#     raw_txn = transaction.PaymentTxn(
#         sender=test_account.address, receiver=test_account.address, sp=sp, amt=0
#     )
#     txn = atomic_transaction_composer.TransactionWithSigner(
#         txn=raw_txn, signer=test_account.signer
#     )
#
#     proposal_key = "The test proposal"
#     proposal_detail = """
#             The Test proposal details
#         """
#
#     result = community_app_client.call(
#         community_contract.create_proposal,
#         txn=txn,
#         title=proposal_key,
#         proposal_key=proposal_key,
#         proposal_detail=proposal_detail,
#         end_date=int(datetime.now().timestamp()),
#         boxes=[
#             (community_app_client.app_id, proposal_key.encode()),
#             (
#                 community_app_client.app_id,
#                 encoding.decode_address(test_account.address),
#             ),
#         ],
#     )
#
#     assert list(result.return_value)[0] == proposal_key
