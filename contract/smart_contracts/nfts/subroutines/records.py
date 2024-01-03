import pyteal as P

from smart_contracts.nfts.boxes import (
    ArtAuctionItem,
    ArtNFT,
    AurallyCreative,
    SoundNFT,
)


@P.Subroutine(P.TealType.none)
def increase_app_nft_transaction_count():
    from smart_contracts.nfts.contract import app

    return P.Seq(
        app.state.epoch_nft_transactions.set(
            app.state.epoch_nft_transactions.get() + P.Int(1)
        ),
        app.state.total_nft_transactions.set(
            app.state.total_nft_transactions.get() + P.Int(1)
        ),
    )


@P.Subroutine(P.TealType.none)
def create_nft_owner(txn: P.abi.Transaction):
    from smart_contracts.nfts.contract import app

    return P.Seq(
        P.InnerTxnBuilder.Execute(
            {
                P.TxnField.type_enum: P.TxnType.AssetConfig,
                P.TxnField.config_asset_name: txn.get().sender(),
                P.TxnField.config_asset_manager: P.Global.current_application_address(),
                P.TxnField.config_asset_total: P.Int(1),
            }
        ),
        (address := P.abi.Address()).set(txn.get().sender()),
        (dnft_id := P.abi.Uint64()).set(P.InnerTxn.created_asset_id()),
        (minted := P.abi.Uint64()).set(0),
        (creative := AurallyCreative()).set(
            address,
            minted,
            dnft_id,
        ),
        app.state.aurally_nft_owners[txn.get().sender()].set(creative),
    )


@P.Subroutine(P.TealType.none)
def increment_creator_nft_count(creator: P.abi.Address):
    from smart_contracts.nfts.contract import app

    return P.Seq(
        (creative := AurallyCreative()).decode(
            app.state.aurally_nft_owners[creator.get()].get()
        ),
        (minted := P.abi.Uint64()).set(creative.minted),
        (d_nft_id := P.abi.Uint64()).set(creative.d_nft_id),
        (minted.set(minted.get() + P.Int(1))),
        creative.set(
            creator,
            minted,
            d_nft_id,
        ),
        app.state.aurally_nft_owners[creator.get()].set(creative),
    )


@P.Subroutine(P.TealType.none)
def new_art_auction(
    txn: P.abi.Transaction,
    auction_key: P.abi.String,
    asset_key: P.abi.String,
    name: P.abi.String,
    description: P.abi.String,
    min_bid: P.abi.Uint64,
    starts_at: P.abi.Uint64,
    ends_at: P.abi.Uint64,
):
    from smart_contracts.nfts.contract import app

    return P.Seq(
        P.Assert(
            P.Not(app.state.art_auctions[auction_key.get()].exists()),
            comment="an art auction with this key already exists",
        ),
        (auctionier := P.abi.Address()).set(txn.get().sender()),
        (highest_bid := P.abi.Uint64()).set(0),
        (highest_bidder := P.abi.Address()).set(P.Global.current_application_address()),
        (closed := P.abi.Bool()).set(False),
        (art_auction := ArtAuctionItem()).set(
            auction_key,
            auctionier,
            asset_key,
            name,
            min_bid,
            starts_at,
            ends_at,
            description,
            highest_bid,
            highest_bidder,
            closed,
        ),
        app.state.art_auctions[auction_key.get()].set(art_auction),
    )


