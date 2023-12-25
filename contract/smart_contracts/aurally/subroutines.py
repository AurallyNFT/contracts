import pyteal as P

from .contract import app


@P.Subroutine(P.TealType.none)
def save_art_nft(
    asset_id: P.abi.Uint64,
    asset_key: P.abi.String,
    title: P.abi.String,
    name: P.abi.String,
    supply: P.abi.Uint64,
    description: P.abi.String,
    ipfs_location: P.abi.String,
    price: P.abi.Uint64,
    sold_price: P.abi.Uint64,
    owner: P.abi.Address,
    for_sale: P.abi.Bool,
):
    return P.Seq(
        (art_nft := ArtNFT()).set(
            asset_id,
            asset_key,
            title,
            name,
            supply,
            description,
            ipfs_location,
            price,
            sold_price,
            owner,
            for_sale,
        ),
        app.state.art_nfts[asset_key.get()].set(art_nft),
    )


@P.Subroutine(P.TealType.none)
def transfer_art_auction_item_to_highest_bidder(auction_key: P.abi.String):
    return P.Seq(
        (auction_item := ArtAuctionItem()).decode(
            app.state.art_auctions[auction_key.get()].get()
        ),
        (highest_bidder := P.abi.Address()).set(auction_item.highest_bidder),
        (nft_key := P.abi.String()).set(auction_item.item_id),
        update_art_nft_owner(nft_key, highest_bidder),
    )


@P.Subroutine(P.TealType.none)
def update_art_nft_owner(asset_key: P.abi.String, new_owner: P.abi.Address):
    return P.Seq(
        (art_nft := ArtNFT()).decode(app.state.art_nfts[asset_key.get()].get()),
        (asset_id := P.abi.Uint64()).set(art_nft.asset_id),
        (title := P.abi.String()).set(art_nft.title),
        (name := P.abi.String()).set(art_nft.name),
        (description := P.abi.String()).set(art_nft.description),
        (ipfs_location := P.abi.String()).set(art_nft.ipfs_location),
        (price := P.abi.Uint64()).set(art_nft.price),
        (sold_price := P.abi.Uint64()).set(art_nft.sold_price),
        (creator := P.abi.Address()).set(art_nft.creator),
        (for_sale := P.abi.Bool()).set(art_nft.for_sale),
        (claimed := P.abi.Bool()).set(art_nft.claimed),
        art_nft.set(
            asset_id,
            asset_key,
            title,
            name,
            description,
            ipfs_location,
            price,
            sold_price,
            creator,
            new_owner,
            for_sale,
            claimed,
        ),
        app.state.art_nfts[asset_key.get()].set(art_nft),
    )


@P.Subroutine(P.TealType.none)
def update_sound_nft_owner(asset_key: P.abi.String, new_owner: P.abi.Address):
    return P.Seq(
        (sound_nft := SoundNFT()).decode(app.state.sound_nfts[asset_key.get()].get()),
        (asset_id := P.abi.Uint64()).set(sound_nft.asset_id),
        (supply := P.abi.Uint64()).set(sound_nft.supply),
        (title := P.abi.String()).set(sound_nft.title),
        (label := P.abi.String()).set(sound_nft.label),
        (artist := P.abi.String()).set(sound_nft.artist),
        (release_date := P.abi.Uint64()).set(sound_nft.release_date),
        (genre := P.abi.String()).set(sound_nft.genre),
        (price := P.abi.Uint64()).set(sound_nft.price),
        (cover_image_ipfs := P.abi.String()).set(sound_nft.cover_image_ipfs),
        (audio_sample_ipfs := P.abi.String()).set(sound_nft.audio_sample_ipfs),
        (full_track_ipfs := P.abi.String()).set(sound_nft.full_track_ipfs),
        (for_sale := P.abi.Bool()).set(sound_nft.for_sale),
        (claimed := P.abi.Bool()).set(sound_nft.claimed),
        sound_nft.set(
            asset_id,
            asset_key,
            supply,
            title,
            label,
            artist,
            release_date,
            genre,
            price,
            cover_image_ipfs,
            audio_sample_ipfs,
            full_track_ipfs,
            new_owner,
            for_sale,
            claimed,
        ),
    )


