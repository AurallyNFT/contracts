import pyteal as P
from smart_contracts.nfts.boxes import AurallyCreative, AurallyToken


@P.Subroutine(P.TealType.none)
def ensure_zero_payment(txn: P.abi.PaymentTransaction):
    return P.Assert(txn.get().amount() == P.Int(0), comment="Payment amount must be 0")


@P.Subroutine(P.TealType.none)
def ensure_auras_exist():
    from smart_contracts.nfts.contract import app

    return P.Seq(
        P.Assert(
            app.state.registered_asa[P.Bytes("aura")].exists(),
            comment="aura tokens have not been created yet",
        ),
    )


@P.Subroutine(P.TealType.none)
def ensure_valid_nft_type(nft_type: P.abi.String):
    return P.Assert(
        P.Or(nft_type.get() == P.Bytes("art"), nft_type.get() == P.Bytes("sound")),
        comment="asset_type can only be `art` or `sound`",
    )


@P.Subroutine(P.TealType.none)
def ensure_fixed_asset_sale_exists(sale_key: P.abi.String):
    from smart_contracts.nfts.contract import app

    return P.Assert(
        app.state.fixed_asset_sales[sale_key.get()].exists(),
        comment="Fixed asset sale with the specified sale_key does not exist",
    )


@P.Subroutine(P.TealType.none)
def ensure_asset_is_aura(asset: P.abi.Asset):
    from smart_contracts.nfts.contract import app

    return P.Seq(
        (aura_token := AurallyToken()).decode(
            app.state.registered_asa[P.Bytes("aura")].get()
        ),
        (aura_id := P.abi.Uint64()).set(aura_token.asset_id),
        P.Assert(
            asset.asset_id() == aura_id.get(), comment="The asset is not an aura token"
        ),
    )


@P.Subroutine(P.TealType.none)
def ensure_txn_is_aura_optin(txn: P.abi.AssetTransferTransaction):
    from smart_contracts.nfts.contract import app

    return P.Seq(
        (aura_token := AurallyToken()).decode(
            app.state.registered_asa[P.Bytes("aura")].get()
        ),
        (aura_id := P.abi.Uint64()).set(aura_token.asset_id),
        P.Assert(
            txn.get().xfer_asset() == aura_id.get(),
            comment="The txn is not an aura optin Transaction",
        ),
    )


@P.Subroutine(P.TealType.none)
def ensure_art_auction_exists(auction_key: P.abi.String):
    from smart_contracts.nfts.contract import app

    return P.Assert(
        app.state.art_auctions[auction_key.get()].exists(),
        comment="art auction with the specified key does not exist",
    )


@P.Subroutine(P.TealType.none)
def ensure_sound_nft_exists(asset_key: P.abi.String):
    from smart_contracts.nfts.contract import app

    return P.Assert(
        app.state.sound_nfts[asset_key.get()].exists(),
        comment="SoundNFT with the specified asset_key does not exist",
    )


@P.Subroutine(P.TealType.none)
def ensure_art_nft_exists(asset_key: P.abi.String):
    from smart_contracts.nfts.contract import app

    return P.Assert(
        app.state.art_nfts[asset_key.get()].exists(),
        comment="ArtNFT with the specified asset_key does not exist",
    )


# @P.Subroutine(P.TealType.none)
# def ensure_has_auras(txn: P.abi.Transaction):
#     from smart_contracts.nfts.contract import app
#
#     return P.Seq(
#         ensure_auras_exist(),
#         (aura_token := AurallyToken()).decode(
#             app.state.registered_asa[P.Bytes("aura")].get()
#         ),
#         (aura_id := P.abi.Uint64()).set(aura_token.asset_id),
#         (asset_bal := P.AssetHolding.balance(txn.get().sender(), aura_id.get())),
#         P.Assert(
#             asset_bal.value() > P.Int(0),
#             comment="User must have at least one aura token",
#         ),
#     )
#
#
# @P.Subroutine(P.TealType.none)
# def ensure_auras_frozen_status(txn: P.abi.Transaction, status: P.abi.Bool):
#     from smart_contracts.nfts.contract import app
#
#     return P.Seq(
#         ensure_auras_exist(),
#         (aura_token := AurallyToken()).decode(
#             app.state.registered_asa[P.Bytes("aura")].get()
#         ),
#         (aura_id := P.abi.Uint64()).set(aura_token.asset_id),
#         (asset_frozen := P.AssetHolding.frozen(txn.get().sender(), aura_id.get())),
#         P.If(
#             status.get(),
#             P.Assert(asset_frozen.value(), comment="auras should be frozen"),
#             P.Assert(P.Not(asset_frozen.value()), comment="auras should not be frozen"),
#         ),
#     )
#
#
# @P.Subroutine(P.TealType.none)
# def ensure_nft_owner_exists_from_txn(txn: P.abi.Transaction):
#     from smart_contracts.nfts.contract import app
#
#     return P.Assert(
#         app.state.aurally_nft_owners[txn.get().sender()].exists(),
#         comment="User is not an NFT owner",
#     )


@P.Subroutine(P.TealType.none)
def ensure_registered_creative(txn: P.abi.Transaction, creative_type: P.abi.String):
    from smart_contracts.nfts.contract import app

    return P.Seq(
        P.Assert(
            app.state.aurally_nft_owners[txn.get().sender()].exists(),
            comment="Account is not a registered creative",
        ),
        (creative := AurallyCreative()).decode(
            app.state.aurally_nft_owners[txn.get().sender()].get()
        ),
        (is_music_creative := P.abi.Bool()).set(creative.is_music_creative),
        (is_art_creative := P.abi.Bool()).set(creative.is_art_creative),
        (minted := P.abi.Uint64()).set(creative.minted),
        (fullname := P.abi.String()).set(creative.fullname),
        (username := P.abi.String()).set(creative.username),
        (d_nft_id := P.abi.Uint64()).set(creative.d_nft_id),
        P.If(creative_type.get() == P.Bytes("music"), is_music_creative.set(True)),
        P.If(creative_type.get() == P.Bytes("art"), is_music_creative.set(True)),
        creative.set(
            is_music_creative,
            is_art_creative,
            minted,
            fullname,
            username,
            d_nft_id,
        ),
        app.state.aurally_nft_owners[txn.get().sender()].set(creative),
    )


@P.Subroutine(P.TealType.none)
def ensure_asset_reciver_is_application(txn: P.abi.AssetTransferTransaction):
    return P.Assert(
        txn.get().asset_receiver() == P.Global.current_application_address(),
        comment="The asset_receiver must be the current_application_address",
    )
