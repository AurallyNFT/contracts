import beaker as B
import pyteal as P

from smart_contracts.nfts.boxes import (
    ArtAuctionItem,
    ArtNFT,
    AurallyCreative,
    AurallyToken,
    SoundNFT,
)
from .state import AppState

app = B.Application("Aurally_NFT", state=AppState())


@app.update(authorize=B.Authorize.only_creator(), bare=True)
def update() -> P.Expr:
    return P.Approve()


@app.delete(authorize=B.Authorize.only_creator(), bare=True)
def delete() -> P.Expr:
    return P.Approve()


@app.external
def create_aura_tokens(*, output: AurallyToken):
    from .subroutines.tokens import bootstrap_token

    return P.Seq(
        (token_key := P.abi.String()).set("aura"),
        (unit_name := P.abi.String()).set("AUR"),
        (url := P.abi.String()).set(
            "https://res.cloudinary.com/dev-media/image/upload/v1703091710/Aurally_A_p1v2ob.png"
        ),
        P.If(
            P.Not(app.state.registered_asa[token_key.get()].exists()),
            P.Seq(
                (total := P.abi.Uint64()).set(1000000000000),
                bootstrap_token(token_key, total, unit_name, url),
                P.Assert(app.state.registered_asa[token_key.get()].exists()),
            ),
        ),
        output.decode(app.state.registered_asa[token_key.get()].get()),
    )


@app.external
def register_creator(
    txn: P.abi.Transaction,
    fullname: P.abi.String,
    username: P.abi.String,
    *,
    output: AurallyCreative,
):
    from .subroutines.records import create_nft_owner

    return P.Seq(
        P.If(
            P.Not(app.state.aurally_nft_owners[txn.get().sender()].exists()),
            create_nft_owner(txn, fullname, username),
        ),
        output.decode(app.state.aurally_nft_owners[txn.get().sender()].get()),
    )


@app.external
def create_sound_nft(
    txn: P.abi.PaymentTransaction,
    nft_name: P.abi.String,
    asset_key: P.abi.String,
    title: P.abi.String,
    label: P.abi.String,
    artist: P.abi.String,
    release_date: P.abi.Uint64,
    genre: P.abi.String,
    price: P.abi.Uint64,
    cover_image_ipfs: P.abi.String,
    audio_sample_ipfs: P.abi.String,
    full_track_ipfs: P.abi.String,
    supply: P.abi.Uint64,
    aura: P.abi.Asset,
    creator: P.abi.Account,
    *,
    output: SoundNFT,
):
    from .subroutines.records import increment_creator_nft_count
    from .subroutines.transactions import send_aura_token
    from .subroutines.validators import (
        ensure_registered_creative,
        ensure_zero_payment,
        ensure_asset_is_aura,
    )

    opup = P.OpUp(P.OpUpMode.OnCall)
    return P.Seq(
        ensure_zero_payment(txn),
        ensure_asset_is_aura(aura),
        opup.maximize_budget(P.Int(1000)),
        (creative_type := P.abi.String()).set("music"),
        ensure_registered_creative(txn, creative_type),
        P.Assert(
            creator.address() == txn.get().sender(),
            comment="The creator must be the same as the transaction sender",
        ),
        P.Assert(
            P.Not(app.state.sound_nfts[asset_key.get()].exists()),
            comment="An asset with this key already exists",
        ),
        (creators_address := P.abi.Address()).set(txn.get().sender()),
        P.InnerTxnBuilder.Execute(
            {
                P.TxnField.type_enum: P.TxnType.AssetConfig,
                P.TxnField.config_asset_name: nft_name.get(),
                P.TxnField.config_asset_total: supply.get(),
                P.TxnField.config_asset_url: cover_image_ipfs.get(),
                P.TxnField.config_asset_manager: creators_address.get(),
            }
        ),
        (asset_id := P.abi.Uint64()).set(P.InnerTxn.created_asset_id()),
        (for_sale := P.abi.Bool()).set(True),
        (claimed := P.abi.Bool()).set(False),
        (sound_nft := SoundNFT()).set(
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
            creators_address,
            for_sale,
            claimed,
        ),
        app.state.sound_nfts[asset_key.get()].set(sound_nft),
        increment_creator_nft_count(creators_address),
        (aura_amt := P.abi.Uint64()).set(1),
        send_aura_token(creators_address, aura_amt),
        output.decode(app.state.sound_nfts[asset_key.get()].get()),
    )