@P.Subroutine(P.TealType.none)
def record_auction_bid(txn: P.abi.PaymentTransaction, auction_key: P.abi.String):
    from smart_contracts.nfts.contract import app

    return P.Seq(
        (auction_item := ArtAuctionItem()).decode(
            app.state.art_auctions[auction_key.get()].get()
        ),
        (auctioneer := P.abi.Address()).set(auction_item.auctioneer),
        (item_asset_key := P.abi.String()).set(auction_item.item_asset_key),
        (item_name := P.abi.String()).set(auction_item.item_name),
        (highest_bidder := P.abi.Address()).set(txn.get().sender()),
        (highest_bid := P.abi.Uint64()).set(auction_item.highest_bid),
        (min_bid := P.abi.Uint64()).set(auction_item.min_bid),
        (starts_at := P.abi.Uint64()).set(auction_item.starts_at),
        (ends_at := P.abi.Uint64()).set(auction_item.ends_at),
        (description := P.abi.String()).set(auction_item.description),
        (closed := P.abi.Bool()).set(auction_item.closed),
        P.Assert(
            txn.get().amount() > highest_bid.get(),
            comment="The new bid must be larger than the current highest bid",
        ),
        P.Assert(
            txn.get().amount() > min_bid.get(),
            comment="The new bid must be greater that the minimum bid price",
        ),
        highest_bid.set(txn.get().amount()),
        auction_item.set(
            auction_key,
            auctioneer,
            item_asset_key,
            item_name,
            min_bid,
            starts_at,
            ends_at,
            description,
            highest_bid,
            highest_bidder,
            closed,
        ),
        app.state.art_auctions[auction_key.get()].set(auction_item),
    )


@P.Subroutine(P.TealType.none)
def update_art_nft_owner(asset_key: P.abi.String, new_owner: P.abi.Address):
    from smart_contracts.nfts.contract import app

    return P.Seq(
        (art_nft := ArtNFT()).decode(app.state.art_nfts[asset_key.get()].get()),
        (asset_id := P.abi.Uint64()).set(art_nft.asset_id),
        (title := P.abi.String()).set(art_nft.title),
        (name := P.abi.String()).set(art_nft.name),
        (description := P.abi.String()).set(art_nft.description),
        (ipfs_location := P.abi.String()).set(art_nft.image_url),
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
def update_art_nft_for_sale(asset_key: P.abi.String, for_sale: P.abi.Bool):
    from smart_contracts.nfts.contract import app

    return P.Seq(
        (art_nft := ArtNFT()).decode(app.state.art_nfts[asset_key.get()].get()),
        (asset_id := P.abi.Uint64()).set(art_nft.asset_id),
        (title := P.abi.String()).set(art_nft.title),
        (name := P.abi.String()).set(art_nft.name),
        (description := P.abi.String()).set(art_nft.description),
        (ipfs_location := P.abi.String()).set(art_nft.image_url),
        (price := P.abi.Uint64()).set(art_nft.price),
        (sold_price := P.abi.Uint64()).set(art_nft.sold_price),
        (creator := P.abi.Address()).set(art_nft.creator),
        (owner := P.abi.Address()).set(art_nft.owner),
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
            owner,
            for_sale,
            claimed,
        ),
        app.state.art_nfts[asset_key.get()].set(art_nft),
    )


@P.Subroutine(P.TealType.none)
def update_sound_nft_for_sale(asset_key: P.abi.String, for_sale: P.abi.Bool):
    from smart_contracts.nfts.contract import app

    return P.Seq(
        (sound_nft := SoundNFT()).decode(app.state.sound_nfts[asset_key.get()].get()),
        (asset_id := P.abi.Uint64()).set(sound_nft.asset_id),
        (asset_key := P.abi.String()).set(sound_nft.asset_key),
        (supply := P.abi.Uint64()).set(sound_nft.supply),
        (title := P.abi.String()).set(sound_nft.title),
        (label := P.abi.String()).set(sound_nft.label),
        (artist := P.abi.String()).set(sound_nft.artist),
        (release_date := P.abi.Uint64()).set(sound_nft.release_date),
        (genre := P.abi.String()).set(sound_nft.genre),
        (description := P.abi.String()).set(sound_nft.description),
        (price := P.abi.Uint64()).set(sound_nft.price),
        (cover_image_url := P.abi.String()).set(sound_nft.cover_image_url),
        (audio_sample_url := P.abi.String()).set(sound_nft.audio_sample_id),
        (full_track_url := P.abi.String()).set(sound_nft.full_track_id),
        (creator := P.abi.Address()).set(sound_nft.creator),
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
            description,
            price,
            cover_image_url,
            audio_sample_url,
            full_track_url,
            creator,
            for_sale,
            claimed,
        ),
        app.state.sound_nfts[asset_key.get()].set(sound_nft),
    )