@P.Subroutine(P.TealType.none)
def perform_sound_nft_sale(txn: P.abi.PaymentTransaction, asset_key: P.abi.String):
    from .helpers.transactions import pay_95_percent, send_aura_token

    return P.Seq(
        (asset_item := SoundNFT()).decode(app.state.sound_nfts[asset_key.get()].get()),
        (price := P.abi.Uint64()).set(asset_item.price),
        (nft_owner := P.abi.Address()).set(asset_item.creator),
        (buyer := P.abi.Address()).set(txn.get().sender()),
        (asset_id := P.abi.Uint64()).set(asset_item.asset_id),
        (amount := P.abi.Uint64()).set(1),
        (for_sale := P.abi.Bool()).set(asset_item.for_sale),
        P.Assert(for_sale.get(), comment="This asset is not currently for sale"),
        pay_95_percent(txn, price, nft_owner),
        perform_asset_transfer(asset_id, buyer, amount),
        update_sound_nft_owner(asset_key, buyer),
        (aura_amt := P.abi.Uint64()).set(1),
        send_aura_token(buyer, aura_amt),
        P.Approve(),
    )


@P.Subroutine(P.TealType.none)
def perform_art_nft_sale(txn: P.abi.PaymentTransaction, asset_key: P.abi.String):
    from .helpers.transactions import pay_95_percent, send_aura_token

    return P.Seq(
        (asset_item := ArtNFT()).decode(app.state.art_nfts[asset_key.get()].get()),
        (price := P.abi.Uint64()).set(asset_item.price),
        (nft_owner := P.abi.Address()).set(asset_item.creator),
        (buyer := P.abi.Address()).set(txn.get().sender()),
        (asset_id := P.abi.Uint64()).set(asset_item.asset_id),
        (amount := P.abi.Uint64()).set(1),
        (for_sale := P.abi.Bool()).set(asset_item.for_sale),
        P.Assert(for_sale.get(), comment="This asset is not currently for sale"),
        pay_95_percent(txn, price, nft_owner),
        perform_asset_transfer(asset_id, buyer, amount),
        update_art_nft_owner(asset_key, buyer),
        (aura_amt := P.abi.Uint64()).set(1),
        send_aura_token(buyer, aura_amt),
        P.Approve(),
    )


@P.Subroutine(P.TealType.none)
def buy_event_ticket(txn: P.abi.PaymentTransaction, event_key: P.abi.String):
    from .helpers.transactions import pay_95_percent, send_aura_token

    return P.Seq(
        (asset_item := ArtNFT()).decode(app.state.art_nfts[event_key.get()].get()),
        (price := P.abi.Uint64()).set(asset_item.price),
        (nft_owner := P.abi.Address()).set(asset_item.creator),
        (buyer := P.abi.Address()).set(txn.get().sender()),
        pay_95_percent(txn, price, nft_owner),
        update_art_nft_owner(event_key, buyer),
        (aura_amt := P.abi.Uint64()).set(1),
        send_aura_token(buyer, aura_amt),
        P.Approve(),
    )


@P.Subroutine(P.TealType.none)
def validate_sound_nft_owner(txn: P.abi.Transaction, asset_key: P.abi.String):
    from .helpers.validators import ensure_sound_nft_exists

    return P.Seq(
        ensure_sound_nft_exists(asset_key),
        (sound_nft := SoundNFT()).decode(app.state.sound_nfts[asset_key.get()].get()),
        (owner := P.abi.Address()).set(sound_nft.creator),
        P.Assert(
            owner.get() == txn.get().sender(),
            comment="The transaction sender is not the owner of the nft",
        ),
    )


@P.Subroutine(P.TealType.none)
def validate_art_nft_owner(txn: P.abi.Transaction, asset_key: P.abi.String):
    from .helpers.validators import ensure_art_nft_exists

    return P.Seq(
        ensure_art_nft_exists(asset_key),
        (art_nft := ArtNFT()).decode(app.state.art_nfts[asset_key.get()].get()),
        (owner := P.abi.Address()).set(art_nft.creator),
        P.Assert(
            owner.get() == txn.get().sender(),
            comment="The transaction sender is not the owner of the art nft",
        ),
    )