@app.external
def claim_created_sound(
    txn: P.abi.AssetTransferTransaction,
    asset_key: P.abi.String,
    reciever: P.abi.Account,
    asset: P.abi.Asset,
    *,
    output: SoundNFT,
):
    from .subroutines.validators import ensure_sound_nft_exists
    from .subroutines.transactions import transfer_asset_from_contract

    return P.Seq(
        ensure_sound_nft_exists(asset_key),
        (sound_nft := SoundNFT()).decode(app.state.art_nfts[asset_key.get()].get()),
        (asset_id := P.abi.Uint64()).set(sound_nft.asset_id),
        (asset_key := P.abi.String()).set(sound_nft.asset_key),
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
        (creator := P.abi.Address()).set(sound_nft.creator),
        (for_sale := P.abi.Bool()).set(sound_nft.for_sale),
        (claimed := P.abi.Bool()).set(sound_nft.claimed),
        P.Assert(P.Not(claimed.get()), comment="This art nft has already been claimed"),
        P.Assert(
            creator.get() == txn.get().sender(),
            comment="This address is not the nft creator",
        ),
        P.Assert(
            reciever.address() == creator.get(),
            comment="The reciever must be the creator of the nft",
        ),
        P.Assert(
            asset.asset_id() == asset_id.get(),
            comment="The asset must have the same asset_id as the nft",
        ),
        transfer_asset_from_contract(asset_id, supply, creator),
        claimed.set(True),
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
            creator,
            for_sale,
            claimed,
        ),
        app.state.sound_nfts[asset_key.get()].set(sound_nft),
        output.decode(app.state.sound_nfts[asset_key.get()].get()),
    )


@app.external
def create_art_nft(
    txn: P.abi.PaymentTransaction,
    asset_key: P.abi.String,
    nft_name: P.abi.String,
    title: P.abi.String,
    name: P.abi.String,
    description: P.abi.String,
    ipfs_location: P.abi.String,
    price: P.abi.Uint64,
    aura: P.abi.Asset,
    creator: P.abi.Account,
    *,
    output: ArtNFT,
):
    from .subroutines.validators import (
        ensure_zero_payment,
        ensure_registered_creative,
        ensure_asset_is_aura,
    )
    from .subroutines.transactions import send_aura_token
    from .subroutines.records import increment_creator_nft_count

    return P.Seq(
        ensure_zero_payment(txn),
        ensure_asset_is_aura(aura),
        P.Assert(
            creator.address() == txn.get().sender(),
            comment="The creator must be the same as the transaction sender",
        ),
        P.Assert(
            P.Not(app.state.art_nfts[asset_key.get()].exists()),
            comment="An art NFT with this key already exists",
        ),
        (creative_type := P.abi.String()).set("art"),
        ensure_registered_creative(txn, creative_type),
        (creators_address := P.abi.Address()).set(txn.get().sender()),
        P.InnerTxnBuilder.Execute(
            {
                P.TxnField.type_enum: P.TxnType.AssetConfig,
                P.TxnField.config_asset_name: nft_name.get(),
                P.TxnField.config_asset_total: P.Int(1),
                P.TxnField.config_asset_url: ipfs_location.get(),
                P.TxnField.config_asset_manager: creators_address.get(),
            }
        ),
        (asset_id := P.abi.Uint64()).set(P.InnerTxn.created_asset_id()),
        (sold_price := P.abi.Uint64()).set(0),
        (for_sale := P.abi.Bool()).set(True),
        (owners_address := P.abi.Address()).set(P.Global.current_application_address()),
        (claimed := P.abi.Bool()).set(False),
        (art_nft := ArtNFT()).set(
            asset_id,
            asset_key,
            title,
            name,
            description,
            ipfs_location,
            price,
            sold_price,
            creators_address,
            owners_address,
            for_sale,
            claimed,
        ),
        app.state.art_nfts[asset_key.get()].set(art_nft),
        increment_creator_nft_count(creators_address),
        (aura_amt := P.abi.Uint64()).set(1),
        send_aura_token(creators_address, aura_amt),
        output.decode(app.state.art_nfts[asset_key.get()].get()),
    )


