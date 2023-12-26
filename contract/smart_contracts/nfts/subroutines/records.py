import pyteal as P

from smart_contracts.nfts.boxes import ArtAuctionItem, ArtNFT, AurallyCreative


@P.Subroutine(P.TealType.none)
def update_creative_is_admin(address: P.abi.Address, is_admin: P.abi.Bool):
    from smart_contracts.nfts.contract import app

    return P.Seq(
        P.Assert(
            app.state.aurally_nft_owners[address.get()].exists(),
            comment="The address is not an aurally creative",
        ),
        (creative := AurallyCreative()).decode(
            app.state.aurally_nft_owners[address.get()].get()
        ),
        (is_music_creative := P.abi.Bool()).set(creative.is_music_creative),
        (is_art_creative := P.abi.Bool()).set(creative.is_art_creative),
        (minted := P.abi.Uint64()).set(creative.minted),
        (fullname := P.abi.String()).set(creative.fullname),
        (username := P.abi.String()).set(creative.username),
        (d_nft_id := P.abi.Uint64()).set(creative.d_nft_id),
        creative.set(
            is_music_creative,
            is_art_creative,
            minted,
            fullname,
            username,
            d_nft_id,
            is_admin,
        ),
        app.state.aurally_nft_owners[address.get()].set(creative),
    )


@P.Subroutine(P.TealType.none)
def create_nft_owner(
    txn: P.abi.Transaction,
    fullname: P.abi.String,
    username: P.abi.String,
):
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
        (dnft_id := P.abi.Uint64()).set(P.InnerTxn.created_asset_id()),
        (is_music_creative := P.abi.Bool()).set(False),
        (is_art_creative := P.abi.Bool()).set(False),
        (minted := P.abi.Uint64()).set(0),
        (is_admin := P.abi.Bool()).set(False),
        (creative := AurallyCreative()).set(
            is_music_creative,
            is_art_creative,
            minted,
            fullname,
            username,
            dnft_id,
            is_admin,
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
        (is_music_creative := P.abi.Bool()).set(creative.is_music_creative),
        (is_art_creative := P.abi.Bool()).set(creative.is_art_creative),
        (fullname := P.abi.String()).set(creative.fullname),
        (username := P.abi.String()).set(creative.username),
        (d_nft_id := P.abi.Uint64()).set(creative.d_nft_id),
        (is_admin := P.abi.Bool()).set(creative.is_admin),
        (minted.set(minted.get() + P.Int(1))),
        creative.set(
            is_music_creative,
            is_art_creative,
            minted,
            fullname,
            username,
            d_nft_id,
            is_admin,
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
        (asset_key := P.abi.String()).set(art_nft.asset_key),
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
