# import beaker as B
# import pyteal as P
#
# from smart_contracts.aurally.boxes import (
#     Event,
#     EventTicket,
#     Proposal,
# )
# from .states import AppState
#
# app = B.Application("Aurally", state=AppState()).apply(
#     B.unconditional_create_approval, initialize_global_state=True
# )
#
#
# @app.update(authorize=B.Authorize.only_creator(), bare=True)
# def update() -> P.Expr:
#     return P.Approve()
#
#
# @app.delete(authorize=B.Authorize.only_creator(), bare=True)
# def delete() -> P.Expr:
#     return P.Approve()


# Todo: Update SoundNFT owner on creation
# Todo: Update ArtNFT owner on creation


# @app.external
# def place_nft_on_sale(
#     txn: P.abi.PaymentTransaction,
#     asset_key: P.abi.String,
#     nft_type: P.abi.String,
#     asset: P.abi.Asset,
# ):
#     from .subroutines import (
#         update_sound_nft_sale,
#         update_art_nft_sale,
#         validate_sound_nft_owner,
#         validate_art_nft_owner,
#     )
#     from .helpers.validators import ensure_zero_payment
#
#     return P.Seq(
#         ensure_zero_payment(txn),
#         P.Assert(
#             P.Or(nft_type.get() == P.Bytes("art"), nft_type.get() == P.Bytes("sound")),
#             comment="nft_type can only be `art` or `sound`",
#         ),
#         (for_sale := P.abi.Bool()).set(True),
#         P.If(
#             nft_type.get() == P.Bytes("sound"),
#             P.Seq(
#                 validate_sound_nft_owner(txn, asset_key),
#                 update_sound_nft_sale(asset_key, for_sale),
#             ),
#             P.Seq(
#                 validate_art_nft_owner(txn, asset_key),
#                 update_art_nft_sale(asset_key, for_sale),
#             ),
#         ),
#     )
#
#
# @app.external
# def purchase_nft(
#     txn: P.abi.PaymentTransaction,
#     optin_txn: P.abi.AssetTransferTransaction,
#     asset_key: P.abi.String,
#     nft_type: P.abi.String,
#     seller: P.abi.Account,
#     nft_id: P.abi.Asset,
#     aura_id: P.abi.Asset,
#     aura_optin_txn: P.abi.AssetTransferTransaction,
#     buyer: P.abi.Account,
# ):
#     from .subroutines import perform_sound_nft_sale, perform_art_nft_sale
#
#     return P.Seq(
#         P.Assert(
#             P.Or(nft_type.get() == P.Bytes("sound"), nft_type.get() == P.Bytes("art"))
#         ),
#         P.If(
#             nft_type.get() == P.Bytes("sound"),
#             perform_sound_nft_sale(txn, asset_key),
#             perform_art_nft_sale(txn, asset_key),
#         ),
#     )
#
#
# @app.external
# def transfer_nft(
#     txn: P.abi.PaymentTransaction,
#     to: P.abi.Address,
#     asset_key: P.abi.String,
#     nft_type: P.abi.String,
# ):
#     from .subroutines import (
#         validate_art_nft_owner,
#         update_art_nft_owner,
#     )
#
#     return P.Seq(
#         P.Assert(txn.get().amount() == P.Int(0)),
#         P.Assert(
#             P.Or(nft_type.get() == P.Bytes("ticket"), nft_type.get() == P.Bytes("art"))
#         ),
#         P.If(
#             nft_type.get() == P.Bytes("art"),
#             P.Seq(
#                 validate_art_nft_owner(txn, asset_key),
#                 update_art_nft_owner(asset_key, to),
#             ),
#         ),
#     )

#
# @app.external
# def hello(name: P.abi.String, *, output: P.abi.String) -> P.Expr:
#     return output.set(P.Concat(name.get(), P.Bytes(" World")))
