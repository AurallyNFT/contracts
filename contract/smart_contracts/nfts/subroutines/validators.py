import pyteal as P

from smart_contracts.nfts.boxes import ArtNFT, AurallyCreative, AurallyToken, SoundNFT


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


#
#
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
#
#
# @P.Subroutine(P.TealType.none)
# def ensure_sender_is_app_creator(txn: P.abi.Transaction):
#     return P.Assert(
#         txn.get().sender() == P.Global.creator_address(),
#         comment="Not app creator: You are not authorised to perform this action",
#     )
#
#
# @P.Subroutine(P.TealType.none)
# def ensure_is_admin_or_app_creator(addr: P.abi.Address):
#     from smart_contracts.nfts.contract import app
#
#     return P.Assert(
#         P.Or(
#             addr.get() == P.Global.creator_address(),
#             app.state.aurally_admins[addr.get()].exists(),
#         ),
#         comment="Not admin: You are not authorised to perform this action",
#     )


@P.Subroutine(P.TealType.none)
def ensure_sound_nft_exists(key: P.abi.String):
    from smart_contracts.nfts.contract import app

    return P.Assert(
        app.state.sound_nfts[key.get()].exists(),
        comment="SoundNFT with specified key does not exist",
    )


@P.Subroutine(P.TealType.none)
def ensure_art_nft_exists(key: P.abi.String):
    from smart_contracts.nfts.contract import app

    return P.Assert(
        app.state.art_nfts[key.get()].exists(),
        comment="ArtNFT with specified key does not exist",
    )


# @P.Subroutine(P.TealType.none)
# def ensure_sender_is_sound_nft_owner(txn: P.abi.Transaction, key: P.abi.String):
#     from smart_contracts.nfts.contract import app
#
#     return P.Seq(
#         ensure_sound_nft_exists(key),
#         (sound_nft := SoundNFT()).decode(app.state.sound_nfts[key.get()].get()),
#         (owner := P.abi.Address()).set(sound_nft.creator),
#         P.Assert(
#             txn.get().sender() == owner.get(),
#             comment="Not Sound NFT owner: You are not authorised to perform this action",
#         ),
#     )
#
#
# @P.Subroutine(P.TealType.none)
# def ensure_sender_is_art_nft_owner(txn: P.abi.Transaction, key: P.abi.String):
#     from smart_contracts.nfts.contract import app
#
#     return P.Seq(
#         ensure_sound_nft_exists(key),
#         (art_nft := ArtNFT()).decode(app.state.art_nfts[key.get()].get()),
#         (owner := P.abi.Address()).set(art_nft.creator),
#         P.Assert(
#             txn.get().sender() == owner.get(),
#             comment="Not Art NFT owner: You are not authorised to perform this action",
#         ),
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
            is_music_creative, is_art_creative, minted, fullname, username, d_nft_id
        ),
        app.state.aurally_nft_owners[txn.get().sender()].set(creative),
    )