@app.external
def claim_created_art(
    txn: P.abi.AssetTransferTransaction,
    asset_key: P.abi.String,
    reciever: P.abi.Account,
    asset: P.abi.Asset,
    *,
    output: ArtNFT,
):
    from .subroutines.transactions import transfer_asset_from_contract
    from .subroutines.validators import ensure_art_nft_exists

    return P.Seq(
        ensure_art_nft_exists(asset_key),
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
        (owner := P.abi.Address()).set(art_nft.owner),
        (for_sale := P.abi.Bool()).set(art_nft.for_sale),
        (claimed := P.abi.Bool()).set(art_nft.claimed),
        P.Assert(P.Not(claimed.get()), comment="This art nft has already been claimed"),
        P.Assert(
            reciever.address() == creator.get(),
            comment="The reciever must be the creator of the nft",
        ),
        P.Assert(
            creator.get() == txn.get().sender(),
            comment="This address is not the nft creator",
        ),
        P.Assert(
            asset.asset_id() == asset_id.get(),
            comment="The asset must have the same asset_id as the nft",
        ),
        (amt := P.abi.Uint64()).set(1),
        transfer_asset_from_contract(asset_id, amt, creator),
        owner.set(txn.get().sender()),
        claimed.set(True),
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
        output.decode(app.state.art_nfts[asset_key.get()].get()),
    )


@app.external
def create_art_auction(
    txn: P.abi.PaymentTransaction,
    auction_key: P.abi.String,
    asset_key: P.abi.String,
    min_bid: P.abi.Uint64,
    starts_at: P.abi.Uint64,
    ends_at: P.abi.Uint64,
    description: P.abi.String,
    *,
    output: ArtAuctionItem,
):
    from .subroutines.validators import ensure_zero_payment
    from .subroutines.records import new_art_auction

    return P.Seq(
        P.Assert(
            P.Not(app.state.art_auctions[auction_key.get()].exists()),
            comment="An auction with this key already exists",
        ),
        ensure_zero_payment(txn),
        P.Assert(
            starts_at.get() < ends_at.get(),
            comment="End date must be greater that start date",
        ),
        P.Assert(
            app.state.art_nfts[asset_key.get()].exists(),
            comment="Art NFT with this key was not found",
        ),
        (art_nft := ArtNFT()).decode(app.state.art_nfts[asset_key.get()].get()),
        (art_nft_owner := P.abi.Address()).set(art_nft.owner),
        (nft_name := P.abi.String()).set(art_nft.name),
        P.Assert(
            art_nft_owner.get() == txn.get().sender(),
            comment="Only the owner of this NFT can auction it",
        ),
        new_art_auction(
            txn,
            auction_key,
            asset_key,
            nft_name,
            description,
            min_bid,
            starts_at,
            ends_at,
        ),
        output.decode(app.state.art_auctions[auction_key.get()].get()),
    )


@app.external
def bid_on_art_auction(
    txn: P.abi.PaymentTransaction,
    auction_key: P.abi.String,
    bid_ammount: P.abi.Uint64,
    current_highest_bidder: P.abi.Account,
    *,
    output: ArtAuctionItem,
):
    from .subroutines.transactions import refund_last_bidder

    return P.Seq(
        P.Assert(
            app.state.art_auctions[auction_key.get()].exists(),
            comment="art auction with the specified key does not exist",
        ),
        P.Assert(txn.get().receiver() == P.Global.current_application_address()),
        (auction := ArtAuctionItem()).decode(
            app.state.art_auctions[auction_key.get()].get()
        ),
        (auction_name := P.abi.String()).set(auction.item_name),
        (highest_bid := P.abi.Uint64()).set(auction.highest_bid),
        (highest_bidder := P.abi.Address()).set(auction.highest_bidder),
        (min_bid := P.abi.Uint64()).set(auction.min_bid),
        P.Assert(current_highest_bidder.address() == highest_bidder.get()),
        P.If(
            highest_bid.get() == P.Int(0),
            P.Assert(
                txn.get().amount() > min_bid.get(),
                comment="Bid amount has to be greated than the minimum bid",
            ),
            P.Assert(
                txn.get().amount() > highest_bid.get(),
                comment="Bid amount must be greater that the highest_bid",
            ),
        ),
        P.If(
            P.Not(highest_bidder.get() == P.Global.current_application_address()),
            P.Seq(
                (note := P.abi.String()).set(
                    P.Concat(P.Bytes("Refund for your bid on: "), auction_name.get())
                ),
                refund_last_bidder(current_highest_bidder, highest_bid, note)
            ),
        ),
        perform_auction_bid(txn, auction_key, bid_ammount),
        output.decode(app.state.art_auctions[auction_key.get()].get()),
    )
