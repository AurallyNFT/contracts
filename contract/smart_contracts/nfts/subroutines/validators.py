import pyteal as P
from smart_contracts.nfts.boxes import ArtNFT, AurallyToken


@P.Subroutine(P.TealType.none)
def ensure_sender_is_registered_creative(txn: P.abi.Transaction):
    from smart_contracts.nfts.contract import app

    return P.Assert(
        app.state.aurally_nft_owners[txn.get().sender()].exists(),
        comment="Sender is not a registered creative",
    )


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


@P.Subroutine(P.TealType.none)
def ensure_asset_reciver_is_application(txn: P.abi.AssetTransferTransaction):
    return P.Assert(
        txn.get().asset_receiver() == P.Global.current_application_address(),
        comment="The asset_receiver must be the current_application_address",
    )


@P.Subroutine(P.TealType.none)
def ensure_can_market_art(asset_key: P.abi.String):
    from smart_contracts.nfts.contract import app

    return P.Seq(
        ensure_art_nft_exists(asset_key),
        (art_nft := ArtNFT()).decode(app.state.art_nfts[asset_key.get()].get()),
        (on_sale := P.abi.Bool()).set(art_nft.for_sale),
        (on_auction := P.abi.Bool()).set(art_nft.on_auction),
        P.Assert(P.Not(on_sale.get()), comment="ArtNFT is already on sale"),
        P.Assert(P.Not(on_auction.get()), comment="ArtNFT is already on auction"),
    )