@P.Subroutine(P.TealType.none)
def validate_and_update_sound_nft_owner(
    txn: P.abi.Transaction, asset_key: P.abi.String, to: P.abi.Address
):
    return P.Seq(
        validate_sound_nft_owner(txn),
        update_sound_nft_owner(asset_key, to),
        P.Approve(),
    )


@P.Subroutine(P.TealType.none)
def update_sound_nft_sale(asset_key: P.abi.String, for_sale: P.abi.Bool):
    from .helpers.validators import ensure_sound_nft_exists

    return P.Seq(
        ensure_sound_nft_exists(asset_key),
        (sound_nft := SoundNFT()).decode(app.state.sound_nfts[asset_key.get()].get()),
        (asset_id := P.abi.Uint64()).set(sound_nft.asset_id),
        (supply := P.abi.Uint64()).set(sound_nft.supply),
        (title := P.abi.String()).set(sound_nft.title),
        (label := P.abi.String()).set(sound_nft.label),
        (artist := P.abi.String()).set(sound_nft.artist),
        (release_date := P.abi.Uint64()).set(sound_nft.release_date),
        (genre := P.abi.String()).set(sound_nft.genre),
        (price := P.abi.Uint64()).set(sound_nft.price),
        (cover_image_ipfs := P.abi.String()).set(sound_nft.cover_image_ipfs),
        (audio_sample_ipfs := P.abi.String()).set(sound_nft.audio_sample_ipfs),
        (full_track_ipfs := P.abi.String()).set(sound_nft.full_track_ipfs),
        (owner := P.abi.Address()).set(sound_nft.creator),
        (claimed := P.abi.Bool()).set(sound_nft.claimed),
        sound_nft.set(
            asset_id,
            asset_key,
            supply,
            title,
            label,
            artist,
            release_date,
            genre,
            price,
            cover_image_ipfs,
            audio_sample_ipfs,
            full_track_ipfs,
            owner,
            for_sale,
            claimed,
        ),
        app.state.sound_nfts[asset_key.get()].set(sound_nft),
    )


@P.Subroutine(P.TealType.none)
def update_art_nft_sale(asset_key: P.abi.String, for_sale: P.abi.Bool):
    from .helpers.validators import ensure_art_nft_exists

    return P.Seq(
        ensure_art_nft_exists(asset_key),
        (art_nft := ArtNFT()).decode(app.state.art_nfts[asset_key.get()].get()),
        (asset_id := P.abi.Uint64()).set(art_nft.asset_id),
        (title := P.abi.String()).set(art_nft.title),
        (name := P.abi.String()).set(art_nft.name),
        (description := P.abi.String()).set(art_nft.description),
        (ipfs_location := P.abi.String()).set(art_nft.ipfs_location),
        (price := P.abi.Uint64()).set(art_nft.price),
        (sold_price := P.abi.Uint64()).set(art_nft.sold_price),
        (creator_address := P.abi.Address()).set(art_nft.creator),
        (claimed := P.abi.Bool()).set(art_nft.claimed),
        opt_app_into_asset(asset_id),
        art_nft.set(
            asset_id,
            asset_key,
            title,
            name,
            description,
            ipfs_location,
            price,
            sold_price,
            creator_address,
            creator_address,
            for_sale,
            claimed,
        ),
        app.state.art_nfts[asset_key.get()].set(art_nft),
    )


@P.Subroutine(P.TealType.none)
def opt_app_into_asset(asset_id: P.abi.Uint64):
    return P.Seq(
        # Perform Asset Transfer
        P.InnerTxnBuilder.Execute(
            {
                P.TxnField.type_enum: P.TxnType.AssetTransfer,
                P.TxnField.xfer_asset: asset_id.get(),
                P.TxnField.asset_receiver: P.Global.current_application_address(),
                P.TxnField.sender: P.Global.current_application_address(),
                P.TxnField.asset_amount: P.Int(0),
            }
        )
    )


@P.Subroutine(P.TealType.none)
def perform_asset_transfer(
    asset_id: P.abi.Uint64, to: P.abi.Address, amt: P.abi.Uint64
):
    return P.Seq(
        P.InnerTxnBuilder.Execute(
            {
                P.TxnField.type_enum: P.TxnType.AssetTransfer,
                P.TxnField.xfer_asset: asset_id.get(),
                P.TxnField.asset_receiver: to.get(),
                P.TxnField.asset_amount: amt.get(),
            }
        )
    )
