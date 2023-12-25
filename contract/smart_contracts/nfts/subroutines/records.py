import pyteal as P

from smart_contracts.nfts.boxes import ArtAuctionItem, AurallyCreative


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
        (creative := AurallyCreative()).set(
            is_music_creative, is_art_creative, minted, fullname, username, dnft_id
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
        (minted.set(minted.get() + P.Int(1))),
        creative.set(
            is_music_creative, is_art_creative, minted, fullname, username, d_nft_id
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
def perform_auction_bid(
    txn: P.abi.PaymentTransaction, auction_key: P.abi.String, bid_ammount: P.abi.Uint64
):
    from smart_contracts.nfts.contract import app

    return P.Seq(
        (auction_item := ArtAuctionItem()).decode(
            app.state.art_auctions[auction_key.get()].get()
        ),
        (highest_bid := P.abi.Uint64()).set(auction_item.highest_bid),
        (min_bid := P.abi.Uint64()).set(auction_item.min_bid),
        (starts_at := P.abi.Uint64()).set(auction_item.starts_at),
        (ends_at := P.abi.Uint64()).set(auction_item.ends_at),
        P.Assert(
            bid_ammount.get() > highest_bid.get(),
            comment="The new bid must be larger than the current highest bid",
        ),
        P.Assert(
            bid_ammount.get() > min_bid.get(),
            comment="The new bid must be greater that the minimum bid price",
        ),
        (auctioneer := P.abi.Address()).set(auction_item.auctioneer),
        (item_id := P.abi.String()).set(auction_item.item_id),
        (item_name := P.abi.String()).set(auction_item.item_name),
        (highest_bidder := P.abi.Address()).set(txn.get().sender()),
        auction_item.set(
            auctioneer,
            item_id,
            item_name,
            min_bid,
            starts_at,
            ends_at,
            bid_ammount,
            highest_bidder,
        ),
        app.state.art_auctions[auction_key.get()].set(auction_item),
    )
